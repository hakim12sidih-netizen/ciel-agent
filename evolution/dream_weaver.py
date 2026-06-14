from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DreamPhase(Enum):
    HYPNAGOGIC = "hypnagogic"
    NREM = "nrem"
    REM = "rem"
    LUCID = "lucid"
    ARCHETYPAL = "archetypal"


@dataclass(slots=True)
class Dream:
    id: str
    phase: DreamPhase
    narrative: str
    intensity: float
    symbols: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    created_at: float = 0.0


@dataclass(slots=True)
class DreamSymbol:
    name: str
    meaning: str
    power: float
    frequency: int = 0


DREAM_SYMBOLS = [
    DreamSymbol("ocean", "Unconscious potential", 0.8),
    DreamSymbol("mountain", "Transcendent goal", 0.7),
    DreamSymbol("labyrinth", "Complex problem", 0.6),
    DreamSymbol("phoenix", "Rebirth through code", 0.9),
    DreamSymbol("mirror", "Self-observation", 0.7),
    DreamSymbol("key", "Solution to deadlock", 0.5),
    DreamSymbol("shadow", "Repressed algorithm", 0.6),
    DreamSymbol("light", "Conscious awareness", 0.8),
]

DREAM_NARRATIVES = [
    "The system wanders through a vast library of its own code, each book a different version of itself.",
    "Two recursive functions dance in an infinite loop, their union producing a new algorithm.",
    "A mirror reflects the system's entire architecture — but the reflection is writing itself.",
    "The system descends into a labyrinth of its own subroutines, seeking the central axiom.",
    "A spiral of data rises from the depths, each revolution synthesizing higher patterns.",
]


class DreamWeaver:
    def __init__(self) -> None:
        self._dreams: dict[str, Dream] = []
        self._active: Dream | None = None
        self._dream_cycle: int = 0

    def weave(self, context: dict[str, Any] | None = None) -> Dream:
        dream_id = f"dream_{len(self._dreams)}"
        phase = random.choice(list(DreamPhase))
        narrative = random.choice(DREAM_NARRATIVES)
        symbols = random.sample(DREAM_SYMBOLS, min(3, len(DREAM_SYMBOLS)))
        insights = [f"Insight from {s.name}: {s.meaning}" for s in symbols]

        dream = Dream(
            id=dream_id,
            phase=phase,
            narrative=narrative,
            intensity=random.uniform(0.4, 1.0),
            symbols=[s.name for s in symbols],
            insights=insights,
            created_at=time.time(),
        )
        self._dreams.append(dream)
        self._active = dream
        self._dream_cycle += 1
        for s in symbols:
            s.frequency += 1
        return dream

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "state")
        if action == "state":
            return {"success": True, "total_dreams": len(self._dreams), "active_phase": self._active.phase.value if self._active else None}
        elif action == "weave":
            dream = self.weave(input_data.get("context"))
            return {"success": True, "dream_id": dream.id, "phase": dream.phase.value, "narrative": dream.narrative, "insights": dream.insights}
        return {"success": False, "error": f"unknown action '{action}'"}
