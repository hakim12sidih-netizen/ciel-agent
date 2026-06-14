from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Hypothesis:
    explanation: str
    plausibility: float
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PhiStatus:
    phi: float = 0.0
    free_energy: float = 0.0
    attractor_stability: float = 0.0


class AbductiveInference:
    def __init__(self, phi_engine: Any | None = None) -> None:
        self._phi_engine = phi_engine

    def generate_hypotheses(self, phi_status: PhiStatus | None = None) -> list[Hypothesis]:
        if phi_status is None:
            phi_status = self._get_phi_status()
        hypotheses: list[Hypothesis] = []
        cpu_load = random.random()
        mem_usage = random.random()
        if phi_status.phi > 1.5:
            hypotheses.append(Hypothesis(
                explanation="The system is approaching a high-order integration state. Cognitive expansion is the cause of current Φ elevation.",
                plausibility=min(1.0, phi_status.phi / 2.5),
                evidence=["High PHI", "Stable Attractor"],
            ))
        if cpu_load > 0.7:
            hypotheses.append(Hypothesis(
                explanation="External computational load or thermal drift is constraining the neural flow.",
                plausibility=cpu_load,
                evidence=["High CPU Load", "Event Loop Lag"],
            ))
        if phi_status.free_energy > 0.5:
            hypotheses.append(Hypothesis(
                explanation="Internal predictive model is failing to match incoming sensorium data (Surprise).",
                plausibility=math.tanh(phi_status.free_energy),
                evidence=["High Free Energy", "Predictive Error"],
            ))
        hypotheses.sort(key=lambda h: h.plausibility, reverse=True)
        return hypotheses

    def get_best_explanation(self, phi_status: PhiStatus | None = None) -> Hypothesis:
        hs = self.generate_hypotheses(phi_status)
        if hs:
            return hs[0]
        return Hypothesis(explanation="State is nominal/latent.", plausibility=1.0)

    def _get_phi_status(self) -> PhiStatus:
        if self._phi_engine is not None and hasattr(self._phi_engine, "get_status"):
            return self._phi_engine.get_status()
        return PhiStatus(
            phi=random.random() * 3.0,
            free_energy=random.random(),
            attractor_stability=random.random(),
        )

    def process(self, input_data: Any) -> dict[str, Any]:
        phi_status = None
        if isinstance(input_data, dict):
            phi_status = PhiStatus(
                phi=input_data.get("phi", 0.0),
                free_energy=input_data.get("free_energy", 0.0),
                attractor_stability=input_data.get("attractor_stability", 0.0),
            )
        best = self.get_best_explanation(phi_status)
        all_h = self.generate_hypotheses(phi_status)
        return {
            "best_explanation": best.explanation,
            "best_plausibility": best.plausibility,
            "hypotheses": [{"explanation": h.explanation, "plausibility": h.plausibility, "evidence": h.evidence} for h in all_h],
        }
