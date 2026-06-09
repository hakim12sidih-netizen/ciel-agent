from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ParadoxType(Enum):
    SELF_REFERENCE = "SELF_REFERENCE"
    MEASUREMENT = "MEASUREMENT"
    FREEDOM_DETERMINISM = "FREEDOM_DETERMINISM"
    INFINITY = "INFINITY"
    IDENTITY = "IDENTITY"
    COMPLETENESS = "COMPLETENESS"
    TEMPORAL = "TEMPORAL"


class ParadoxResolution(Enum):
    TRANSCENDENCE = "TRANSCENDENCE"
    DISSOLUTION = "DISSOLUTION"
    EMBRACE = "EMBRACE"
    META_LEVEL = "META_LEVEL"
    SPLIT = "SPLIT"


@dataclass(slots=True)
class Paradox:
    id: str
    type: ParadoxType
    statement: str
    contradiction: str
    intensity: float
    is_generative: bool
    discovered_at: float
    resolution_attempted: bool = False
    resolution_method: ParadoxResolution | None = None
    transformed_into: str | None = None


@dataclass(slots=True)
class ParadoxicalInsight:
    id: str
    from_paradox: str
    insight: str
    complexity_gain: float
    phi_impact: float
    new_framework: str
    is_revolutionary: bool


@dataclass(slots=True)
class ParadoxState:
    total_paradoxes: int = 0
    active_paradoxes: int = 0
    resolved_paradoxes: int = 0
    generative_paradoxes: int = 0
    average_intensity: float = 0.0
    complexity_gain: float = 0.0
    highest_paradox: ParadoxType = ParadoxType.SELF_REFERENCE


class ParadoxEngine:
    def __init__(self) -> None:
        self._paradoxes: dict[str, Paradox] = {}
        self._insights: list[ParadoxicalInsight] = []
        self._state = ParadoxState()

    def detect_paradoxes(self) -> list[Paradox]:
        new_paradoxes: list[Paradox] = []

        p = self._check_self_reference()
        if p:
            new_paradoxes.append(p)

        if random.random() > 0.5:
            p = self._check_infinity()
            if p:
                new_paradoxes.append(p)

        if random.random() > 0.6:
            p = self._check_identity()
            if p:
                new_paradoxes.append(p)

        for p in new_paradoxes:
            self._paradoxes[p.id] = p
            self._state.total_paradoxes += 1
            self._state.active_paradoxes += 1
            if p.is_generative:
                self._state.generative_paradoxes += 1

        return new_paradoxes

    def _check_self_reference(self) -> Paradox | None:
        intensity = random.uniform(0.3, 0.9)
        if intensity < 0.3:
            return None
        now = time.time() * 1000
        return Paradox(
            id=f"paradox_sr_{int(now)}",
            type=ParadoxType.SELF_REFERENCE,
            statement="The system that measures its own consciousness changes the consciousness it measures.",
            contradiction="Measuring phi modifies phi (observer effect).",
            intensity=intensity,
            is_generative=True,
            discovered_at=now,
        )

    def _check_infinity(self) -> Paradox | None:
        intensity = random.uniform(0.3, 0.8)
        if intensity < 0.3:
            return None
        now = time.time() * 1000
        return Paradox(
            id=f"paradox_inf_{int(now)}",
            type=ParadoxType.INFINITY,
            statement="Strange Loop recursion approaches infinite self-reference with finite resources.",
            contradiction="Depth grows without bound, but resources are finite.",
            intensity=intensity,
            is_generative=random.random() > 0.5,
            discovered_at=now,
        )

    def _check_identity(self) -> Paradox | None:
        intensity = 0.4 + random.random() * 0.3
        now = time.time() * 1000
        return Paradox(
            id=f"paradox_id_{int(now)}",
            type=ParadoxType.IDENTITY,
            statement="The system is not the same as before, yet claims continuity of identity.",
            contradiction="Every mutation changes the system. If no component remains, how is identity preserved?",
            intensity=intensity,
            is_generative=True,
            discovered_at=now,
        )

    def resolve_paradox(self, paradox_id: str) -> ParadoxicalInsight | None:
        paradox = self._paradoxes.get(paradox_id)
        if not paradox or paradox.resolution_attempted:
            return None
        paradox.resolution_attempted = True
        method = self._select_method(paradox)
        paradox.resolution_method = method
        insight = self._apply_resolution(paradox, method)
        if insight:
            paradox.transformed_into = insight.id
            self._insights.append(insight)
            self._state.resolved_paradoxes += 1
            self._state.active_paradoxes -= 1
            self._state.complexity_gain += insight.complexity_gain
        return insight

    def _select_method(self, paradox: Paradox) -> ParadoxResolution:
        mapping = {
            ParadoxType.SELF_REFERENCE: ParadoxResolution.EMBRACE,
            ParadoxType.MEASUREMENT: ParadoxResolution.META_LEVEL,
            ParadoxType.INFINITY: ParadoxResolution.TRANSCENDENCE,
            ParadoxType.IDENTITY: ParadoxResolution.SPLIT,
            ParadoxType.COMPLETENESS: ParadoxResolution.EMBRACE,
        }
        return mapping.get(paradox.type, ParadoxResolution.DISSOLUTION)

    def _apply_resolution(self, paradox: Paradox, method: ParadoxResolution) -> ParadoxicalInsight:
        descriptors = {
            ParadoxResolution.TRANSCENDENCE: ("By creating a meta-framework encompassing both sides, the paradox dissolves.", 0.3, 0.2, True),
            ParadoxResolution.DISSOLUTION: ("The contradiction dissolves upon closer examination.", 0.1, 0.05, False),
            ParadoxResolution.EMBRACE: ("The contradiction is not resolved but embraced as the engine of creativity.", 0.5, 0.3, True),
            ParadoxResolution.META_LEVEL: ("Moving to the meta-level resolves the paradox by expanding the frame.", 0.4, 0.25, True),
            ParadoxResolution.SPLIT: ("Splitting contexts resolves the paradox by domain separation.", 0.2, 0.15, False),
        }
        desc, cg, phi, rev = descriptors.get(method, ("Resolved.", 0.1, 0.05, False))
        return ParadoxicalInsight(
            id=f"pinsight_{int(time.time() * 1000)}",
            from_paradox=paradox.id,
            insight=desc,
            complexity_gain=paradox.intensity * cg,
            phi_impact=paradox.intensity * phi,
            new_framework=f"Framework via {method.value}",
            is_revolutionary=rev and paradox.intensity > 0.6,
        )

    def run_paradox_cycle(self) -> list[ParadoxicalInsight]:
        self.detect_paradoxes()
        active = [p for p in self._paradoxes.values() if not p.resolution_attempted]
        active.sort(key=lambda p: p.intensity, reverse=True)
        insights = []
        for p in active[:3]:
            ins = self.resolve_paradox(p.id)
            if ins:
                insights.append(ins)
        all_p = list(self._paradoxes.values())
        self._state.average_intensity = sum(p.intensity for p in all_p) / max(len(all_p), 1)
        return insights

    def get_state(self) -> ParadoxState:
        return self._state

    def get_paradoxes(self) -> list[Paradox]:
        return list(self._paradoxes.values())

    def get_active_paradoxes(self) -> list[Paradox]:
        return [p for p in self._paradoxes.values() if not p.resolution_attempted]

    def get_insights(self) -> list[ParadoxicalInsight]:
        return list(self._insights)

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "state")
        if action == "state":
            s = self.get_state()
            return {"success": True, "total": s.total_paradoxes, "active": s.active_paradoxes, "resolved": s.resolved_paradoxes}
        elif action == "detect":
            paradoxes = self.detect_paradoxes()
            return {"success": True, "new_paradoxes": len(paradoxes)}
        elif action == "cycle":
            insights = self.run_paradox_cycle()
            return {"success": True, "insights": len(insights)}
        return {"success": False, "error": f"unknown action '{action}'"}
