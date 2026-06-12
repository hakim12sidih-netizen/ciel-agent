"""
CIEL v∞.3 — LLMBridge : Pont Multi-Plateforme (Gateway).

Inspiré du module gateway/ de LLMBridge Agent.
Délivre des messages entre CIEL et les plateformes externes.
"""
from __future__ import annotations

from ciel.llmbridge.gateway.base import (
    PlatformAdapter,
    Message,
    MessageDirection,
    GatewayConfig,
)
from ciel.llmbridge.gateway.telegram import TelegramAdapter
from ciel.llmbridge.gateway.discord import DiscordAdapter
from ciel.llmbridge.gateway.slack import SlackAdapter

__all__ = [
    "PlatformAdapter", "Message", "MessageDirection", "GatewayConfig",
    "TelegramAdapter", "DiscordAdapter", "SlackAdapter",
]
