"""
CIEL v1.0 — Gateway : serveur de passerelle multi-plateforme avec daemon.

Composant CIEL natif — passerelle de communication unifiée :
  - GatewayServer : serveur HTTP/WebSocket avec état persistant
  - GatewayState : état SQLite des channels, sessions, métriques
  - GatewayAuth : authentification device pairing + OAuth
  - GatewayAPI : API REST pour le dashboard
  - Router : routage des messages vers les agents/workspaces
  - Daemon : service systemd/launchd persistant
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ciel.gateway.state import GatewayState, ChannelState, SessionState
from ciel.gateway.auth import GatewayAuth, Device
from ciel.gateway.router import Router, Route, create_default_routes
from ciel.gateway.daemon import (
    install, uninstall, stop, is_running, get_pid, serve, write_pid, remove_pid,
)
from ciel.llmbridge.gateway.hdlm import ChannelParams, init_channels, init_llm
from ciel.llmbridge.gateway.base import Message, MessageDirection
from ciel.channels import ChannelManager, Message as ChannelMessage
from ciel.swarm.gateway_bridge import SwarmGatewayBridge

logger = logging.getLogger(__name__)


class GatewayServer:
    """Serveur de passerelle CIEL — point d'entrée unique.

    Consolide :
      - Messages des canaux (Telegram, Discord, Slack, etc.)
      - Appels API REST
      - WebSocket JSON-RPC
      - CLI
      - Essaim CIEL-NET fédéré
    """

    def __init__(self, state: GatewayState | None = None,
                 auth: GatewayAuth | None = None):
        self.state = state or GatewayState()
        self.auth = auth or GatewayAuth()
        self.router = Router()
        self.router.add_routes(create_default_routes())
        self.router.register_handler("help", self._handle_help)
        self.router.register_handler("status", self._handle_status)
        self.router.register_handler("chat", self._handle_chat)
        self.swarm_bridge = SwarmGatewayBridge()
        self.swarm_bridge.bind_gateway(self)
        self._adapters: dict[str, Any] = {}
        self._api = None
        self._running = False
        self._start_time: float = 0.0

    def _handle_help(self, text: str = "", platform: str = "", **kwargs: Any) -> str:
        return (
            "🤖 *CIEL Gateway*\n"
            "Commandes disponibles :\n"
            "  /help  — Cette aide\n"
            "  /status — État du système\n"
            "  /channels — Canaux connectés\n\n"
            "Posez une question pour parler avec l'agent CIEL."
        )

    def _handle_status(self, text: str = "", platform: str = "", **kwargs: Any) -> str:
        st = self.state.status()
        m = st["metrics"]
        return (
            f"*CIEL Gateway*\n"
            f"Uptime : {m['uptime']:.0f}s\n"
            f"Messages : {m['total_messages']}\n"
            f"Canaux : {m['active_channels']}/{st['channels']}\n"
            f"Sessions : {st['sessions']}"
        )

    def _handle_chat(self, text: str = "", platform: str = "",
                     chat_id: str = "", **kwargs: Any) -> str | None:
        from ciel.llmbridge.core import LLMBridgeEngine
        engine = LLMBridgeEngine()
        response = engine.chat(text, context={"platform": platform, "chat_id": chat_id})
        return str(response) if response else None

    def start(self) -> bool:
        self._running = True
        self._start_time = time.time()

        channel_params = ChannelParams.from_env()
        adapters = init_channels(channel_params)
        self._adapters.update(adapters)

        for name, adapter in adapters.items():
            cid = self.state.register_channel(name)
            adapter.on_message(lambda msg, c=cid: self._on_adapter_message(msg, c))
            asyncio.create_task(self._start_adapter(name, adapter, cid))

        from ciel.gateway.api import GatewayAPI
        self._api = GatewayAPI(self.state, self.auth, self.router)
        asyncio.create_task(self._start_api())

        logger.info(f"Gateway started with {len(adapters)} channel(s)")
        return True

    async def _start_adapter(self, name: str, adapter: Any, cid: str) -> None:
        try:
            await adapter.start()
            self.state.update_channel(cid, connected=True)
            logger.info(f"Channel {name} connected")
        except Exception as e:
            self.state.update_channel(cid, connected=False)
            self.state.record_error(cid)
            logger.error(f"Channel {name} failed: {e}")

    async def _start_api(self) -> None:
        if self._api:
            try:
                await self._api.start()
            except Exception as e:
                logger.error(f"API server failed: {e}")

    def stop(self) -> bool:
        self._running = False
        for name, adapter in self._adapters.items():
            try:
                asyncio.create_task(adapter.stop())
            except Exception:
                pass
        if self._api:
            asyncio.create_task(self._api.stop())
        if self._start_time:
            uptime = time.time() - self._start_time
            logger.info(f"Gateway stopped after {uptime:.0f}s")
        return True

    def _on_adapter_message(self, message: Message, channel_id: str) -> None:
        self.state.record_message(channel_id, "incoming")
        self.state.metrics.total_messages += 1

        target = self.router.route(
            message.platform, message.text,
            chat_id=message.chat_id,
            sender_id=message.sender_id,
        )
        if target:
            logger.info(f"Routed message to {target}")

    def status(self) -> dict[str, Any]:
        st = self.state.status()
        return {
            "running": self._running,
            "uptime_s": round(time.time() - self._start_time, 2) if self._start_time else 0,
            "channels": {
                name: {"running": getattr(adapter, '_running', False)}
                for name, adapter in self._adapters.items()
            },
            "state": st,
        }


_gateway: GatewayServer | None = None


def get_gateway() -> GatewayServer:
    global _gateway
    if _gateway is None:
        _gateway = GatewayServer()
    return _gateway


def reset_gateway() -> None:
    global _gateway
    _gateway = None
