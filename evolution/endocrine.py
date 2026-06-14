from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class HormonalState:
    cortisol: float = 0.0
    dopamine: float = 0.0
    oxytocin: float = 0.0
    serotonin: float = 0.0
    adrenaline: float = 0.0
    noradrenaline: float = 0.0
    testosterone: float = 0.0
    estrogen: float = 0.0

    def as_vector(self) -> np.ndarray:
        return np.array([
            self.cortisol, self.dopamine, self.oxytocin, self.serotonin,
            self.adrenaline, self.noradrenaline, self.testosterone, self.estrogen,
        ], dtype=np.float32)


class HormonalSystem:
    """Endocrinological model — hormone regulation for adaptive behavior."""

    def __init__(self) -> None:
        self.state = HormonalState()
        self.history: list[HormonalState] = []
        self.decay_rate: float = 0.05
        self.homeostatic_target = HormonalState()

    def update(self, stress: float = 0.0, reward: float = 0.0, social: float = 0.0) -> None:
        self.state.cortisol += stress * 0.1 - self.decay_rate * self.state.cortisol
        self.state.dopamine += reward * 0.2 - self.decay_rate * self.state.dopamine
        self.state.oxytocin += social * 0.15 - self.decay_rate * self.state.oxytocin
        self.state.serotonin += (reward - stress) * 0.05 - self.decay_rate * self.state.serotonin
        self.state.adrenaline += stress * 0.3 - self.decay_rate * self.state.adrenaline
        self.state.noradrenaline += stress * 0.2 - self.decay_rate * self.state.noradrenaline
        for h in ["cortisol", "dopamine", "oxytocin", "serotonin", "adrenaline", "noradrenaline", "testosterone", "estrogen"]:
            v = getattr(self.state, h)
            v = max(0.0, v)
            setattr(self.state, h, v)
        self.history.append(HormonalState(
            cortisol=self.state.cortisol, dopamine=self.state.dopamine,
            oxytocin=self.state.oxytocin, serotonin=self.state.serotonin,
            adrenaline=self.state.adrenaline, noradrenaline=self.state.noradrenaline,
            testosterone=self.state.testosterone, estrogen=self.state.estrogen,
        ))

    def get_drive(self, hormone: str) -> float:
        return getattr(self.state, hormone, 0.0)

    def homeostasis_deviation(self) -> float:
        return sum(
            (getattr(self.state, h) - getattr(self.homeostatic_target, h)) ** 2
            for h in ["cortisol", "dopamine", "oxytocin", "serotonin"]
        )


class Cortisol:
    @staticmethod
    def effect(level: float) -> dict[str, float]:
        return {
            "stress_response": min(1.0, level / 10.0),
            "memory_consolidation": max(0.0, 1.0 - abs(level - 5.0) / 5.0),
            "immune_suppression": min(1.0, level / 15.0),
        }


class Dopamine:
    @staticmethod
    def effect(level: float) -> dict[str, float]:
        return {
            "motivation": min(1.0, level / 8.0),
            "reward_seeking": min(1.0, max(0.0, level - 3.0) / 5.0),
            "exploration": max(0.0, 1.0 - level / 10.0),
        }


class Oxytocin:
    @staticmethod
    def effect(level: float) -> dict[str, float]:
        return {
            "trust": min(1.0, level / 6.0),
            "bonding": min(1.0, level / 4.0),
            "anxiety_reduction": max(0.0, 1.0 - level / 8.0),
        }
