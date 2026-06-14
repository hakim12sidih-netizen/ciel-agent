from __future__ import annotations

import json
import logging
import random
import threading
import time
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization

from ciel.evolution.leader_network import LeaderNetwork

from .identity import NodeIdentity
from .discovery import PeerDiscovery, PeerInfo
from .transport import GrpcTransport

log = logging.getLogger("ciel.mesh.node")


class MeshNode:
    def __init__(self, identity: NodeIdentity | None = None,
                 namespace: str = "ciel-net",
                 host: str = "0.0.0.0", port: int = 0,
                 data_dir: str | None = None):
        self.identity = identity or NodeIdentity.generate()
        self.namespace = namespace
        self.host = host
        self.port = port
        self.data_dir = Path(data_dir) if data_dir else Path.home() / ".ciel" / "mesh"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.discovery = PeerDiscovery(self.identity.peer_id, namespace)
        self.transport = GrpcTransport(self.identity, self.discovery, host, port)
        self.network = LeaderNetwork()

        self._running = False
        self._tick_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._mesh_stats: dict[str, Any] = {
            "messages_sent": 0,
            "messages_received": 0,
            "gossip_sent": 0,
            "pings_sent": 0,
            "elections_started": 0,
        }

        self.transport.on_gossip(self._handle_gossip)
        self.transport.on_peer_connected(self._handle_peer_connected)

    # ── Lifecycle ──

    def start(self) -> bool:
        if self._running:
            return True
        ok = self.transport.start()
        if not ok:
            return False
        self.port = self.transport.port
        self.host = self.transport.host
        self.identity.address = self.host
        self.identity.port = self.port
        self._running = True
        self.discovery.add_peer(PeerInfo(
            peer_id=self.identity.peer_id,
            address=self.host,
            port=self.port,
            role="ouvriere",
            state=2,
            public_key=self.identity.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            ).hex(),
            protocol_version=self.identity.protocol_version,
            capabilities=list(self.identity.capabilities),
            last_seen=time.time(),
            first_seen=time.time(),
        ))
        self._tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._tick_thread.start()
        self.network.emit("mesh.started", {
            "peer_id": self.identity.peer_id,
            "address": self.host,
            "port": self.port,
        })
        log.info("MeshNode %s started on %s:%d", self.identity.peer_id, self.host, self.port)
        return True

    def stop(self) -> None:
        self._running = False
        if self._tick_thread:
            self._tick_thread.join(timeout=3)
        self.transport.stop()
        self.network.emit("mesh.stopped", {"peer_id": self.identity.peer_id})

    def save_state(self) -> None:
        self.identity.save(str(self.data_dir / "identity.json"))
        peers_file = self.data_dir / "known_peers.json"
        peers_data = [
            {"peer_id": p.peer_id, "address": p.address, "port": p.port,
             "role": p.role, "public_key": p.public_key,
             "trust_score": p.trust_score}
            for p in self.discovery.all_peers()
        ]
        peers_file.write_text(json.dumps(peers_data, indent=2))

    # ── Peer Management ──

    def join(self, seeds: list[str] = None, discover_interval: float = 5.0) -> None:
        seeds = seeds or []
        for s in seeds:
            self.discovery.register_seed(s)
        self._bootstrap()

    def _bootstrap(self) -> None:
        for seed in self.discovery.seeds():
            try:
                host, port_str = seed.rsplit(":", 1)
                port = int(port_str)
                fake = PeerInfo(
                    peer_id=f"seed-{seed}", address=host,
                    port=port, state=0,
                )
                latency = self.transport.ping(fake)
                if latency is not None:
                    fake.peer_id = f"seed-{host}-{port}"
                    known = self.discovery.active_peers()
                    log.info("Connected to seed %s (latency: %.1fms)", seed, latency * 1000)
                    self.network.emit("mesh.peer_connected", {
                        "peer_id": fake.peer_id,
                        "address": host,
                        "port": port,
                    })
            except Exception as e:
                log.debug("Seed %s unreachable: %s", seed, e)

    def connect_to(self, address: str, port: int) -> bool:
        peer = self.discovery.get_peer(f"{address}:{port}")
        if not peer:
            peer = PeerInfo(
                peer_id=f"{address}:{port}",
                address=address, port=port, state=0,
            )
        latency = self.transport.ping(peer)
        if latency is not None:
            self.discovery.add_peer(peer)
            self.transport.announce(peer)
            return True
        return False

    def broadcast_gossip(self, topic: str, payload: bytes, ttl: int = 3) -> None:
        self._mesh_stats["gossip_sent"] += 1
        self.transport.gossip(topic, payload, ttl)

    def find_peer(self, peer_id: str) -> PeerInfo | None:
        local = self.discovery.get_peer(peer_id)
        if local:
            return local
        for peer in self.discovery.active_peers():
            if peer.peer_id == self.identity.peer_id:
                continue
            stub = self.transport._get_stub(peer)
            if not stub:
                continue
            try:
                from .proto import FindPeerRequest
                resp = stub.FindPeer(FindPeerRequest(
                    target_id=peer_id,
                    requester_id=self.identity.peer_id,
                    max_hops=3,
                ), timeout=3)
                if resp.found and resp.peer.peer_id:
                    info = PeerInfo(
                        peer_id=resp.peer.peer_id,
                        address=resp.peer.address,
                        port=resp.peer.port,
                        role=resp.peer.role,
                        public_key=resp.peer.public_key,
                    )
                    self.discovery.add_peer(info)
                    return info
            except Exception:
                continue
        return None

    # ── Raft Consensus ──

    def start_election(self) -> int | None:
        self._mesh_stats["elections_started"] += 1
        state = self.transport._raft_state
        state["current_term"] += 1
        state["voted_for"] = self.identity.peer_id
        state["role"] = "candidate"
        term = state["current_term"]
        votes = 1
        for peer in self.discovery.active_peers():
            if peer.peer_id == self.identity.peer_id:
                continue
            granted = self.transport.request_vote(peer)
            if granted:
                votes += 1
        majority = (self.discovery.peer_count() // 2) + 1
        if votes >= majority:
            state["role"] = "leader"
            self.network.emit("mesh.elected", {"term": term, "votes": votes})
            log.info("Elected leader for term %d (%d/%d votes)", term, votes, self.discovery.peer_count())
            return term
        log.info("Election lost for term %d (%d/%d votes)", term, votes, self.discovery.peer_count())
        return None

    def append_log(self, command: str, data: dict = None) -> dict | None:
        state = self.transport._raft_state
        if state["role"] != "leader":
            return None
        entry = {
            "term": state["current_term"],
            "index": len(self.transport._raft_log) + 1,
            "command": command,
            "data": data or {},
            "timestamp": time.time(),
        }
        self.transport._raft_log.append(entry)
        for peer in self.discovery.active_peers():
            if peer.peer_id == self.identity.peer_id:
                continue
            self.transport.append_entries(peer, [entry])
        self.network.emit("mesh.log_appended", {"index": entry["index"], "command": command})
        return entry

    # ── Internal ──

    def _tick_loop(self) -> None:
        while self._running:
            try:
                self._tick()
            except Exception as e:
                log.debug("Tick error: %s", e)
            time.sleep(5.0)

    def _tick(self) -> None:
        self._mesh_stats["pings_sent"] += 1
        for peer in self.discovery.all_peers():
            if peer.peer_id == self.identity.peer_id:
                continue
            if peer.address and peer.port:
                self.transport.ping(peer)
        stale = self.discovery.prune_stale(timeout=120.0)
        if stale:
            for pid in stale:
                self.network.emit("mesh.peer_lost", {"peer_id": pid})

    def _handle_gossip(self, msg: Any) -> None:
        self._mesh_stats["messages_received"] += 1
        self.network.emit("mesh.gossip", {
            "topic": msg.topic,
            "sender": msg.sender_id,
            "payload_len": len(msg.payload),
            "msg_id": msg.msg_id,
        })

    def _handle_peer_connected(self, peer_id: str) -> None:
        self.network.emit("mesh.peer_connected", {"peer_id": peer_id})

    # ── Stats ──

    def get_stats(self) -> dict[str, Any]:
        return {
            "peer_id": self.identity.peer_id,
            "address": self.host,
            "port": self.port,
            "namespace": self.namespace,
            "running": self._running,
            "peers": self.discovery.peer_count(),
            "active_peers": len(self.discovery.active_peers()),
            "seeds": len(self.discovery.seeds()),
            "raft_role": self.transport._raft_state["role"],
            "raft_term": self.transport._raft_state["current_term"],
            "raft_log_size": len(self.transport._raft_log),
            "messages_sent": self._mesh_stats["messages_sent"],
            "messages_received": self._mesh_stats["messages_received"],
            "gossip_sent": self._mesh_stats["gossip_sent"],
            "elections_started": self._mesh_stats["elections_started"],
        }

    def get_peers(self) -> list[dict[str, Any]]:
        return [
            {
                "peer_id": p.peer_id,
                "address": p.address,
                "port": p.port,
                "role": p.role,
                "state": p.state,
                "latency_ms": round(p.latency * 1000, 1),
                "trust_score": round(p.trust_score, 2),
                "last_seen": p.last_seen,
                "is_active": p.is_active(),
            }
            for p in self.discovery.all_peers()
            if p.peer_id != self.identity.peer_id
        ]

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "start":
            ok = self.start()
            return {"success": ok, "peer_id": self.identity.peer_id}

        elif action == "stop":
            self.stop()
            return {"success": True}

        elif action == "join":
            seeds = data.get("seeds", [])
            if isinstance(seeds, str):
                seeds = [seeds]
            self.join(seeds)
            return {"success": True, "peer_id": self.identity.peer_id}

        elif action == "connect":
            addr = str(data.get("address", ""))
            port = int(data.get("port", 0))
            ok = self.connect_to(addr, port)
            return {"success": ok}

        elif action == "gossip":
            topic = str(data.get("topic", "general"))
            payload = json.dumps(data.get("payload", {})).encode()
            self.broadcast_gossip(topic, payload)
            return {"success": True}

        elif action == "find_peer":
            target = str(data.get("target", ""))
            peer = self.find_peer(target)
            if peer:
                return {"success": True, "peer": {
                    "peer_id": peer.peer_id, "address": peer.address,
                    "port": peer.port, "role": peer.role,
                }}
            return {"success": False, "error": "peer not found"}

        elif action == "elect":
            term = self.start_election()
            return {"success": term is not None, "term": term}

        elif action == "append_log":
            entry = self.append_log(
                str(data.get("command", "")),
                data.get("data"),
            )
            return {"success": entry is not None, "entry": entry}

        elif action == "peers":
            return {"success": True, "peers": self.get_peers()}

        elif action == "stats":
            return {"success": True, "stats": self.get_stats()}

        elif action == "save":
            self.save_state()
            return {"success": True}

        return {"success": False, "error": f"unknown action '{action}'"}
