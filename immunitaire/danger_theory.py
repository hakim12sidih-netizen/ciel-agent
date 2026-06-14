from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class SignalType(Enum):
    PAMP = "pamp"  # Pathogen-associated molecular pattern
    DAMP = "damp"  # Damage-associated molecular pattern
    STRESS = "stress"
    APOPTOSIS = "apoptosis"
    NECROSIS = "necrosis"
    INFLAMMATION = "inflammation"


@dataclass(slots=True)
class DangerSignal:
    signal_type: SignalType
    strength: float
    source: str = ""
    position: np.ndarray | None = None
    decay_rate: float = 0.1
    age: float = 0.0

    def is_active(self) -> bool:
        return self.strength * math.exp(-self.decay_rate * self.age) > 0.01


@dataclass(slots=True)
class APC:
    """Antigen-Presenting Cell — active la réponse adaptative."""
    activated: bool = False
    cytokine_level: float = 0.0
    antigen_processed: bool = False
    co_stimulation: float = 0.0

    def present(self, danger: DangerSignal) -> bool:
        if danger.strength > 0.5:
            self.activated = True
            self.cytokine_level = min(1.0, danger.strength)
            self.co_stimulation = min(1.0, self.cytokine_level * 1.2)
            return True
        return False

    def reset(self) -> None:
        self.activated = False
        self.cytokine_level = 0.0
        self.antigen_processed = False
        self.co_stimulation = 0.0


class DangerZone:
    """Théorie du Danger — Matzinger 1994.

    Le système immunitaire répond aux signaux de danger, pas au non-self.
    """

    def __init__(self, decay_rate: float = 0.05) -> None:
        self.signals: list[DangerSignal] = []
        self.apc = APC()
        self.decay_rate = decay_rate
        self.threshold: float = 0.3
        self.alarm_threshold: float = 0.7

    def add_signal(self, signal: DangerSignal) -> None:
        self.signals.append(signal)

    def add_pamp(self, strength: float, source: str = "") -> None:
        self.add_signal(DangerSignal(SignalType.PAMP, strength, source))

    def add_damp(self, strength: float, source: str = "") -> None:
        self.add_signal(DangerSignal(SignalType.DAMP, strength, source))

    def add_stress(self, strength: float, source: str = "") -> None:
        self.add_signal(DangerSignal(SignalType.STRESS, strength, source))

    def tick(self) -> None:
        """Decay all signals."""
        for s in self.signals:
            s.age += 1.0
        self.signals = [s for s in self.signals if s.is_active()]
        # APC activation
        total_danger = self.total_danger()
        self.apc.present(DangerSignal(SignalType.INFLAMMATION, total_danger))

    def total_danger(self) -> float:
        if not self.signals:
            return 0.0
        return sum(s.strength * math.exp(-self.decay_rate * s.age) for s in self.signals)

    def is_in_danger(self) -> bool:
        return self.total_danger() > self.threshold

    def is_alarm(self) -> bool:
        return self.total_danger() > self.alarm_threshold

    def danger_gradient(self) -> float:
        """Rate of change of danger level."""
        if len(self.signals) < 2:
            return 0.0
        return self.total_danger() - sum(
            s.strength * math.exp(-self.decay_rate * (s.age - 1)) for s in self.signals
        )

    def immune_decision(self) -> str:
        if self.is_alarm():
            return "adaptive_response"
        if self.is_in_danger():
            if self.danger_gradient() > 0:
                return "innate_response_escalating"
            return "innate_response"
        return "tolerance"

    def status(self) -> dict[str, Any]:
        return {
            "total_danger": self.total_danger(),
            "is_in_danger": self.is_in_danger(),
            "is_alarm": self.is_alarm(),
            "apc_activated": self.apc.activated,
            "cytokine_level": self.apc.cytokine_level,
            "active_signals": len(self.signals),
            "signal_types": [s.signal_type.value for s in self.signals],
        }
