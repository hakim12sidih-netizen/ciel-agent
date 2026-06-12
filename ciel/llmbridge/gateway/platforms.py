from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Any

import aiohttp

from ciel.llmbridge.gateway.base import GatewayConfig, Message, MessageDirection, PlatformAdapter

logger = logging.getLogger(__name__)


class TelegramAdapter(PlatformAdapter):
    """Telegram Bot API adapter (long polling)."""

    def __init__(self, config: GatewayConfig) -> None:
        super().__init__(config)
        self._api_base: str = ""
        self._offset: int = 0
        self._session: aiohttp.ClientSession | None = None
        self._poll_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        token = self.config.bot_token or self.config.api_key
        if not token:
            raise ValueError("Telegram bot token required")
        self._api_base = f"https://api.telegram.org/bot{token}"
        self._session = aiohttp.ClientSession()
        me = await self._api_call("getMe")
        logger.info(f"Telegram bot connected: {me.get('result', {}).get('username', 'unknown')}")
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

    async def _api_call(self, method: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._session:
            return {}
        url = f"{self._api_base}/{method}"
        try:
            async with self._session.post(url, json=data or {}) as resp:
                result = await resp.json()
                if not result.get("ok"):
                    logger.warning(f"Telegram API error {method}: {result}")
                return result
        except Exception:
            logger.exception(f"Telegram API call failed: {method}")
            return {}

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                result = await self._api_call("getUpdates", {
                    "offset": self._offset + 1,
                    "timeout": 30,
                    "allowed_updates": ["message", "callback_query"],
                })
                for update in result.get("result", []):
                    self._offset = update.get("update_id", self._offset)
                    await self._process_update(update)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Telegram poll error")
                await asyncio.sleep(5)

    async def _process_update(self, update: dict[str, Any]) -> None:
        msg_data = update.get("message") or update.get("callback_query", {}).get("message", {})
        if not msg_data:
            return
        chat = msg_data.get("chat", {})
        from_user = msg_data.get("from", {})
        text = msg_data.get("text", "") or update.get("callback_query", {}).get("data", "")
        message = Message(
            id=str(msg_data.get("message_id", 0)),
            platform="telegram",
            direction=MessageDirection.INCOMING,
            text=text,
            sender_id=str(from_user.get("id", "")),
            sender_name=from_user.get("first_name", ""),
            chat_id=str(chat.get("id", "")),
            chat_name=chat.get("title", "") or chat.get("type", ""),
            thread_id=str(msg_data.get("message_thread_id", "")),
            reply_to=str(msg_data.get("reply_to_message", {}).get("message_id", "")) or None,
            metadata={"update": update},
        )
        await self._dispatch(message)

    async def send_message(self, message: Message) -> str:
        data: dict[str, Any] = {
            "chat_id": message.chat_id,
            "text": message.text,
            "parse_mode": "HTML",
        }
        if message.reply_to:
            data["reply_to_message_id"] = int(message.reply_to)
        if message.thread_id:
            data["message_thread_id"] = int(message.thread_id)
        result = await self._api_call("sendMessage", data)
        return str(result.get("result", {}).get("message_id", ""))


class DiscordAdapter(PlatformAdapter):
    """Discord Bot API adapter."""

    def __init__(self, config: GatewayConfig) -> None:
        super().__init__(config)
        self._session: aiohttp.ClientSession | None = None
        self._api_base: str = "https://discord.com/api/v10"
        self._ws_url: str = ""
        self._heartbeat_interval: float = 30.0
        self._ws_task: asyncio.Task[None] | None = None
        self._seq: int | None = None
        self._session_id: str = ""

    async def start(self) -> None:
        token = self.config.bot_token or self.config.api_key
        if not token:
            raise ValueError("Discord bot token required")
        self._session = aiohttp.ClientSession(
            headers={"Authorization": f"Bot {token}", "Content-Type": "application/json"}
        )
        self._running = True
        self._ws_task = asyncio.create_task(self._ws_loop())
        if self._on_ready:
            await self._on_ready()

    async def stop(self) -> None:
        self._running = False
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()
            self._session = None

    async def _ws_loop(self) -> None:
        await asyncio.sleep(0.5)
        logger.info("Discord adapter started (polling mode)")

    async def _api_call(self, method: str, path: str, data: dict | None = None) -> dict:
        if not self._session:
            return {}
        url = f"{self._api_base}{path}"
        try:
            async with self._session.request(method, url, json=data) as resp:
                if resp.status == 429:
                    retry = float(resp.headers.get("Retry-After", 5))
                    await asyncio.sleep(retry)
                    return await self._api_call(method, path, data)
                return await resp.json()
        except Exception:
            logger.exception(f"Discord API error {method} {path}")
            return {}

    async def send_message(self, message: Message) -> str:
        data: dict[str, Any] = {"content": message.text}
        result = await self._api_call("POST", f"/channels/{message.chat_id}/messages", data)
        return str(result.get("id", ""))


class SlackAdapter(PlatformAdapter):
    """Slack Web API adapter."""

    def __init__(self, config: GatewayConfig) -> None:
        super().__init__(config)
        self._session: aiohttp.ClientSession | None = None
        self._api_base: str = "https://slack.com/api"

    async def start(self) -> None:
        token = self.config.api_key or self.config.bot_token
        if not token:
            raise ValueError("Slack bot token required")
        self._session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        result = await self._api_call("GET", "/auth.test")
        logger.info(f"Slack connected: {result.get('user', 'unknown')}")
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
                if not result.get("ok"):
                    logger.warning(f"Slack API error: {result.get('error', 'unknown')}")
                return result
        except Exception:
            logger.exception(f"Slack API error {method} {path}")
            return {}

    async def send_message(self, message: Message) -> str:
        data: dict[str, Any] = {
            "channel": message.chat_id,
            "text": message.text,
        }
        if message.thread_id:
            data["thread_ts"] = message.thread_id
        result = await self._api_call("POST", "/chat.postMessage", data)
        return str(result.get("ts", ""))
