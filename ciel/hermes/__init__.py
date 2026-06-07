"""
CIEL v∞.3 — Hermes : Intégration de l'Agent Hermes.

Pont multi-plateforme, gestion d'état, fournisseurs LLM, et système de
compétences adaptés de Hermes Agent pour CIEL.
"""
from __future__ import annotations

from ciel.hermes.gateway import (
    PlatformAdapter, Message, MessageDirection, GatewayConfig,
    TelegramAdapter, DiscordAdapter, SlackAdapter,
)
from ciel.hermes.hermes_state import HermesState, SessionRecord
from ciel.hermes.providers import ProviderBase, LLMResponse

__all__ = [
    "PlatformAdapter", "Message", "MessageDirection", "GatewayConfig",
    "TelegramAdapter", "DiscordAdapter", "SlackAdapter",
    "HermesState", "SessionRecord",
    "ProviderBase", "LLMResponse",
]
