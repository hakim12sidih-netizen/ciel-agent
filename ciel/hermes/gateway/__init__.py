"""
CIEL v∞.3 — Hermes : Pont Multi-Plateforme (Gateway).

Inspiré du module gateway/ de Hermes Agent.
Délivre des messages entre CIEL et les plateformes externes.
"""
from __future__ import annotations

from ciel.hermes.gateway.base import (
    PlatformAdapter,
    Message,
    MessageDirection,
    GatewayConfig,
)
from ciel.hermes.gateway.telegram import TelegramAdapter
from ciel.hermes.gateway.discord import DiscordAdapter
from ciel.hermes.gateway.slack import SlackAdapter

__all__ = [
    "PlatformAdapter", "Message", "MessageDirection", "GatewayConfig",
    "TelegramAdapter", "DiscordAdapter", "SlackAdapter",
]
