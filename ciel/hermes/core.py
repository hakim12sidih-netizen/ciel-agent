from __future__ import annotations

from typing import Any

from ciel.hermes.gateway.base import PlatformAdapter, Message
from ciel.hermes.hermes_state import HermesState
from ciel.hermes.providers import ProviderBase, LLMResponse, Message as LLMMessage


class HermesEngine:
    """Pont multi-plateforme — Hermes : agents, état, fournisseurs LLM, gateway."""

    def __init__(self):
        self.state = HermesState(db_path=":memory:")
        self._providers: dict[str, ProviderBase] = {}
        self._adapters: dict[str, PlatformAdapter] = {}
        self._messages_processed = 0

    def register_provider(self, name: str, provider: ProviderBase) -> None:
        self._providers[name] = provider

    def register_adapter(self, name: str, adapter: PlatformAdapter) -> None:
        self._adapters[name] = adapter

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

    def get_stats(self) -> dict[str, Any]:
        return {
            "state": self.state.stats(),
            "providers": list(self._providers.keys()),
            "adapters": list(self._adapters.keys()),
            "messages_processed": self._messages_processed,
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "create_session":
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
