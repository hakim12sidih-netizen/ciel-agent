from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from .base import InterfaceBackend

log = logging.getLogger("ciel.interfaces.backends.web")


class WebBackend(InterfaceBackend):
    def __init__(self):
        super().__init__(name="Web UI", mode="web")
        self._ws_port = 9877
        self._ws_server = None

    @property
    def description(self) -> str:
        return "Interface web avec WebSocket. Chat en direct, session management, outils."

    @property
    def required_dependencies(self) -> list[str]:
        return []

    def start(self) -> bool:
        self._running = True
        log.info("Web backend ready (WebSocket port: %d)", self._ws_port)
        return True

    def stop(self) -> bool:
        self._running = False
        return True

    async def start_ws_server(self):
        import websockets
        self._ws_server = await websockets.serve(
            self._handle_ws, "127.0.0.1", self._ws_port,
            ping_interval=30, ping_timeout=10,
        )
        log.info("Web backend WebSocket on ws://127.0.0.1:%d", self._ws_port)

    async def stop_ws_server(self):
        if self._ws_server:
            self._ws_server.close()
            await self._ws_server.wait_closed()

    async def _handle_ws(self, websocket):
        async for msg in websocket:
            await websocket.send(f"Echo: {msg}")

    def serve_html(self) -> str:
        html_path = Path(__file__).parent.parent / "web" / "ide.html"
        if html_path.exists():
            return html_path.read_text(encoding="utf-8")
        return "<html><body><h1>CIEL Web</h1></body></html>"
