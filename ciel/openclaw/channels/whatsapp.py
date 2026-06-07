from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Any

import aiohttp

from ciel.openclaw.channels.base import ChannelAdapter, ChannelConfig, ChannelMessage, MessageType

logger = logging.getLogger(__name__)


class WhatsAppAdapter(ChannelAdapter):
    """WhatsApp Cloud API adapter via Meta's Graph API."""

    def __init__(self, config: ChannelConfig) -> None:
        super().__init__(config)
        self._session: aiohttp.ClientSession | None = None
        self._api_base: str = "https://graph.facebook.com/v18.0"
        self._phone_number_id: str = ""
        self._webhook_token: str = config.webhook_secret or ""

    async def start(self) -> None:
        token = self.config.api_key
        if not token:
            raise ValueError("WhatsApp API key (token) required")
        self._phone_number_id = self.config.extra.get("phone_number_id", "")
        if not self._phone_number_id:
            raise ValueError("WhatsApp phone_number_id required in extra")
        self._session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        logger.info(f"WhatsApp adapter ready (phone_id={self._phone_number_id})")
        self._running = True
        if self._on_ready:
            await self._on_ready()

    async def stop(self) -> None:
        self._running = False
        if self._session:
            await self._session.close()
            self._session = None

    async def _api_call(self, method: str, path: str, data: dict | None = None) -> dict:
        if not self._session:
            return {}
        url = f"{self._api_base}{path}"
        try:
            async with self._session.request(method, url, json=data) as resp:
                result = await resp.json()
                if "error" in result:
                    logger.warning(f"WA API error: {result['error']}")
                return result
        except Exception:
            logger.exception(f"WA API error {method} {path}")
            return {}

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str | None:
        if mode == "subscribe" and token == self._webhook_token:
            return challenge
        return None

    async def process_webhook(self, body: dict[str, Any]) -> list[ChannelMessage]:
        messages: list[ChannelMessage] = []
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg_data in value.get("messages", []):
                    msg_type = msg_data.get("type", "text")
                    text = ""
                    media_url = ""
                    media_mime = ""
                    file_size = 0
                    if msg_type == "text":
                        text = msg_data.get("text", {}).get("body", "")
                    elif msg_type in ("image", "audio", "video", "document"):
                        media = msg_data.get(msg_type, {})
                        text = media.get("caption", "")
                        media_url = media.get("url", "")
                        media_mime = media.get("mime_type", "")
                        file_size = media.get("file_size", 0)
                    msg = ChannelMessage(
                        id=msg_data.get("id", ""),
                        channel="whatsapp",
                        text=text,
                        sender_id=msg_data.get("from", ""),
                        chat_id=value.get("metadata", {}).get("phone_number_id", ""),
                        message_type=MessageType(msg_type) if msg_type in {e.value for e in MessageType} else MessageType.TEXT,
                        media_url=media_url,
                        media_mime=media_mime,
                        file_size=file_size,
                        metadata={"entry": entry.get("id", "")},
                    )
                    messages.append(msg)
        for msg in messages:
            await self._dispatch(msg)
        return messages

    async def send_message(self, message: ChannelMessage) -> str:
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": message.chat_id,
            "type": "text",
            "text": {"body": message.text},
        }
        path = f"/{self._phone_number_id}/messages"
        result = await self._api_call("POST", path, payload)
        msg_id = result.get("messages", [{}])[0].get("id", "")
        return str(msg_id) if msg_id else ""
