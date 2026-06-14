from __future__ import annotations

import json
from typing import Any

from ciel.swarm.core import (
    SwarmEngine, Peer as SwarmPeer, Role, PeerState,
    Message, ConsensusEntry, ModelUpdate,
)
from .node import MeshNode


class SwarmAdapter:
    """Connecte le MeshNode distribué (gRPC+QUIC) au SwarmEngine existant.

    Remplace les simulations in-memory du SwarmEngine par le vrai
    transport réseau MeshNode. SwarmEngine conserve son interface
    publique — l'adapter se charge de la traduction.
    """

    def __init__(self, mesh: MeshNode, swarm: SwarmEngine | None = None):
        self.mesh = mesh
        self.swarm = swarm or SwarmEngine(peer_id=mesh.identity.peer_id)
        self._synced = False

    def sync_peers_to_swarm(self) -> None:
        """Synchronise les pairs découverts via le mesh vers le SwarmEngine."""
        for p in self.mesh.discovery.all_peers():
            if p.peer_id == self.mesh.identity.peer_id:
                continue
            try:
                role = Role(p.role) if p.role else Role.OUVRIERE
            except ValueError:
                role = Role.OUVRIERE
            state = PeerState(p.state) if p.state else PeerState.DISCOVERED
            sp = SwarmPeer(
                peer_id=p.peer_id,
                address=f"{p.address}:{p.port}" if p.address else "",
                role=role,
                state=state,
                public_key=p.public_key,
                last_seen=p.last_seen,
                latency=p.latency,
                trust_score=p.trust_score,
            )
            existing = self.swarm.discovery.get_peer(p.peer_id)
            if not existing:
                self.swarm.discovery.add_peer(
                    p.peer_id,
                    address=sp.address,
                    role=role,
                    state=state,
                )
        self._synced = True

    def send_message(self, target: str, content: str,
                     msg_type: str = "data") -> Message | None:
        sp = self.swarm.discovery.get_peer(target)
        if not sp:
            mp = self.mesh.discovery.get_peer(target)
            if mp:
                sp = self.swarm.discovery.add_peer(
                    target, address=f"{mp.address}:{mp.port}" if mp.address else "",
                    state=PeerState.CONNECTED,
                )
            else:
                return None

        msg = Message(
            sender=self.mesh.identity.peer_id,
            content=content,
            msg_type=msg_type,
            timestamp=__import__("time").time(),
        )

        # Send over mesh gossip
        payload = json.dumps({
            "sender": msg.sender,
            "content": msg.content,
            "msg_type": msg.msg_type,
            "timestamp": msg.timestamp,
        }).encode()
        self.mesh.broadcast_gossip(f"msg/{target}", payload)
        self.swarm._messages_sent += 1
        return msg

    def raft_elect(self) -> int | None:
        return self.mesh.start_election()

    def raft_append(self, command: str, data: dict[str, Any] = None) -> ConsensusEntry | None:
        entry = self.mesh.append_log(command, data) if data else self.mesh.append_log(command)
        if entry:
            ce = ConsensusEntry(
                term=entry["term"],
                index=entry["index"],
                command=entry["command"],
                data=entry.get("data", {}),
            )
            self.swarm._commands_processed += 1
            return ce
        return None

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "stats")

        if action == "sync":
            self.sync_peers_to_swarm()
            return {"success": True, "action": "sync", "synced": self._synced,
                    "swarm_peers": self.swarm.discovery.count()}

        # Delegate non-mesh actions to swarm
        if action in ("set_role", "discover", "pbft_propose", "fed_round"):
            return self.swarm.process(input_data)

        # Intercept mesh-aware actions
        if action == "join":
            seeds = input_data.get("seeds", input_data.get("seed", ""))
            if isinstance(seeds, str):
                seeds = [s.strip() for s in seeds.split(",") if s.strip()]
            self.mesh.join(seeds)
            self.sync_peers_to_swarm()
            return {"success": True, "action": "join", "peer_id": self.mesh.identity.peer_id}

        elif action == "send":
            target = str(input_data.get("target", ""))
            content = str(input_data.get("content", ""))
            msg = self.send_message(target, content)
            if msg:
                return {"success": True, "action": "send", "message_type": msg.msg_type}
            return {"success": False, "error": f"peer '{target}' not found"}

        elif action == "raft_elect":
            term = self.raft_elect()
            return {"success": term is not None, "action": "raft_elect", "term": term}

        elif action == "raft_append":
            ce = self.raft_append(
                str(input_data.get("command", "")),
                input_data.get("data"),
            )
            if ce:
                return {"success": True, "action": "raft_append",
                        "index": ce.index, "term": ce.term}
            return {"success": False, "error": "not leader"}

        elif action == "stats":
            mesh_stats = self.mesh.get_stats()
            swarm_stats = self.swarm.get_stats()
            return {"success": True, "action": "stats",
                    "mesh": mesh_stats, "swarm": swarm_stats}

        return self.swarm.process(input_data)
