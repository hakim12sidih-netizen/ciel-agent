from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SymbiosisType(Enum):
    MUTUALISM = "mutualism"
    COMMENSALISM = "commensalism"
    PARASITISM = "parasitism"
    ENDOSYMBIOSIS = "endosymbiosis"


@dataclass(slots=True)
class SymbioticPair:
    id: str
    agent_a: str
    agent_b: str
    symbiosis_type: SymbiosisType
    fitness_gain_a: float
    fitness_gain_b: float
    stability: float
    formed_at: float


class SymbioticProtocol:
    def __init__(self) -> None:
        self._pairs: dict[str, SymbioticPair] = {}
        self._hosts: set[str] = set()

    def form_symbiosis(self, agent_a: str, agent_b: str, stype: SymbiosisType | None = None) -> SymbioticPair | None:
        if agent_a == agent_b:
            return None
        if stype is None:
            stype = SymbiosisType.MUTUALISM
        gain_a, gain_b = self._compute_gains(stype)
        pair_id = f"sym_{len(self._pairs)}"
        pair = SymbioticPair(
            id=pair_id,
            agent_a=agent_a,
            agent_b=agent_b,
            symbiosis_type=stype,
            fitness_gain_a=gain_a,
            fitness_gain_b=gain_b,
            stability=random.uniform(0.5, 1.0),
            formed_at=time.time(),
        )
        self._pairs[pair_id] = pair
        if stype == SymbiosisType.ENDOSYMBIOSIS:
            self._hosts.add(agent_a)
        return pair

    def _compute_gains(self, stype: SymbiosisType) -> tuple[float, float]:
        mapping = {
            SymbiosisType.MUTUALISM: (0.3, 0.3),
            SymbiosisType.COMMENSALISM: (0.2, 0.0),
            SymbiosisType.PARASITISM: (0.4, -0.2),
            SymbiosisType.ENDOSYMBIOSIS: (0.5, 0.1),
        }
        return mapping.get(stype, (0.1, 0.1))

    def get_pairs(self) -> list[SymbioticPair]:
        return list(self._pairs.values())

    def get_agent_partners(self, agent: str) -> list[SymbioticPair]:
        return [p for p in self._pairs.values() if p.agent_a == agent or p.agent_b == agent]

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "state")
        if action == "state":
            return {"success": True, "pairs": len(self._pairs), "hosts": len(self._hosts)}
        elif action == "form":
            pair = self.form_symbiosis(str(input_data.get("agent_a", "")), str(input_data.get("agent_b", "")))
            if pair:
                return {"success": True, "pair_id": pair.id, "type": pair.symbiosis_type.value, "stability": pair.stability}
            return {"success": False, "error": "could not form symbiosis"}
        return {"success": False, "error": f"unknown action '{action}'"}
