from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class InterfaceMode(Enum):
    CLI = "cli"
    TUI = "tui"
    VOICE = "voice"
    CANVAS = "canvas"
    API_SERVER = "api_server"
    ACP = "acp"


@dataclass(slots=True)
class InterfaceSession:
    mode: InterfaceMode
    session_id: str = ""
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class InterfacesEngine:
    """Moteur d'interfaces — 6 modes de communication avec l'extérieur."""

    def __init__(self) -> None:
        self._sessions: dict[str, InterfaceSession] = {}
        self._mode_availability: dict[InterfaceMode, bool] = {
            mode: True for mode in InterfaceMode
        }

    def create_session(self, mode: str, **metadata: Any) -> dict[str, Any]:
        try:
            m = InterfaceMode(mode)
        except ValueError:
            return {"success": False, "error": f"unknown mode '{mode}'"}
        sid = f"iface_{len(self._sessions)}_{random.randint(1000, 9999)}"
        self._sessions[sid] = InterfaceSession(mode=m, session_id=sid, metadata=metadata)
        return {"success": True, "session_id": sid, "mode": mode}

    def close_session(self, session_id: str) -> dict[str, Any]:
        sess = self._sessions.pop(session_id, None)
        if not sess:
            return {"success": False, "error": f"session '{session_id}' not found"}
        return {"success": True, "session_id": session_id}

    def get_stats(self) -> dict[str, Any]:
        return {
            "active_sessions": len(self._sessions),
            "modes": {m.value: avail for m, avail in self._mode_availability.items()},
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "create_session":
            return self.create_session(
                str(data.get("mode", "cli")),
                **{k: v for k, v in data.items() if k != "mode"},
            )

        elif action == "close_session":
            return self.close_session(str(data.get("session_id", "")))

        elif action == "stats":
            return {"success": True, "action": "stats", **self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
