"""LLMBridgeEngine — Pont multi-fournisseur avec hot-swap sans fil."""
from __future__ import annotations

import os
from typing import Any

from ciel.llmbridge.gateway.base import PlatformAdapter, Message
from ciel.llmbridge.hermes_state import LLMState
from ciel.llmbridge.providers import (
    ProviderBase, LLMResponse, Message as LLMMessage,
    OpenAIProvider, AnthropicProvider, GeminiProvider,
)
from ciel.providers import get_registry, ProviderProfile

# Provider factory : profile → implémentation concrète
_PROVIDER_CLASSES = {
    "chat_completions": OpenAIProvider,
    "anthropic_messages": AnthropicProvider,
    "gemini": GeminiProvider,
}


def _build_provider(
    profile: ProviderProfile, model: str,
    config: dict | None = None,
) -> ProviderBase | None:
    cls = _PROVIDER_CLASSES.get(profile.api_mode)
    if cls is None:
        return None

    # Clé API : config > env var
    api_key = ""
    if config:
        api_key = config.get("api_keys", {}).get(profile.name, "")
    if not api_key and profile.env_var:
        api_key = os.environ.get(profile.env_var, "")

    # URL : normalisation selon le mode API
    base_url = profile.base_url
    if profile.api_mode == "chat_completions":
        if base_url and not base_url.rstrip("/").endswith("/chat/completions"):
            base_url = base_url.rstrip("/") + "/chat/completions"

    kwargs: dict = {"model": model, "api_key": api_key, "base_url": base_url}
    if profile.api_mode == "chat_completions":
        kwargs["provider_name"] = profile.name
    return cls(**kwargs)


class LLMBridgeEngine:
    """Pont multi-plateforme avec gestion centralisée des providers.
    Hot-swap : changer de modèle sans recréer l'objet."""

    def __init__(self):
        self.state = LLMState(db_path=":memory:")
        self._providers: dict[str, ProviderBase] = {}
        self._adapters: dict[str, PlatformAdapter] = {}
        self._active_provider_name: str = ""
        self._active_model: str = ""
        self._messages_processed = 0
        self._registry = get_registry()
        self._config: dict | None = None

    def configure(self, llm_config: dict | None) -> None:
        self._config = llm_config or {}
        api_keys = self._config.get("api_keys", {})
        self._registry.configure(api_keys=api_keys)

    # ── Gestion des providers ──────────────────────────────

    def register_provider(self, name: str, provider: ProviderBase) -> None:
        self._providers[name] = provider

    def list_available_providers(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._registry.list(available_only=True)]

    def list_all_providers(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self._registry.list()]

    # ── Hot-swap : changer de modèle SANS recréation ───────

    def set_active_provider(self, provider_name: str, model: str = "") -> dict:
        profile = self._registry.get(provider_name)
        if profile is None:
            return {"ok": False, "error": f"Provider inconnu: {provider_name}"}

        if not model:
            model = profile.default_model
        if not model and profile.models:
            model = profile.models[0]

        provider = _build_provider(profile, model, config=self._config)
        if provider is None:
            return {"ok": False, "error": f"API mode non supporte: {profile.api_mode}"}

        # Hot-swap : remplacer sans recréer l'engine
        self._providers[provider_name] = provider
        self._active_provider_name = provider_name
        self._active_model = model
        return {
            "ok": True,
            "provider": provider_name,
            "model": model,
            "api_mode": profile.api_mode,
        }

    def get_active_provider(self) -> ProviderBase | None:
        if self._active_provider_name and self._active_provider_name in self._providers:
            return self._providers[self._active_provider_name]
        if self._providers:
            name = next(iter(self._providers))
            self._active_provider_name = name
            return self._providers[name]
        # Auto-init avec le premier provider disponible
        profile = self._registry.get_default()
        if profile:
            self.set_active_provider(profile.name)
            return self._providers.get(profile.name)
        return None

    def switch_model(self, model: str) -> dict:
        """Change de modèle sur le provider actif (hot-swap sans fil).
        Cherche d'abord sur le provider actif, puis dans tout le registre.
        Accepte tout modèle — même non listé — pour les providers locaux."""
        cur = self._active_provider_name
        if cur:
            return self.set_active_provider(cur, model)
        profile = self._registry.get_model_provider(model)
        if profile is None:
            profile = self._registry.get_default()
        if profile is None:
            return {"ok": False, "error": f"Aucun provider trouve pour le modele: {model}"}
        return self.set_active_provider(profile.name, model)

    def active_info(self) -> dict:
        return {
            "provider": self._active_provider_name,
            "model": self._active_model,
        }

    # ── Appel LLM ──────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        provider = self.get_active_provider()
        if provider is None:
            raise RuntimeError("Aucun provider LLM actif. Utilise set_active_provider() d'abord.")

        llm_msgs = [LLMMessage(role=m.get("role", "user"), content=m.get("content", ""))
                     for m in messages]
        return await provider.chat_completion(llm_msgs, temperature, max_tokens)

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """Streaming chat — wrapped over chat_completion.

        Yields LLMResponse chunks. Actuellement chaque provider
        retourne une réponse complète (stream non implémenté au niveau HTTP).
        La boucle yield un unique chunk pour compatibilité async for.
        """
        provider = self.get_active_provider()
        if provider is None:
            raise RuntimeError("Aucun provider LLM actif.")
        llm_msgs = [LLMMessage(role=m.get("role", "user"), content=m.get("content", ""))
                     for m in messages]
        result = await provider.chat_completion(llm_msgs, temperature, max_tokens, stream=True)
        yield result

    # ── Sessions (état) ────────────────────────────────────

    def create_session(self, platform: str = "cli", chat_id: str = "",
                       user_id: str = "", title: str = "") -> str:
        return self.state.create_session(platform, chat_id, user_id, title)

    def send_message(self, session_id: str, content: str, role: str = "user") -> int:
        self._messages_processed += 1
        return self.state.add_message(session_id, role, content)

    def get_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return self.state.get_messages(session_id, limit)

    def list_sessions(self, platform: str = "", limit: int = 20) -> list[dict[str, Any]]:
        sessions = self.state.list_sessions(platform, limit)
        return [{
            "session_id": s.session_id,
            "platform": s.platform,
            "message_count": s.message_count,
        } for s in sessions]

    def close_session(self, session_id: str) -> None:
        self.state.close_session(session_id)

    # ── Gateway ────────────────────────────────────────────

    def register_adapter(self, name: str, adapter: PlatformAdapter) -> None:
        self._adapters[name] = adapter

    def get_stats(self) -> dict[str, Any]:
        return {
            "state": self.state.stats(),
            "providers": list(self._providers.keys()),
            "active": self.active_info(),
            "adapters": list(self._adapters.keys()),
            "messages_processed": self._messages_processed,
        }

    # ── Dispatcher (compat ascendante) ─────────────────────

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "set_provider":
            return self.set_active_provider(
                str(data.get("provider", "")),
                str(data.get("model", "")),
            )
        elif action == "switch_model":
            return self.switch_model(str(data.get("model", "")))
        elif action == "active_info":
            return {"success": True, **self.active_info()}

        elif action == "create_session":
            sid = self.create_session(
                str(data.get("platform", "cli")),
                str(data.get("chat_id", "")),
                str(data.get("user_id", "")),
                str(data.get("title", "")),
            )
            return {"success": True, "action": "create_session", "session_id": sid}

        elif action == "send":
            sid = str(data.get("session_id", ""))
            content = str(data.get("content", ""))
            role = str(data.get("role", "user"))
            msg_id = self.send_message(sid, content, role)
            return {"success": True, "action": "send", "message_id": msg_id}

        elif action == "history":
            sid = str(data.get("session_id", ""))
            msgs = self.get_history(sid, int(data.get("limit", 50)))
            return {"success": True, "action": "history", "messages": msgs}

        elif action == "sessions":
            sessions = self.list_sessions(str(data.get("platform", "")))
            return {"success": True, "action": "sessions", "sessions": sessions}

        elif action == "close":
            self.close_session(str(data.get("session_id", "")))
            return {"success": True, "action": "close"}

        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
