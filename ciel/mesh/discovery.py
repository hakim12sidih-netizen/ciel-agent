from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class PeerInfo:
    peer_id: str
    address: str = ""
    port: int = 0
    role: str = "ouvriere"
    state: int = 0
    public_key: str = ""
    protocol_version: int = 1
    capabilities: list[str] = field(default_factory=list)
    last_seen: float = 0.0
    latency: float = 0.0
    trust_score: float = 0.5
    first_seen: float = 0.0

    def is_active(self, timeout: float = 60.0) -> bool:
        return time.time() - self.last_seen < timeout


class PeerDiscovery:
    def __init__(self, peer_id: str, namespace: str = "ciel-net"):
        self.peer_id = peer_id
        self.namespace = namespace
        self._peers: dict[str, PeerInfo] = {}
        self._seeds: list[str] = []
        self._lock = threading.Lock()
        self._on_peer_added: list[Callable] = []
        self._on_peer_removed: list[Callable] = []

    def register_seed(self, address: str) -> None:
        if address not in self._seeds:
            self._seeds.append(address)

    def seeds(self) -> list[str]:
        return list(self._seeds)

    def add_peer(self, info: PeerInfo) -> PeerInfo:
        with self._lock:
            existing = self._peers.get(info.peer_id)
            if existing:
                existing.address = info.address or existing.address
                existing.port = info.port or existing.port
                existing.role = info.role or existing.role
                existing.state = info.state
                existing.last_seen = time.time()
                existing.latency = info.latency
                existing.trust_score = info.trust_score
                existing.capabilities = info.capabilities or existing.capabilities
                existing.protocol_version = info.protocol_version or existing.protocol_version
                result = existing
            else:
                if not info.first_seen:
                    info.first_seen = time.time()
                if not info.last_seen:
                    info.last_seen = time.time()
                self._peers[info.peer_id] = info
                result = info
        for cb in self._on_peer_added:
            try:
                cb(result)
            except Exception:
                pass
        return result

    def remove_peer(self, peer_id: str) -> bool:
        with self._lock:
            removed = self._peers.pop(peer_id, None) is not None
        if removed:
            for cb in self._on_peer_removed:
                try:
                    cb(peer_id)
                except Exception:
                    pass
        return removed

    def get_peer(self, peer_id: str) -> PeerInfo | None:
        with self._lock:
            return self._peers.get(peer_id)

    def all_peers(self) -> list[PeerInfo]:
        with self._lock:
            return list(self._peers.values())

    def active_peers(self, timeout: float = 60.0) -> list[PeerInfo]:
        now = time.time()
        with self._lock:
            return [p for p in self._peers.values()
                    if p.state != 0 and now - p.last_seen < timeout]

    def peers_by_role(self, role: str) -> list[PeerInfo]:
        with self._lock:
            return [p for p in self._peers.values() if p.role == role]

    def peer_count(self) -> int:
        with self._lock:
            return len(self._peers)

    def on_peer_added(self, cb: Callable) -> None:
        self._on_peer_added.append(cb)

    def on_peer_removed(self, cb: Callable) -> None:
        self._on_peer_removed.append(cb)

    def prune_stale(self, timeout: float = 300.0) -> list[str]:
        now = time.time()
        stale = []
        with self._lock:
            to_remove = [
                pid for pid, p in self._peers.items()
                if now - p.last_seen > timeout
            ]
            for pid in to_remove:
                self._peers.pop(pid, None)
                stale.append(pid)
        for pid in stale:
            for cb in self._on_peer_removed:
                try:
                    cb(pid)
                except Exception:
                    pass
        return stale

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "seeds": len(self._seeds),
            "peers": self.peer_count(),
            "active": len(self.active_peers()),
        }
