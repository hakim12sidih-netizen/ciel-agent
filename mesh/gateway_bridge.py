from __future__ import annotations

import json
import logging
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork
from .node import MeshNode

log = logging.getLogger("ciel.mesh.gateway")


class GatewayBridge:
    """Pont entre le MeshNode distribué et le Gateway CIEL.

    Enregistre des handlers d'événements sur le LeaderNetwork
    pour que les événements du mesh soient dispatchables via
    le Gateway (methodes mesh.*).
    """

    def __init__(self, mesh: MeshNode):
        self.mesh = mesh
        self.network = mesh.network
        self._method_registry: dict[str, Any] = {}
        self._event_subscriptions: list[str] = []

    def register_gateway_methods(self, gateway: Any) -> None:
        """Enregistre les méthodes mesh.* sur une instance GatewayServer."""
        methods = [
            ("mesh.status", self._cmd_status, "État du mesh distribué"),
            ("mesh.peers", self._cmd_peers, "Liste des pairs connectés"),
            ("mesh.connect", self._cmd_connect, "Connexion à un pair distant"),
            ("mesh.gossip", self._cmd_gossip, "Diffuser un message gossip"),
            ("mesh.find", self._cmd_find, "Trouver un pair par son ID"),
            ("mesh.elect", self._cmd_elect, "Démarrer une élection Raft"),
            ("mesh.stats", self._cmd_stats, "Statistiques détaillées du mesh"),
        ]
        for name, handler, desc in methods:
            try:
                gateway.register_method(name, handler, desc, scope="admin")
                self._method_registry[name] = handler
            except Exception as e:
                log.warning("Could not register %s: %s", name, e)

    def subscribe_events(self) -> None:
        events = [
            "mesh.started", "mesh.stopped",
            "mesh.peer_connected", "mesh.peer_lost",
            "mesh.elected", "mesh.gossip",
        ]
        for event in events:
            self.network.subscribe(event, self._make_handler(event))
            self._event_subscriptions.append(event)

    def _make_handler(self, event: str):
        def handler(data: Any) -> None:
            log.debug("Mesh event: %s %s", event, data)
        return handler

    # ── Commandes Gateway ──

    def _cmd_status(self, **kwargs) -> dict:
        stats = self.mesh.get_stats()
        return {
            "status": "running" if self.mesh._running else "stopped",
            "peer_id": stats["peer_id"],
            "address": f"{stats['address']}:{stats['port']}",
            "peers": stats["peers"],
            "active": stats["active_peers"],
            "raft_role": stats["raft_role"],
            "raft_term": stats["raft_term"],
            "namespace": stats["namespace"],
        }

    def _cmd_peers(self, **kwargs) -> dict:
        peers = self.mesh.get_peers()
        return {"count": len(peers), "peers": peers}

    def _cmd_connect(self, address: str = "", port: int = 0, **kwargs) -> dict:
        if not address or not port:
            return {"status": "error", "message": "address and port required"}
        ok = self.mesh.connect_to(address, port)
        return {"status": "ok" if ok else "error"}

    def _cmd_gossip(self, topic: str = "general",
                    payload: dict = None, **kwargs) -> dict:
        payload_bytes = json.dumps(payload or {}).encode()
        self.mesh.broadcast_gossip(topic, payload_bytes)
        return {"status": "sent", "topic": topic}

    def _cmd_find(self, peer_id: str = "", **kwargs) -> dict:
        if not peer_id:
            return {"status": "error", "message": "peer_id required"}
        peer = self.mesh.find_peer(peer_id)
        if peer:
            return {"status": "found", "peer": {
                "peer_id": peer.peer_id,
                "address": peer.address,
                "port": peer.port,
                "role": peer.role,
            }}
        return {"status": "not_found"}

    def _cmd_elect(self, **kwargs) -> dict:
        term = self.mesh.start_election()
        return {"status": "elected" if term else "lost", "term": term}

    def _cmd_stats(self, **kwargs) -> dict:
        return {"status": "ok", "stats": self.mesh.get_stats()}
