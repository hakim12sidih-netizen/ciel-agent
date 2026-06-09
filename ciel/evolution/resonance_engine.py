from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResonanceMode(Enum):
    HARMONIC = "harmonic"
    SYMPATHETIC = "sympathetic"
    STOCHASTIC = "stochastic"
    CHAOTIC = "chaotic"


@dataclass(slots=True)
class ResonancePattern:
    id: str
    frequency: float
    amplitude: float
    phase: float
    mode: ResonanceMode
    coherence: float
    harmonics: list[float] = field(default_factory=list)


class ResonanceEngine:
    def __init__(self) -> None:
        self._patterns: dict[str, ResonancePattern] = {}

    def generate_pattern(self, base_freq: float, mode: ResonanceMode = ResonanceMode.HARMONIC) -> ResonancePattern:
        pid = f"res_{len(self._patterns)}"
        harmonics = [base_freq * (i + 2) for i in range(5)]
        pattern = ResonancePattern(
            id=pid,
            frequency=base_freq,
            amplitude=random.uniform(0.3, 1.0),
            phase=random.uniform(0, 2 * math.pi),
            mode=mode,
            coherence=random.uniform(0.6, 1.0),
            harmonics=harmonics,
        )
        self._patterns[pid] = pattern
        return pattern

    def compute_interference(self, p1_id: str, p2_id: str) -> float:
        p1 = self._patterns.get(p1_id); p2 = self._patterns.get(p2_id)
        if not p1 or not p2:
            return 0.0
        return abs(p1.amplitude - p2.amplitude) * abs(p1.frequency - p2.frequency) / max(p1.frequency, p2.frequency)

    def resonate(self) -> float:
        if len(self._patterns) < 2:
            return 0.0
        freqs = [p.frequency for p in self._patterns.values()]
        avg_freq = sum(freqs) / len(freqs)
        variance = sum((f - avg_freq) ** 2 for f in freqs) / len(freqs)
        return 1.0 / (1.0 + variance)

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "state")
        if action == "state":
            return {"success": True, "patterns": len(self._patterns), "resonance": self.resonate()}
        elif action == "generate":
            p = self.generate_pattern(float(input_data.get("frequency", 440.0)))
            return {"success": True, "pattern_id": p.id, "frequency": p.frequency, "mode": p.mode.value}
        return {"success": False, "error": f"unknown action '{action}'"}
