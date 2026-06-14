from __future__ import annotations

import hashlib
import json
import math
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(Enum):
    REINE = "reine"
    OUVRIERE = "ouvriere"
    ECLAIREUSE = "eclaireuse"
    GARDIENNE = "gardienne"
    MERE = "mere"


class PeerState(Enum):
    OFFLINE = 0
    DISCOVERED = 1
    CONNECTED = 2
    SYNCED = 3
    FAULTY = 4


class ConsensusType(Enum):
    RAFT = "raft"
    PBFT = "pbft"


@dataclass(slots=True)
class Peer:
    peer_id: str
    address: str = ""
    role: Role = Role.OUVRIERE
    state: PeerState = PeerState.OFFLINE
    public_key: str = ""
    last_seen: float = 0.0
    latency: float = 0.0
    trust_score: float = 0.5


@dataclass(slots=True)
class Message:
    sender: str
    content: str
    msg_type: str = "data"
    timestamp: float = 0.0
    signature: str = ""
    ttl: int = 3


@dataclass(slots=True)
class ConsensusEntry:
    term: int = 0
    index: int = 0
    command: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelUpdate:
    peer_id: str
    weights: list[float] = field(default_factory=list)
    n_samples: int = 0
    accuracy: float = 0.0


class Discovery:
    """Découverte de pairs — DHT + mDNS simplifié."""

    def __init__(self, namespace: str = "ciel-net"):
        self.namespace = namespace
        self._peers: dict[str, Peer] = {}
        self._seeds: list[str] = []

    def register_seed(self, address: str) -> None:
        if address not in self._seeds:
            self._seeds.append(address)

    def add_peer(self, peer_id: str, address: str = "",
                 role: Role = Role.OUVRIERE,
                 state: PeerState = PeerState.DISCOVERED) -> Peer:
        peer = Peer(peer_id=peer_id, address=address, role=role,
                    state=state, last_seen=time.time())
        self._peers[peer_id] = peer
        return peer

    def remove_peer(self, peer_id: str) -> bool:
        return self._peers.pop(peer_id, None) is not None

    def get_peer(self, peer_id: str) -> Peer | None:
        return self._peers.get(peer_id)

    def all_peers(self) -> list[Peer]:
        return list(self._peers.values())

    def peers_by_role(self, role: Role) -> list[Peer]:
        return [p for p in self._peers.values() if p.role == role]

    def active_peers(self) -> list[Peer]:
        now = time.time()
        return [p for p in self._peers.values()
                if p.state != PeerState.OFFLINE and now - p.last_seen < 300]

    def dht_lookup(self, key: str) -> str | None:
        for pid, p in self._peers.items():
            if p.state == PeerState.CONNECTED or p.state == PeerState.SYNCED:
                h = hashlib.sha256((key + pid).encode()).hexdigest()[:8]
                if int(h, 16) % 100 < 30:
                    return pid
        return None

    def count(self) -> int:
        return len(self._peers)


class SecureTransport:
    """Transport sécurisé — Noise XX + Double Ratchet simplifié."""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}
        self._message_log: list[dict[str, Any]] = []

    def create_session(self, peer_id: str, public_key: str) -> dict[str, Any]:
        session = {
            "peer_id": peer_id,
            "public_key": public_key,
            "ephemeral": hashlib.sha256(f"ephemeral-{ peer_id }-{ random.random() }".encode()).hexdigest()[:16],
            "ratchet_step": 0,
            "created": time.time(),
        }
        self._sessions[peer_id] = session
        return session

    def encrypt(self, peer_id: str, plaintext: str) -> str | None:
        session = self._sessions.get(peer_id)
        if not session:
            return None
        session["ratchet_step"] += 1
        key = hashlib.sha256(
            f"{ session['ephemeral'] }-{ session['ratchet_step'] }".encode()
        ).hexdigest()[:16]
        cipher = "".join(chr(ord(c) ^ ord(k)) for c, k in zip(plaintext, key * (len(plaintext) // len(key) + 1)))
        self._message_log.append({
            "peer": peer_id, "step": session["ratchet_step"], "len": len(plaintext)
        })
        return cipher.encode("utf-8").hex()

    def decrypt(self, peer_id: str, cipherhex: str) -> str | None:
        session = self._sessions.get(peer_id)
        if not session:
            return None
        step = session["ratchet_step"]
        key = hashlib.sha256(
            f"{ session['ephemeral'] }-{ step }".encode()
        ).hexdigest()[:16]
        try:
            cipher = bytes.fromhex(cipherhex).decode("utf-8")
            plain = "".join(chr(ord(c) ^ ord(k)) for c, k in zip(cipher, key * (len(cipher) // len(key) + 1)))
            return plain
        except Exception:
            return None

    def session_count(self) -> int:
        return len(self._sessions)

    def message_count(self) -> int:
        return len(self._message_log)


class RaftConsensus:
    """Consensus Raft — élection + réplication de logs."""

    def __init__(self, peer_id: str):
        self.peer_id = peer_id
        self.term = 0
        self.voted_for: str | None = None
        self.log: list[ConsensusEntry] = []
        self.commit_index = 0
        self.role: str = "follower"
        self.leader_id: str | None = None
        self._votes_received = 0
        self._election_timeout = random.uniform(1.0, 3.0)
        self._last_heartbeat = time.time()

    def start_election(self) -> int:
        self.term += 1
        self.voted_for = self.peer_id
        self._votes_received = 1
        self.role = "candidate"
        self._last_heartbeat = time.time()
        return self.term

    def vote_for(self, candidate_id: str, candidate_term: int) -> bool:
        if candidate_term < self.term:
            return False
        if candidate_term == self.term and self.voted_for is not None:
            return False
        self.term = candidate_term
        self.voted_for = candidate_id
        return True

    def receive_heartbeat(self, leader_id: str, leader_term: int) -> bool:
        if leader_term < self.term:
            return False
        self.term = leader_term
        self.leader_id = leader_id
        self.role = "follower"
        self._last_heartbeat = time.time()
        return True

    def append_entry(self, command: str, data: dict[str, Any] = None) -> ConsensusEntry:
        entry = ConsensusEntry(
            term=self.term,
            index=len(self.log) + 1,
            command=command,
            data=data or {},
        )
        self.log.append(entry)
        return entry

    def last_log_term(self) -> int:
        return self.log[-1].term if self.log else 0

    def last_log_index(self) -> int:
        return len(self.log)

    def is_leader(self) -> bool:
        return self.role == "leader"

    def election_timeout_elapsed(self) -> bool:
        return time.time() - self._last_heartbeat > self._election_timeout


class PBFTConsensus:
    """PBFT — Practical Byzantine Fault Tolerance simplifié."""

    def __init__(self, peer_id: str, total_nodes: int = 4):
        self.peer_id = peer_id
        self.total_nodes = total_nodes
        self.view = 0
        self.sequence = 0
        self._prepared: list[dict[str, Any]] = []
        self._committed: list[dict[str, Any]] = []
        self._faulty = (total_nodes - 1) // 3

    def pre_prepare(self, request: dict[str, Any]) -> dict[str, Any]:
        self.sequence += 1
        msg = {
            "view": self.view,
            "sequence": self.sequence,
            "request": request,
            "sender": self.peer_id,
        }
        return msg

    def prepare(self, msg: dict[str, Any]) -> bool:
        if msg.get("view") != self.view:
            return False
        self._prepared.append(msg)
        return len(self._prepared) >= 2 * self._faulty + 1

    def commit(self, msg: dict[str, Any]) -> bool:
        prepared = sum(1 for p in self._prepared if p.get("sequence") == msg.get("sequence"))
        if prepared < 2 * self._faulty + 1:
            return False
        self._committed.append(msg)
        return len(self._committed) >= 2 * self._faulty + 1

    def fault_tolerance(self) -> int:
        return self._faulty

    def is_byzantine(self, peer_id: str) -> bool:
        return random.random() < self._faulty / max(self.total_nodes, 1)


class FederatedLearning:
    """Apprentissage fédéré — FedAvg, SCAFFOLD, Ditto."""

    def __init__(self):
        self._global_weights: list[float] = []
        self._updates: list[ModelUpdate] = []
        self._round = 0
        self._history: list[float] = []

    def fed_avg(self, updates: list[ModelUpdate]) -> list[float]:
        if not updates:
            return self._global_weights
        total_samples = sum(u.n_samples for u in updates)
        if total_samples == 0:
            return self._global_weights
        aggregated = [0.0] * len(updates[0].weights) if updates[0].weights else []
        for u in updates:
            weight = u.n_samples / total_samples
            for i, w in enumerate(u.weights):
                aggregated[i] += w * weight
        self._global_weights = aggregated
        self._updates = updates
        self._round += 1
        avg_acc = sum(u.accuracy for u in updates) / len(updates)
        self._history.append(avg_acc)
        return aggregated

    def scaffold(self, global_weights: list[float],
                 local_weights: list[float],
                 correction: list[float], lr: float = 0.1) -> list[float]:
        return [
            gw + lr * (lw - gw - c)
            for gw, lw, c in zip(global_weights, local_weights, correction)
        ]

    def ditto(self, global_weights: list[float],
              local_weights: list[float], lam: float = 0.5) -> list[float]:
        return [
            lam * gw + (1 - lam) * lw
            for gw, lw in zip(global_weights, local_weights)
        ]

    def get_round(self) -> int:
        return self._round

    def get_history(self) -> list[float]:
        return list(self._history)


class SwarmEngine:
    """Point d'entrée principal — SWARM : Fédération & Civilisation CIEL.

    Couvre la découverte de pairs (DHT/mDNS), le transport sécurisé
    (Noise XX + Double Ratchet), le consensus distribué (Raft, PBFT),
    et l'apprentissage fédéré (FedAvg, SCAFFOLD, Ditto).
    """

    def __init__(self, peer_id: str = "", namespace: str = "ciel-net"):
        self.peer_id = peer_id or f"ciel-{random.randint(1000, 9999)}"
        self.role = Role.OUVRIERE
        self.discovery = Discovery(namespace=namespace)
        self.transport = SecureTransport()
        self.raft = RaftConsensus(self.peer_id)
        self.pbft = PBFTConsensus(self.peer_id, total_nodes=4)
        self.federated = FederatedLearning()
        self._messages_sent = 0
        self._messages_received = 0
        self._commands_processed = 0

    def set_role(self, role: Role) -> None:
        self.role = role
        self.discovery.add_peer(self.peer_id, role=role)

    def join(self, seed_address: str = "") -> Peer:
        self.discovery.add_peer(self.peer_id, role=self.role,
                                state=PeerState.CONNECTED)
        if seed_address:
            self.discovery.register_seed(seed_address)
        return self.discovery.get_peer(self.peer_id)

    def send_message(self, target: str, content: str, msg_type: str = "data") -> Message | None:
        peer = self.discovery.get_peer(target)
        if not peer or peer.state == PeerState.OFFLINE:
            return None
        msg = Message(
            sender=self.peer_id,
            content=content,
            msg_type=msg_type,
            timestamp=time.time(),
        )
        cipher = self.transport.encrypt(target, content)
        msg.signature = cipher or ""
        self._messages_sent += 1
        return msg

    def receive_message(self, msg: Message) -> str:
        self._messages_received += 1
        plain = self.transport.decrypt(msg.sender, msg.signature)
        return plain or msg.content

    def raft_elect(self) -> int:
        return self.raft.start_election()

    def raft_append(self, command: str, data: dict[str, Any] = None) -> ConsensusEntry:
        self._commands_processed += 1
        return self.raft.append_entry(command, data)

    def pbft_propose(self, request: dict[str, Any]) -> dict[str, Any]:
        self._commands_processed += 1
        return self.pbft.pre_prepare(request)

    def federated_round(self, updates: list[ModelUpdate]) -> list[float]:
        return self.federated.fed_avg(updates)

    def get_stats(self) -> dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "role": self.role.value,
            "peers_discovered": self.discovery.count(),
            "peers_active": len(self.discovery.active_peers()),
            "sessions": self.transport.session_count(),
            "messages_sent": self._messages_sent,
            "messages_received": self._messages_received,
            "commands_processed": self._commands_processed,
            "raft_term": self.raft.term,
            "raft_role": self.raft.role,
            "raft_log_size": self.raft.last_log_index(),
            "pbft_view": self.pbft.view,
            "pbft_fault_tolerance": self.pbft.fault_tolerance(),
            "fed_round": self.federated.get_round(),
            "fed_history": self.federated.get_history(),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "join":
            self.join(str(data.get("seed", "")))
            return {"success": True, "action": "join", "peer_id": self.peer_id}

        elif action == "set_role":
            role_name = str(data.get("role", "ouvriere"))
            try:
                role = Role(role_name)
                self.set_role(role)
                return {"success": True, "action": "set_role", "role": role_name}
            except ValueError:
                return {"success": False, "error": f"unknown role '{role_name}'"}

        elif action == "send":
            target = str(data.get("target", ""))
            content = str(data.get("content", ""))
            msg = self.send_message(target, content)
            if msg:
                return {"success": True, "action": "send", "message": msg}
            return {"success": False, "error": f"peer '{target}' not found or offline"}

        elif action == "discover":
            return {"success": True, "action": "discover",
                    "peers": [{"id": p.peer_id, "role": p.role.value, "state": p.state.name}
                              for p in self.discovery.all_peers()]}

        elif action == "raft_elect":
            term = self.raft_elect()
            return {"success": True, "action": "raft_elect", "term": term}

        elif action == "raft_append":
            entry = self.raft_append(str(data.get("command", "")),
                                     data.get("data"))
            return {"success": True, "action": "raft_append",
                    "index": entry.index, "term": entry.term}

        elif action == "pbft_propose":
            req = data.get("request", {})
            msg = self.pbft_propose(req)
            return {"success": True, "action": "pbft_propose",
                    "sequence": msg.get("sequence")}

        elif action == "fed_round":
            raw = data.get("updates", [])
            updates = []
            for u in raw:
                if isinstance(u, dict):
                    updates.append(ModelUpdate(
                        peer_id=u.get("peer_id", ""),
                        weights=u.get("weights", []),
                        n_samples=u.get("n_samples", 0),
                        accuracy=u.get("accuracy", 0.0),
                    ))
            aggregated = self.federated_round(updates)
            return {"success": True, "action": "fed_round",
                    "round": self.federated.get_round(),
                    "weights_count": len(aggregated)}

        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
