from __future__ import annotations

from typing import Any

from ciel.polyglot.bridge import PolyglotBridge


class PolyglotEngine:
    """Moteur polyglot — ponts vers les binaires externes."""

    def __init__(self) -> None:
        self._bridges: dict[str, PolyglotBridge] = {}

    def register_bridge(self, name: str, bridge: PolyglotBridge) -> None:
        self._bridges[name] = bridge

    def call(self, bridge_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        bridge = self._bridges.get(bridge_name)
        if not bridge:
            return {"success": False, "error": f"bridge '{bridge_name}' not registered"}
        try:
            result = bridge.call(payload)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_stats(self) -> dict[str, Any]:
        return {
            "bridges": list(self._bridges.keys()),
            "bridge_count": len(self._bridges),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "call":
            return self.call(
                str(data.get("bridge", "")),
                data.get("payload", {}),
            )

        elif action == "stats":
            return {"success": True, "action": "stats", **self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
