"""
CIEL v1.0 — Channels : système de messagerie multi-plateforme.

Composant CIEL natif — canaux de messagerie.
Architecture d'adaptateurs :
  - BaseChannel : classe de base pour tous les canaux
  - ChannelManager : orchestre les connexions
  - Adaptateurs : Telegram, Discord, WhatsApp, etc.
"""
from __future__ import annotations

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class Message:
    id: str
    channel: str
    content: str
    role: str  # "user" | "assistant" | "system"
    sender: str = "unknown"
    chat_id: str = "default"
    thread_id: str | None = None
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "channel": self.channel, "content": self.content,
            "role": self.role, "sender": self.sender, "chat_id": self.chat_id,
            "timestamp": self.timestamp,
        }


class BaseChannel(ABC):
    """Classe de base pour les adaptateurs de canal."""

    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self._handlers: list[Callable[[Message], None]] = []
        self._running = False

    @abstractmethod
    def connect(self) -> bool:
        ...

    @abstractmethod
    def disconnect(self) -> bool:
        ...

    @abstractmethod
    def send(self, message: Message) -> bool:
        ...

    def on_message(self, handler: Callable[[Message], None]) -> None:
        self._handlers.append(handler)

    def _receive(self, message: Message) -> None:
        for handler in self._handlers:
            try:
                handler(message)
            except Exception as e:
                print(f"[Channel {self.channel_id}] Handler error: {e}")

    @property
    def is_connected(self) -> bool:
        return self._running


class ChannelManager:
    """Gestionnaire de canaux CIEL.

    Maintient la liste des canaux actifs et route les messages.
    """

    def __init__(self):
        self.channels: dict[str, BaseChannel] = {}
        self.network = LeaderNetwork()

    def register(self, channel: BaseChannel) -> None:
        self.channels[channel.channel_id] = channel
        channel.on_message(lambda msg: self._route(msg))

    def connect_all(self) -> dict[str, bool]:
        results = {}
        for cid, channel in self.channels.items():
            results[cid] = channel.connect()
        self.network.emit("channels.connected", results)
        return results

    def disconnect_all(self) -> None:
        for channel in self.channels.values():
            channel.disconnect()

    def send(self, channel_id: str, content: str, role: str = "assistant") -> bool:
        channel = self.channels.get(channel_id)
        if not channel:
            return False
        msg = Message(
            id=f"MSG-{uuid.uuid4().hex[:12]}",
            channel=channel_id, content=content, role=role,
        )
        result = channel.send(msg)
        self.network.emit("channel.sent", {"channel": channel_id})
        return result

    def broadcast(self, content: str, role: str = "assistant") -> dict[str, bool]:
        results = {}
        for cid, channel in self.channels.items():
            msg = Message(
                id=f"MSG-{uuid.uuid4().hex[:12]}",
                channel=cid, content=content, role=role,
            )
            results[cid] = channel.send(msg)
        return results

    def _route(self, message: Message) -> None:
        self.network.emit("channel.message", {
            "channel": message.channel,
            "content_preview": message.content[:50],
        })

    def list_channels(self) -> list[dict]:
        return [
            {"id": cid, "connected": ch.is_connected}
            for cid, ch in self.channels.items()
        ]


class TerminalChannel(BaseChannel):
    """Canal terminal (stdin/stdout) — toujours disponible."""

    def __init__(self):
        super().__init__("terminal")

    def connect(self) -> bool:
        self._running = True
        return True

    def disconnect(self) -> bool:
        self._running = False
        return True

    def send(self, message: Message) -> bool:
        print(f"\n[{message.role.upper()}] {message.content}")
        return True
