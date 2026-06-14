"""
HDLM — Pont de communication multicanal.
Configuration centralisée pour les connexions aux channels
(Telegram, Discord, Slack) et le changement de cerveau CIEL.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from ciel.llmbridge.gateway.base import GatewayConfig
from ciel.llmbridge.gateway import TelegramAdapter, DiscordAdapter, SlackAdapter


# ── Paramètres de connexion aux channels ──

@dataclass
class ChannelParams:
    """Paramètres de connexion pour tous les channels supportés."""
    telegram_token: str = ""
    telegram_enabled: bool = True
    telegram_polling_interval: float = 1.0

    discord_token: str = ""
    discord_enabled: bool = True

    slack_token: str = ""
    slack_enabled: bool = True

    @classmethod
    def from_env(cls) -> ChannelParams:
        return cls(
            telegram_token=os.environ.get("CIEL_TELEGRAM_TOKEN", ""),
            telegram_enabled=os.environ.get("CIEL_TELEGRAM_ENABLED", "1") == "1",
            telegram_polling_interval=float(os.environ.get("CIEL_TELEGRAM_POLLING", "1.0")),
            discord_token=os.environ.get("CIEL_DISCORD_TOKEN", ""),
            discord_enabled=os.environ.get("CIEL_DISCORD_ENABLED", "1") == "1",
            slack_token=os.environ.get("CIEL_SLACK_TOKEN", ""),
            slack_enabled=os.environ.get("CIEL_SLACK_ENABLED", "1") == "1",
        )

    def to_dict(self) -> dict:
        return {
            "telegram": {"token": bool(self.telegram_token), "enabled": self.telegram_enabled},
            "discord": {"token": bool(self.discord_token), "enabled": self.discord_enabled},
            "slack": {"token": bool(self.slack_token), "enabled": self.slack_enabled},
        }


# ── Paramètres de changement de cerveau ──

@dataclass
class BrainSwitchParams:
    """Paramètres pour le changement de cerveau / provider LLM."""
    default_provider: str = "ollama"
    default_model: str = "phi3"
    temperature: float = 0.7
    max_tokens: int = 4096
    auto_switch: bool = True          # switch auto si le provider actif tombe
    fallback_provider: str = "ollama"
    fallback_model: str = "phi3"

    @classmethod
    def from_env(cls) -> BrainSwitchParams:
        return cls(
            default_provider=os.environ.get("CIEL_LLM_PROVIDER", "ollama"),
            default_model=os.environ.get("CIEL_LLM_MODEL", "phi3"),
            temperature=float(os.environ.get("CIEL_LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("CIEL_LLM_MAX_TOKENS", "4096")),
            auto_switch=os.environ.get("CIEL_LLM_AUTO_SWITCH", "1") == "1",
            fallback_provider=os.environ.get("CIEL_LLM_FALLBACK_PROVIDER", "ollama"),
            fallback_model=os.environ.get("CIEL_LLM_FALLBACK_MODEL", "phi3"),
        )

    def to_dict(self) -> dict:
        return {
            "provider": self.default_provider,
            "model": self.default_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "auto_switch": self.auto_switch,
            "fallback": {"provider": self.fallback_provider, "model": self.fallback_model},
        }


# ── HDLM : Initialisation des channels ──

def init_channels(params: ChannelParams | None = None) -> dict[str, Any]:
    """Initialise les adaptateurs channel selon les paramètres.
    Retourne {nom_adapter: adapter_instance}."""
    p = params or ChannelParams.from_env()
    adapters: dict[str, Any] = {}

    if p.telegram_token and p.telegram_enabled:
        cfg = GatewayConfig(
            platform="telegram",
            bot_token=p.telegram_token,
            polling_interval=p.telegram_polling_interval,
        )
        adapters["telegram"] = TelegramAdapter(cfg)

    if p.discord_token and p.discord_enabled:
        cfg = GatewayConfig(
            platform="discord",
            bot_token=p.discord_token,
        )
        adapters["discord"] = DiscordAdapter(cfg)

    if p.slack_token and p.slack_enabled:
        cfg = GatewayConfig(
            platform="slack",
            api_key=p.slack_token,
        )
        adapters["slack"] = SlackAdapter(cfg)

    return adapters


def init_llm(params: BrainSwitchParams | None = None):
    """Initialise le LLMBridgeEngine avec les paramètres de cerveau."""
    from ciel.llmbridge.core import LLMBridgeEngine
    p = params or BrainSwitchParams.from_env()
    engine = LLMBridgeEngine()
    engine.set_active_provider(p.default_provider, p.default_model)
    return engine
