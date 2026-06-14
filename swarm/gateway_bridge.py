"""
CIEL v1.0 — Swarm-Gateway Bridge.

Relie l'essaim CIEL-NET au gateway multi-plateforme.
Les messages des canaux (Telegram, Discord, Slack) peuvent être
routés vers l'essaim, et l'essaim peut diffuser des messages
vers tous les canaux connectés.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from ciel.swarm import SwarmEngine, Peer, Message as SwarmMsg, Role

logger = logging.getLogger(__name__)


class SwarmGatewayBridge:
    """Pont entre le gateway multi-plateforme et l'essaim CIEL-NET.

    Permet :
    - Routage des messages gateway → essaim
    - Diffusion des décisions essaim → gateway channels
    - Fédération des découvertes de pairs
    """

    def __init__(self, swarm: SwarmEngine | None = None):
        self.swarm = swarm or SwarmEngine()
        self._gateway = None
        self._channel_map: dict[str, str] = {}

    def bind_gateway(self, gateway: Any) -> None:
        self._gateway = gateway

    def route_to_swarm(self, platform: str, text: str,
                       chat_id: str = "", sender_id: str = "") -> str | None:
        """Route un message gateway vers l'essaim."""
        target = self._find_swarm_target(platform, text)
        if not target:
            return None
        msg = self.swarm.send_message(target.peer_id, text, "gateway")
        if msg:
            logger.info(f"Routed {platform} message to swarm peer {target.peer_id}")
            return target.peer_id
        return None

    def _find_swarm_target(self, platform: str, text: str) -> Peer | None:
        active = self.swarm.discovery.active_peers()
        if not active:
            return None
        # Prefer queen/reine for complex queries, worker/ouvriere for simple
        if len(text) > 100:
            for p in active:
                if p.role == Role.REINE:
                    return p
        for p in active:
            if p.role == Role.OUVRIERE:
                return p
        return active[0]

    def broadcast_to_channels(self, content: str,
                              platforms: list[str] | None = None) -> dict[str, bool]:
        """Diffuse un message de l'essaim vers tous les canaux gateway."""
        if not self._gateway:
            return {}
        results: dict[str, bool] = {}
        for name, adapter in getattr(self._gateway, '_adapters', {}).items():
            if platforms and name not in platforms:
                continue
            try:
                import asyncio
                asyncio.create_task(adapter.send_text(
                    chat_id="",
                    text=f"[{self.swarm.peer_id}] {content}",
                ))
                results[name] = True
            except Exception as e:
                logger.error(f"Broadcast to {name} failed: {e}")
                results[name] = False
        return results

    def federate_peers(self, remote_peers: list[dict[str, Any]]) -> int:
        """Fédère une liste de pairs découverts depuis un autre nœud."""
        count = 0
        for p in remote_peers:
            pid = p.get("peer_id", "")
            if pid and not self.swarm.discovery.get_peer(pid):
                try:
                    role = Role(p.get("role", "ouvriere"))
                except ValueError:
                    role = Role.OUVRIERE
                self.swarm.discovery.add_peer(
                    pid, p.get("address", ""), role,
                )
                count += 1
        if count:
            logger.info(f"Federated {count} new peers from remote")
        return count

    def get_swarm_status(self) -> dict[str, Any]:
        stats = self.swarm.get_stats()
        return {
            "swarm": stats,
            "peers": [
                {"id": p.peer_id, "role": p.role.value,
                 "state": p.state.name, "address": p.address}
                for p in self.swarm.discovery.all_peers()
            ],
        }
