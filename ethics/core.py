from __future__ import annotations

from typing import Any

from ciel.ethics.filter import EthicsFilter, new_action
from ciel.ethics.transparency import global_log
from ciel.ethics.reversibility import SnapshotStore
from ciel.core.identity import demo_identity


class EthicsEngine:
    """Moteur éthique unifié — filter, transparence, réversibilité."""

    def __init__(self) -> None:
        self.filter = EthicsFilter()
        self.transparency = global_log()
        self.snapshots = SnapshotStore.__new__(SnapshotStore)
        self._identity = demo_identity()

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "validate":
            act = new_action(
                category=str(data.get("category", "unknown")),
                target=str(data.get("target", "")),
                risk=float(data.get("risk", 0.0)),
                reversible=bool(data.get("reversible", True)),
            )
            try:
                self.filter.validate(act)
                return {"success": True, "action": "validate", "valid": True}
            except Exception as e:
                return {"success": True, "action": "validate", "valid": False, "error": str(e)}

        elif action == "certify":
            cert = self.transparency.certify(
                action_id=str(data.get("action_id", "")),
                action_category=str(data.get("category", "unknown")),
                axioms_consulted=data.get("axioms", ["α"]),
                identity=self._identity,
            )
            return {"success": True, "action": "certify", "cert_id": cert.id}

        elif action == "stats":
            return {
                "success": True, "action": "stats",
                "filter": self.filter.stats(),
                "transparency": self.transparency.stats(),
            }

        return {"success": False, "error": f"unknown action '{action}'"}
