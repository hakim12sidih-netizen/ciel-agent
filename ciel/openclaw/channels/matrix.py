from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from ciel.openclaw.channels.base import ChannelAdapter, ChannelConfig, ChannelMessage, MessageType

logger = logging.getLogger(__name__)


class MatrixAdapter(ChannelAdapter):
    """Matrix protocol adapter via Matrix Client-Server API."""

    def __init__(self, config: ChannelConfig) -> None:
        super().__init__(config)
        self._session: aiohttp.ClientSession | None = None
        self._homeserver: str = config.server_url or "https://matrix.org"
        self._access_token: str = ""
        self._user_id: str = ""
        self._device_id: str = ""
        self._sync_token: str = ""
        self._poll_task: asyncio.Task[None] | None = None
        self._rooms: set[str] = set()

    async def start(self) -> None:
        token = self.config.api_key
        self._user_id = self.config.extra.get("user_id", "")
        if not token or not self._user_id:
            raise ValueError("Matrix requires api_key (access_token) and user_id in extra")
        self._access_token = token
        self._device_id = self.config.extra.get("device_id", "CIEL")
        self._session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self._access_token}"}
        )
        async with self._session.get(f"{self._homeserver}/_matrix/client/v3/account/whoami") as resp:
            whoami = await resp.json()
            logger.info(f"Matrix connected: {whoami.get('user_id', self._user_id)}")
        self._running = True
        self._poll_task = asyncio.create_task(self._sync_loop())
        if self._on_ready:
            await self._on_ready()

    async def stop(self) -> None:
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()
            self._session = None

    async def _sync_loop(self) -> None:
        while self._running:
            try:
                params = {"since": self._sync_token, "timeout": 30000} if self._sync_token else {"timeout": 30000}
                async with self._session.get(
                    f"{self._homeserver}/_matrix/client/v3/sync", params=params
                ) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(10)
                        continue
                    data = await resp.json()
                    self._sync_token = data.get("next_batch", self._sync_token)
                    rooms = data.get("rooms", {}).get("join", {})
                    for room_id, room_data in rooms.items():
                        self._rooms.add(room_id)
                        for event in room_data.get("timeline", {}).get("events", []):
                            await self._process_event(room_id, event)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Matrix sync error")
                await asyncio.sleep(10)

    async def _process_event(self, room_id: str, event: dict[str, Any]) -> None:
        if event.get("type") != "m.room.message":
            return
        content = event.get("content", {})
        msgtype = content.get("msgtype", "m.text")
        if msgtype not in ("m.text", "m.notice"):
            return
        sender = event.get("sender", "")
        if sender == self._user_id:
            return
        body = content.get("body", "")
        msg = ChannelMessage(
            id=event.get("event_id", ""),
            channel="matrix",
            text=body,
            sender_id=sender,
            sender_name=sender.split(":")[0].lstrip("@"),
            chat_id=room_id,
            chat_name=room_id.split(":")[0].lstrip("!"),
            message_type=MessageType.TEXT,
            metadata={"event": event},
        )
        await self._dispatch(msg)

    async def send_message(self, message: ChannelMessage) -> str:
        if not self._session:
            return ""
        room_id = message.chat_id
        if not room_id.startswith("!"):
            room_id = f"!{room_id}:{self._homeserver.split('//')[1]}"
        payload = {
            "msgtype": "m.text",
            "body": message.text,
        }
        try:
            async with self._session.put(
                f"{self._homeserver}/_matrix/client/v3/rooms/{room_id}/send/m.room.message",
                json=payload,
            ) as resp:
                result = await resp.json()
                return str(result.get("event_id", ""))
        except Exception:
            logger.exception("Matrix send error")
            return ""
