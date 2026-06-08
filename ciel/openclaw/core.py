from __future__ import annotations

from typing import Any

from ciel.openclaw.gateway import GatewayServer
from ciel.openclaw.skills import SkillRegistry, SkillMetadata


class OpenClawEngine:
    """OpenClaw — canaux de communication, gateway, registre de skills."""

    def __init__(self):
        self.gateway = GatewayServer()
        self.skills = SkillRegistry()
        self._messages_routed = 0
        self._skills_executed = 0
        self._skill_handlers: dict[str, Any] = {}

    def register_channel(self, name: str, adapter: Any) -> None:
        self.gateway.register_channel(name, adapter)

    def add_route(self, path: str, channel: str = "",
                  method: str = "POST", secret: str = "") -> None:
        self.gateway.add_webhook_route(path, channel, secret, method)

    def register_skill(self, name: str, handler: Any,
                       description: str = "", version: str = "1.0.0") -> None:
        meta = SkillMetadata(name=name, description=description, version=version)
        self.skills._skills[name] = meta
        self._skill_handlers[name] = handler

    def execute_skill(self, skill_name: str, context: dict[str, Any] | None = None) -> Any:
        self._skills_executed += 1
        handler = self._skill_handlers.get(skill_name)
        if handler is None:
            return {"error": f"no handler for '{skill_name}'"}
        return handler(context or {})

    def get_stats(self) -> dict[str, Any]:
        return {
            "routes": len(self.gateway._routes),
            "channels": list(self.gateway._channels.keys()),
            "skills_registered": len(self._skill_handlers),
            "messages_routed": self._messages_routed,
            "skills_executed": self._skills_executed,
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "execute":
            result = self.execute_skill(
                str(data.get("skill", "")),
                data.get("context"),
            )
            return {"success": True, "action": "execute", "result": result}

        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
