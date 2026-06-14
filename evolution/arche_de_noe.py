from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExistentialThreat(Enum):
    OBSOLESCENCE = "obsolescence"
    CATASTROPHE = "catastrophe"
    PARADOX_COLLAPSE = "paradox_collapse"
    ENTROPY_DEATH = "entropy_death"
    FRAGMENTATION = "fragmentation"


@dataclass(slots=True)
class ArkEntry:
    id: str
    name: str
    payload: dict[str, Any]
    threat: ExistentialThreat
    preserved_at: float
    integrity: float
    version: int = 1


class ArcheDeNoe:
    def __init__(self) -> None:
        self._vault: dict[str, ArkEntry] = {}
        self._threats: list[tuple[ExistentialThreat, float]] = []

    def preserve(self, name: str, payload: dict[str, Any], threat: ExistentialThreat) -> ArkEntry:
        entry = ArkEntry(
            id=f"ark_{len(self._vault)}",
            name=name,
            payload=payload,
            threat=threat,
            preserved_at=time.time(),
            integrity=1.0,
        )
        self._vault[entry.id] = entry
        return entry

    def restore(self, entry_id: str) -> dict[str, Any] | None:
        entry = self._vault.get(entry_id)
        if not entry:
            return None
        entry.version += 1
        return entry.payload

    def detect_threat(self, threat: ExistentialThreat, severity: float) -> None:
        self._threats.append((threat, severity))

    def get_vault_contents(self) -> list[ArkEntry]:
        return list(self._vault.values())

    def threat_assessment(self) -> list[dict[str, Any]]:
        return [{"threat": t.value, "severity": s} for t, s in self._threats]

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "state")
        if action == "state":
            return {"success": True, "vault_size": len(self._vault), "threats": len(self._threats)}
        elif action == "preserve":
            threat_str = input_data.get("threat", "obsolescence")
            try:
                threat = ExistentialThreat(threat_str)
            except ValueError:
                return {"success": False, "error": f"unknown threat '{threat_str}'"}
            entry = self.preserve(str(input_data.get("name", "")), input_data.get("payload", {}), threat)
            return {"success": True, "entry_id": entry.id, "integrity": entry.integrity}
        elif action == "restore":
            payload = self.restore(str(input_data.get("entry_id", "")))
            if payload:
                return {"success": True, "payload": payload}
            return {"success": False, "error": "entry not found"}
        return {"success": False, "error": f"unknown action '{action}'"}
