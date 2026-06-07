from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class MessageDirection(Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


@dataclass(slots=True, frozen=True)
class Message:
    id: str
    platform: str
    direction: MessageDirection
    text: str
    sender_id: str
    sender_name: str = ""
    chat_id: str = ""
    chat_name: str = ""
    thread_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reply_to: str | None = None
    attachments: tuple[dict[str, Any], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "platform": self.platform,
            "direction": self.direction.value,
            "text": self.text,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "chat_id": self.chat_id,
            "chat_name": self.chat_name,
            "thread_id": self.thread_id,
            "timestamp": self.timestamp.isoformat(),
            "reply_to": self.reply_to,
            "attachments": list(self.attachments),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        d = dict(data)
        d["direction"] = MessageDirection(d["direction"])
        d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        d["attachments"] = tuple(d.get("attachments", []))
        return cls(**d)


@dataclass(slots=True, frozen=True)
class GatewayConfig:
    platform: str
    enabled: bool = True
    api_key: str = ""
    api_secret: str = ""
    bot_token: str = ""
    webhook_url: str = ""
    webhook_secret: str = ""
    polling_interval: float = 1.0
    max_retries: int = 3
    timeout: float = 30.0
    extra: dict[str, Any] = field(default_factory=dict)


class PlatformAdapter(ABC):
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self._running = False
        self._handlers: list[Callable[[Message], Any]] = []
        self._on_ready: Callable[[], Any] | None = None

    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...

    @abstractmethod
    async def send_message(self, message: Message) -> str:
        ...

    async def send_text(
        self, chat_id: str, text: str, thread_id: str = "", reply_to: str = ""
    ) -> str:
        msg = Message(
            id="",
            platform=self.config.platform,
            direction=MessageDirection.OUTGOING,
            text=text,
            sender_id="ciel",
            sender_name="CIEL",
            chat_id=chat_id,
            thread_id=thread_id,
            reply_to=reply_to or None,
        )
        return await self.send_message(msg)

    def on_message(self, handler: Callable[[Message], Any]) -> None:
        self._handlers.append(handler)

    def set_on_ready(self, handler: Callable[[], Any]) -> None:
        self._on_ready = handler

    async def _dispatch(self, message: Message) -> None:
        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception:
                logger.exception(f"Handler failed for message {message.id}")

    def is_running(self) -> bool:
        return self._running
