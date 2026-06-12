from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from ciel.messaging.channels.base import ChannelAdapter, ChannelConfig, ChannelMessage, MessageType

logger = logging.getLogger(__name__)


class SignalAdapter(ChannelAdapter):
    """Signal Messenger adapter via signal-cli REST API."""

    def __init__(self, config: ChannelConfig) -> None:
        super().__init__(config)
        self._session: aiohttp.ClientSession | None = None
        self._api_base: str = config.server_url or "http://localhost:8080"
        self._number: str = config.phone_number
        self._poll_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if not self._number:
            raise ValueError("Signal phone number required")
        self._session = aiohttp.ClientSession()
        try:
            async with self._session.get(f"{self._api_base}/v1/about") as resp:
                about = await resp.json()
                logger.info(f"Signal bridge connected: {about}")
        except Exception:
            logger.warning("Signal bridge not reachable, will retry")
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
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

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                async with self._session.get(
                    f"{self._api_base}/v1/receive/{self._number}", timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data: list[dict] = await resp.json()
                        for envelope in data:
                            await self._process_envelope(envelope)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

    async def _process_envelope(self, envelope: dict[str, Any]) -> None:
        sync = envelope.get("syncMessage", {})
        sent = sync.get("sentMessage", {})
        data_msg = sent or envelope.get("dataMessage", {})
        if not data_msg:
            return
        text = data_msg.get("message", "")
        attachments = data_msg.get("attachments", [])
        source = sent.get("destination", "") or envelope.get("source", "")
        msg = ChannelMessage(
            id=data_msg.get("timestamp", str(envelope.get("timestamp", ""))),
            channel="signal",
            text=text,
            sender_id=source,
            sender_name=data_msg.get("profileName", source),
            chat_id=sent.get("destination", source),
            message_type=MessageType.TEXT,
            metadata={"envelope": envelope},
        )
        await self._dispatch(msg)

    async def send_message(self, message: ChannelMessage) -> str:
        if not self._session:
            return ""
        payload: dict[str, Any] = {
            "message": message.text,
            "number": self._number,
            "recipients": [message.chat_id],
        }
        try:
            async with self._session.post(f"{self._api_base}/v2/send", json=payload) as resp:
                result = await resp.json()
                return str(result.get("timestamp", ""))
        except Exception:
            logger.exception("Signal send error")
            return ""
