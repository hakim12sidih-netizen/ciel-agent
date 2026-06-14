from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from aiohttp import web

from ciel.gateway.state import GatewayState
from ciel.gateway.auth import GatewayAuth
from ciel.gateway.router import Router

logger = logging.getLogger(__name__)


class GatewayAPI:
    def __init__(self, state: GatewayState, auth: GatewayAuth, router: Router,
                 host: str = "127.0.0.1", port: int = 8787):
        self.state = state
        self.auth = auth
        self.router = router
        self.host = host
        self.port = port
        self._app = web.Application()
        self._runner: web.AppRunner | None = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_get("/status", self._handle_status)
        self._app.router.add_get("/channels", self._handle_list_channels)
        self._app.router.add_post("/channels/register", self._handle_register_channel)
        self._app.router.add_delete("/channels/{channel_id}", self._handle_remove_channel)
        self._app.router.add_get("/sessions", self._handle_list_sessions)
        self._app.router.add_post("/sessions", self._handle_create_session)
        self._app.router.add_post("/sessions/{session_id}/close", self._handle_close_session)
        self._app.router.add_post("/auth/pair", self._handle_generate_pairing)
        self._app.router.add_post("/auth/verify", self._handle_verify_pairing)
        self._app.router.add_post("/auth/session", self._handle_create_auth_session)
        self._app.router.add_get("/devices", self._handle_list_devices)
        self._app.router.add_delete("/devices/{device_id}", self._handle_remove_device)
        self._app.router.add_post("/message", self._handle_send_message)
        self._app.router.add_get("/metrics", self._handle_metrics)

    async def start(self) -> None:
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()
        logger.info(f"Gateway API running on {self.host}:{self.port}")

    async def stop(self) -> None:
        if self._runner:
            await self._runner.cleanup()

    def _json_response(self, data: Any, status: int = 200) -> web.Response:
        return web.Response(
            text=json.dumps(data, indent=2, default=str),
            status=status,
            content_type="application/json",
        )

    def _get_auth_session(self, request: web.Request) -> Any | None:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return None
        return self.auth.validate_session(token)

    async def _handle_health(self, request: web.Request) -> web.Response:
        return self._json_response({"status": "ok", "timestamp": time.time()})

    async def _handle_status(self, request: web.Request) -> web.Response:
        st = self.state.status()
        channels = [{"id": c.id, "platform": c.platform, "connected": c.connected}
                     for c in self.state.list_channels()]
        return self._json_response({"status": st, "channels": channels})

    async def _handle_list_channels(self, request: web.Request) -> web.Response:
        platform = request.query.get("platform", "")
        channels = self.state.list_channels(platform)
        return self._json_response({
            "channels": [vars(c) for c in channels],
        })

    async def _handle_register_channel(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return self._json_response({"error": "invalid JSON"}, 400)
        platform = data.get("platform", "")
        if not platform:
            return self._json_response({"error": "platform required"}, 400)
        cid = self.state.register_channel(platform, data.get("config"))
        return self._json_response({"id": cid, "platform": platform}, 201)

    async def _handle_remove_channel(self, request: web.Request) -> web.Response:
        channel_id = request.match_info.get("channel_id", "")
        if self.state.remove_channel(channel_id):
            return self._json_response({"status": "removed"})
        return self._json_response({"error": "not found"}, 404)

    async def _handle_list_sessions(self, request: web.Request) -> web.Response:
        channel_id = request.query.get("channel_id", "")
        sessions = self.state.list_sessions(channel_id)
        return self._json_response({
            "sessions": [vars(s) for s in sessions],
        })

    async def _handle_create_session(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return self._json_response({"error": "invalid JSON"}, 400)
        sid = self.state.create_session(
            data.get("channel_id", ""),
            data.get("user_id", ""),
            data.get("workspace_id", ""),
        )
        return self._json_response({"id": sid}, 201)

    async def _handle_close_session(self, request: web.Request) -> web.Response:
        session_id = request.match_info.get("session_id", "")
        if self.state.close_session(session_id):
            return self._json_response({"status": "closed"})
        return self._json_response({"error": "not found"}, 404)

    async def _handle_generate_pairing(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return self._json_response({"error": "invalid JSON"}, 400)
        code, device_id = self.auth.generate_pairing_code(
            data.get("device_name", "Unknown"),
            ttl=data.get("ttl", 300),
        )
        return self._json_response({"code": code, "device_id": device_id})

    async def _handle_verify_pairing(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return self._json_response({"error": "invalid JSON"}, 400)
        device_id = self.auth.verify_pairing(data.get("code", ""))
        if device_id:
            token = self.auth.create_session(device_id)
            return self._json_response({"device_id": device_id, "token": token})
        return self._json_response({"error": "invalid or expired code"}, 401)

    async def _handle_create_auth_session(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return self._json_response({"error": "invalid JSON"}, 400)
        device_id = data.get("device_id", "")
        device = self.auth.get_device(device_id)
        if not device or not device.verified:
            return self._json_response({"error": "device not verified"}, 401)
        token = self.auth.create_session(device_id, data.get("scope"))
        return self._json_response({"token": token})

    async def _handle_list_devices(self, request: web.Request) -> web.Response:
        devices = self.auth.list_devices()
        return self._json_response({
            "devices": [vars(d) for d in devices],
        })

    async def _handle_remove_device(self, request: web.Request) -> web.Response:
        device_id = request.match_info.get("device_id", "")
        if self.auth.remove_device(device_id):
            return self._json_response({"status": "removed"})
        return self._json_response({"error": "not found"}, 404)

    async def _handle_send_message(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return self._json_response({"error": "invalid JSON"}, 400)
        platform = data.get("platform", "")
        text = data.get("text", "")
        chat_id = data.get("chat_id", "")
        if not platform or not text:
            return self._json_response({"error": "platform and text required"}, 400)
        result = self.router.route(platform, text, chat_id=chat_id)
        self.state.record_message("api", "outgoing")
        return self._json_response({"routed": True, "target": result})

    async def _handle_metrics(self, request: web.Request) -> web.Response:
        return self._json_response(vars(self.state.metrics))
