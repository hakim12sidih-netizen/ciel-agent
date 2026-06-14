from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    LOCATION = "location"
    STICKER = "sticker"
    REACTION = "reaction"


@dataclass(slots=True, frozen=True)
class ChannelMessage:
    id: str
    channel: str
    text: str
    sender_id: str
    sender_name: str = ""
    chat_id: str = ""
    chat_name: str = ""
    thread_id: str = ""
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reply_to: str | None = None
    media_url: str = ""
    media_mime: str = ""
    file_size: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "channel": self.channel,
            "text": self.text,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "chat_id": self.chat_id,
            "chat_name": self.chat_name,
            "thread_id": self.thread_id,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "reply_to": self.reply_to,
            "media_url": self.media_url,
            "media_mime": self.media_mime,
            "file_size": self.file_size,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class ChannelConfig:
    channel: str
    enabled: bool = True
    webhook_url: str = ""
    webhook_secret: str = ""
    api_key: str = ""
    api_secret: str = ""
    bot_token: str = ""
    phone_number: str = ""
    server_url: str = ""
    polling_interval: float = 1.0
    max_retries: int = 3
    extra: dict[str, Any] = field(default_factory=dict)


class ChannelAdapter(ABC):
    def __init__(self, config: ChannelConfig) -> None:
        self.config = config
        self._running = False
        self._handlers: list[Callable[[ChannelMessage], Any]] = []
        self._on_ready: Callable[[], Any] | None = None

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def send_message(self, message: ChannelMessage) -> str: ...

    async def send_text(
        self, chat_id: str, text: str, thread_id: str = "", reply_to: str = ""
    ) -> str:
        msg = ChannelMessage(
            id="",
            channel=self.config.channel,
            text=text,
            sender_id="ciel",
            sender_name="CIEL",
            chat_id=chat_id,
            thread_id=thread_id,
            reply_to=reply_to or None,
        )
        return await self.send_message(msg)

    def on_message(self, handler: Callable[[ChannelMessage], Any]) -> None:
        self._handlers.append(handler)

    def set_on_ready(self, handler: Callable[[], Any]) -> None:
        self._on_ready = handler

    async def _dispatch(self, message: ChannelMessage) -> None:
        import asyncio
        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception:
                import logging
                logging.getLogger(__name__).exception(f"Handler failed for {message.id}")

    def is_running(self) -> bool:
        return self._running
