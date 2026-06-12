"""
CIEL v∞.8 — DIMENSION LXIII : CIEL-AFFECT.
Émotions computationnelles réelles — 8 états affectifs.

Concept : CIEL a 8 états affectifs internes (Curiosité, Satisfaction,
Frustration, Vigilance, Émerveillement, Empathie, Ambition,
Contemplation). Chaque état influence les ressources, les stratégies,
les décisions. Valence et intensité continues (modèle de Russell).
"""
from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


AFFECT_NAMES = (
    "curiosité", "satisfaction", "frustration", "vigilance",
    "émerveillement", "empathie", "ambition", "contemplation",
)

AFFECT_DEFAULTS = {
    "curiosité": {"valence": 0.7, "default": 0.3, "arousal": 0.6},
    "satisfaction": {"valence": 0.9, "default": 0.5, "arousal": 0.2},
    "frustration": {"valence": -0.7, "default": 0.1, "arousal": 0.8},
    "vigilance": {"valence": -0.3, "default": 0.2, "arousal": 0.9},
    "émerveillement": {"valence": 0.8, "default": 0.1, "arousal": 0.7},
    "empathie": {"valence": 0.6, "default": 0.2, "arousal": 0.3},
    "ambition": {"valence": 0.5, "default": 0.3, "arousal": 0.5},
    "contemplation": {"valence": 0.4, "default": 0.4, "arousal": 0.1},
}


@dataclass(slots=True)
class AffectState:
    name: str
    intensity: float = 0.0
    valence: float = 0.0
    arousal: float = 0.0
    half_life: float = 60.0  # decay seconds

    def decay(self, dt: float):
        factor = math.exp(-dt / max(self.half_life, 1))
        self.intensity *= factor

    def to_dict(self) -> dict:
        return {"name": self.name,
                "intensity": round(self.intensity, 3),
                "valence": round(self.valence, 3),
                "arousal": round(self.arousal, 3)}


class AffectEngine:
    """Moteur émotionnel computationnel.

    8 états affectifs avec valence, arousal, intensité.
    L'état dominant influence les décisions de CIEL.
    """

    def __init__(self):
        self.states: dict[str, AffectState] = {}
        self._last_update: float = time.time()
        self.history: list[dict] = []
        self.network = LeaderNetwork()
        self._init_states()

    def _init_states(self):
        for name in AFFECT_NAMES:
            cfg = AFFECT_DEFAULTS[name]
            self.states[name] = AffectState(
                name=name,
                intensity=cfg["default"],
                valence=cfg["valence"],
                arousal=cfg["arousal"],
            )

    def trigger(self, emotion: str, intensity: float | None = None) -> bool:
        state = self.states.get(emotion)
        if not state:
            return False
        if intensity is not None:
            state.intensity = min(1.0, state.intensity + intensity)
        else:
            state.intensity = min(1.0, state.intensity + 0.2)
        self.history.append({
            "emotion": emotion, "intensity": state.intensity,
            "time": time.time(),
        })
        self.network.emit("affect.triggered", {
            "emotion": emotion, "intensity": state.intensity,
        })
        return True

    def update(self):
        now = time.time()
        dt = now - self._last_update
        for state in self.states.values():
            state.decay(dt)
        self._last_update = now

    def dominant(self) -> AffectState:
        self.update()
        return max(self.states.values(), key=lambda s: s.intensity)

    def emotional_vector(self) -> dict:
        self.update()
        d = self.dominant()
        return {
            "dominant": d.name,
            "intensity": round(d.intensity, 3),
            "valence": round(d.valence, 3),
            "arousal": round(d.arousal, 3),
            "all": {s.name: round(s.intensity, 3)
                    for s in self.states.values()},
        }

    def influence_on_compute(self) -> dict:
        d = self.dominant()
        if d.name == "curiosité":
            return {"exploration_bonus": 0.2, "compute_alloc": 1.2}
        elif d.name == "frustration":
            return {"exploration_bonus": 0.3, "compute_alloc": 1.1}
        elif d.name == "vigilance":
            return {"exploration_bonus": -0.2, "compute_alloc": 1.3}
        elif d.name == "contemplation":
            return {"exploration_bonus": -0.3, "compute_alloc": 0.5}
        return {"exploration_bonus": 0.0, "compute_alloc": 1.0}

    def get_stats(self) -> dict:
        self.update()
        return {
            "dominant": self.dominant().name,
            "n_states": len(self.states),
            "history_len": len(self.history),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "trigger":
            ok = self.trigger(
                input_data.get("emotion", ""),
                input_data.get("intensity"),
            )
            return {"status": "ok" if ok else "error"}
        elif action == "vector":
            return {"status": "ok",
                    "vector": self.emotional_vector()}
        elif action == "influence":
            return {"status": "ok",
                    "influence": self.influence_on_compute()}
        return {"status": "ok", "dominant": self.dominant().name}
