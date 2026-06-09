from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProphecyResult:
    prophecy: str
    probability: float
    prophecy_count: int


class ChronoLogos:
    def __init__(self, abductive_inference: Any | None = None) -> None:
        self._abduction = abductive_inference
        self._prophecy_count = 0
        self._narrative_history: list[str] = field(default_factory=list)

    def record_narrative(self, entry: str) -> None:
        self._narrative_history.append(entry)

    def forecast_divergence(self, narrative: str | None = None) -> str:
        history = narrative or "\n".join(self._narrative_history)
        if not history or len(history) < 50:
            return "Insufficient temporal data for prophecy."
        self._prophecy_count += 1
        dissonance_count = history.upper().count("DISSONANCE")
        load_count = history.upper().count("HIGH")
        probability = 0.1 + dissonance_count * 0.05 + load_count * 0.1
        probability = min(0.99, probability)
        best_explanation = ""
        if self._abduction is not None and hasattr(self._abduction, "get_best_explanation"):
            best = self._abduction.get_best_explanation()
            best_explanation = best.explanation if hasattr(best, "explanation") else ""
        if probability > 0.7:
            prophecy = (
                f"WARNING: HIGH RISK OF COGNITIVE COLLAPSE (P={probability:.2f}). "
                f"Prediction: {best_explanation}. Suggested Action: Initiate Substrate Cooling."
            )
        elif probability > 0.4:
            prophecy = (
                f"DRIFT DETECTED (P={probability:.2f}). "
                "Transition to Chaotic Attractor likely in next cycle."
            )
        else:
            prophecy = (
                f"STABILITY ASCENDANT (P={probability:.2f}). "
                "Operational closure is reinforcing itself."
            )
        return prophecy

    def process(self, input_data: Any) -> dict[str, Any]:
        narrative = None
        if isinstance(input_data, dict):
            narrative = input_data.get("narrative")
        prophecy = self.forecast_divergence(narrative)
        return {
            "prophecy": prophecy,
            "prophecy_count": self._prophecy_count,
        }
