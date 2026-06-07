from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from aiohttp import web

from ciel.openclaw.channels.base import ChannelAdapter, ChannelMessage

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class RouteConfig:
    path: str
    method: str = "POST"
    channel: str = ""
    webhook_secret: str = ""
    description: str = ""


class GatewayServer:
    """Gateway HTTP/WS server for multi-platform message routing.

    Inspiré de openclaw-main/src/gateway/.
    Routes les messages entrants vers les adaptateurs de canaux appropriés.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self._app = web.Application()
        self._runner: web.AppRunner | None = None
        self._channels: dict[str, ChannelAdapter] = {}
        self._routes: list[RouteConfig] = []
        self._message_hooks: list[Callable[[ChannelMessage], Any]] = []
        self._running = False

    def register_channel(self, name: str, adapter: ChannelAdapter) -> None:
        self._channels[name] = adapter
        adapter.on_message(self._on_channel_message)
        logger.info(f"Registered channel: {name}")

    def add_route(self, route: RouteConfig) -> None:
        self._routes.append(route)
        async def handler(request: web.Request) -> web.Response:
            return await self._handle_webhook(route, request)
        self._app.router.add_route(route.method, route.path, handler)

    def add_webhook_route(
        self, path: str, channel: str, secret: str = "", method: str = "POST"
    ) -> None:
        self.add_route(RouteConfig(path=path, method=method, channel=channel, webhook_secret=secret))

    def on_message(self, hook: Callable[[ChannelMessage], Any]) -> None:
        self._message_hooks.append(hook)

    async def _handle_webhook(self, route: RouteConfig, request: web.Request) -> web.Response:
        body = await request.text()
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return web.Response(status=400, text="Invalid JSON")
        channel = self._channels.get(route.channel)
        if not channel:
            return web.Response(status=404, text=f"Channel {route.channel} not found")
        if hasattr(channel, "process_webhook"):
            messages = await channel.process_webhook(data)
            return web.Response(text=json.dumps({"ok": True, "messages": len(messages)}))
        return web.Response(status=200, text="ok")

    async def _on_channel_message(self, message: ChannelMessage) -> None:
        for hook in self._message_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(message)
                else:
                    hook(message)
            except Exception:
                logger.exception(f"Message hook failed for {message.id}")

    async def start(self) -> None:
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()
        self._running = True
        for name, adapter in self._channels.items():
            if not adapter.is_running():
                try:
                    await adapter.start()
                except Exception:
                    logger.exception(f"Failed to start channel: {name}")
        logger.info(f"Gateway server running on {self.host}:{self.port}")

    async def stop(self) -> None:
        self._running = False
        for name, adapter in self._channels.items():
            try:
                await adapter.stop()
            except Exception:
                logger.exception(f"Failed to stop channel: {name}")
        if self._runner:
            await self._runner.cleanup()

    @property
    def is_running(self) -> bool:
        return self._running

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "host": self.host,
            "port": self.port,
            "channels": {
                name: {"running": ch.is_running(), "config": ch.config.channel}
                for name, ch in self._channels.items()
            },
            "routes": [{"path": r.path, "method": r.method, "channel": r.channel} for r in self._routes],
        }
