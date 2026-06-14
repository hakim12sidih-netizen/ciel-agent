"""DHT — Distributed Hash Table for swarm overlay."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("ciel.swarm.dht")


class DHTNode:
    """Nœud DHT pour le swarm overlay."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._data: dict[str, Any] = {}

    def store(self, key: str, value: Any) -> bool:
        log.info("DHT stub: store %s", key)
        self._data[key] = value
        return True

    def lookup(self, key: str) -> Any | None:
        return self._data.get(key)

    def remove(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    def peers(self) -> list[str]:
        return []


def create_dht(bootstrap: list[str] | None = None) -> DHTNode:
    return DHTNode(node_id="dht-stub")
