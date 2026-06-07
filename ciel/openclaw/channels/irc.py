from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from ciel.openclaw.channels.base import ChannelAdapter, ChannelConfig, ChannelMessage, MessageType

logger = logging.getLogger(__name__)


class IRCAdapter(ChannelAdapter):
    """Internet Relay Chat adapter — raw socket protocol."""

    def __init__(self, config: ChannelConfig) -> None:
        super().__init__(config)
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._server: str = config.server_url or "irc.libera.chat"
        self._port: int = config.extra.get("port", 6667)
        self._nick: str = config.extra.get("nick", "CIELBot")
        self._user: str = config.extra.get("user", "ciel")
        self._realname: str = config.extra.get("realname", "CIEL v∞.3")
        self._password: str = config.api_key
        self._channels: list[str] = config.extra.get("channels", [])
        self._read_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        try:
            self._reader, self._writer = await asyncio.open_connection(self._server, self._port)
        except Exception:
            logger.exception(f"IRC connection failed to {self._server}:{self._port}")
            return
        self._send_raw(f"NICK {self._nick}")
        self._send_raw(f"USER {self._user} 0 * :{self._realname}")
        if self._password:
            self._send_raw(f"PASS {self._password}")
        self._running = True
        self._read_task = asyncio.create_task(self._read_loop())
        for ch in self._channels:
            self._send_raw(f"JOIN {ch}")
        if self._on_ready:
            await self._on_ready()

    async def stop(self) -> None:
        self._running = False
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        for ch in self._channels:
            self._send_raw(f"PART {ch}")
        self._send_raw("QUIT :CIEL shutting down")
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass

    def _send_raw(self, line: str) -> None:
        if self._writer:
            try:
                self._writer.write(f"{line}\r\n".encode("utf-8", errors="replace"))
            except Exception:
                pass

    async def _read_loop(self) -> None:
        while self._running and self._reader:
            try:
                line = await asyncio.wait_for(self._reader.readline(), timeout=300)
            except asyncio.TimeoutError:
                self._send_raw("PING :ciel-keepalive")
                continue
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("IRC read error")
                await asyncio.sleep(5)
                continue
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace").strip()
            if not decoded:
                continue
            if decoded.startswith("PING"):
                self._send_raw(f"PONG {decoded[5:]}")
                continue
            match = re.match(r":(\S+)!~?\S+ PRIVMSG (\S+) :(.+)", decoded)
            if match:
                sender, target, text = match.groups()
                if target == self._nick:
                    chat_id = sender
                else:
                    chat_id = target
                msg = ChannelMessage(
                    id=decoded.split()[2] if len(decoded.split()) > 2 else decoded,
                    channel="irc",
                    text=text,
                    sender_id=sender,
                    sender_name=sender.split("!")[0],
                    chat_id=chat_id,
                    chat_name=target,
                    message_type=MessageType.TEXT,
                    metadata={"raw": decoded},
                )
                await self._dispatch(msg)

    async def send_message(self, message: ChannelMessage) -> str:
        target = message.chat_id
        lines = message.text.split("\n")
        for line in lines:
            self._send_raw(f"PRIVMSG {target} :{line[:400]}")
        await asyncio.sleep(0.1)
        return message.id or "irc_sent"
