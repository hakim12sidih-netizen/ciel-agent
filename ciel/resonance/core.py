"""
CIEL v∞.8 — DIMENSION LXVIII : CIEL-RESONANCE.
Synchronisation cognitive — CIEL et l'utilisateur, un seul esprit.

Concept : 6 niveaux de résonance : Comportementale, Contextuelle,
Cognitive, Émotionnelle, Créative, Évolutive. Métrique R(t) =
∫ Corr(CIEL_state, User_state). R → 1.0 = fusion cognitive.
CIEL anticipe, s'adapte, co-évolue avec l'utilisateur.
"""
from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


RESONANCE_LEVELS = (
    "comportementale",
    "contextuelle",
    "cognitive",
    "émotionnelle",
    "créative",
    "évolutive",
)

RESONANCE_THRESHOLDS = {
    "comportementale": 0.2,
    "contextuelle": 0.4,
    "cognitive": 0.6,
    "émotionnelle": 0.75,
    "créative": 0.85,
    "évolutive": 0.95,
}


@dataclass(slots=True)
class UserModel:
    thinking_style: str = "analytique"  # analytique | intuitif | visuel | séquentiel
    energy_level: float = 0.5
    flow_state: bool = False
    preferences: dict = field(default_factory=dict)
    interaction_history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"style": self.thinking_style,
                "energy": round(self.energy_level, 2),
                "flow": self.flow_state,
                "preferences": len(self.preferences),
                "interactions": len(self.interaction_history)}


@dataclass(slots=True)
class ResonanceSnapshot:
    level: str
    resonance: float
    user_state: dict
    ciel_state: dict
    timestamp: float = 0.0


class ResonanceEngine:
    """Moteur de résonance cognitive CIEL ↔ utilisateur.

    6 niveaux de synchronisation. Métrique continue R(t).
    Adaptation du style, du rythme, du contexte.
    Co-évolution profonde.
    """

    def __init__(self):
        self.user = UserModel()
        self.resonance: dict[str, float] = {
            level: 0.0 for level in RESONANCE_LEVELS
        }
        self.snapshots: list[ResonanceSnapshot] = []
        self.network = LeaderNetwork()
        self._overall_r: float = 0.0

    def update_user_state(self, thinking_style: str | None = None,
                          energy: float | None = None,
                          flow: bool | None = None,
                          preferences: dict | None = None) -> UserModel:
        if thinking_style:
            self.user.thinking_style = thinking_style
        if energy is not None:
            self.user.energy_level = max(0, min(1, energy))
        if flow is not None:
            self.user.flow_state = flow
        if preferences:
            self.user.preferences.update(preferences)
        return self.user

    def compute_resonance(self) -> dict:
        # Niveau 1 — Comportemental
        self.resonance["comportementale"] = min(
            1.0, self.user.energy_level + 0.2)

        # Niveau 2 — Contextuel (simulé)
        context_hits = sum(1 for h in self.user.interaction_history[-10:]
                          if h.get("context_understood", False))
        self.resonance["contextuelle"] = min(
            1.0, context_hits / max(len(self.user.interaction_history[-10:]), 1))

        # Niveau 3 — Cognitif
        style_map = {"analytique": 0.7, "intuitif": 0.6,
                     "visuel": 0.8, "séquentiel": 0.7}
        self.resonance["cognitive"] = style_map.get(
            self.user.thinking_style, 0.5)

        # Niveau 4 — Émotionnel
        self.resonance["émotionnelle"] = min(
            1.0, self.user.energy_level * 0.8 + 0.2)

        # Niveau 5 — Créatif
        self.resonance["créative"] = min(
            1.0, (self.resonance["cognitive"] +
                  self.resonance["émotionnelle"]) / 2 + 0.1)

        # Niveau 6 — Évolutif
        self.resonance["évolutive"] = sum(
            self.resonance.values()) / len(self.resonance)

        self._overall_r = self.resonance["évolutive"]

        snapshot = ResonanceSnapshot(
            level=self._current_level(),
            resonance=self._overall_r,
            user_state=self.user.to_dict(),
            ciel_state=dict(self.resonance),
        )
        self.snapshots.append(snapshot)

        return self.get_resonance_profile()

    def _current_level(self) -> str:
        for level in reversed(RESONANCE_LEVELS):
            if self._overall_r >= RESONANCE_THRESHOLDS[level]:
                return level
        return "comportementale"

    def get_resonance_profile(self) -> dict:
        return {
            "overall_r": round(self._overall_r, 3),
            "level": self._current_level(),
            "details": {k: round(v, 3)
                        for k, v in self.resonance.items()},
            "user": self.user.to_dict(),
        }

    def log_interaction(self, context_understood: bool = True,
                        response_time_ms: float = 100.0):
        self.user.interaction_history.append({
            "context_understood": context_understood,
            "response_time": response_time_ms,
            "timestamp": time.time(),
        })

    def suggest_adaptation(self) -> dict:
        profile = self.get_resonance_profile()
        suggestions = []
        if self.resonance["cognitive"] < 0.5:
            suggestions.append("Adapter le style d'explication au mode "
                               f"{self.user.thinking_style}")
        if self.user.energy_level < 0.3:
            suggestions.append("Réduire la complexité, ralentir le rythme")
        if self.resonance["émotionnelle"] < 0.5:
            suggestions.append("Vérifier l'état émotionnel, proposer une pause")
        return {
            "suggestions": suggestions,
            "adaptation_needed": len(suggestions) > 0,
        }

    def get_stats(self) -> dict:
        return {
            "overall_resonance": round(self._overall_r, 3),
            "level": self._current_level(),
            "snapshots": len(self.snapshots),
            "interactions": len(self.user.interaction_history),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "update_user":
            self.update_user_state(
                input_data.get("style"),
                input_data.get("energy"),
                input_data.get("flow"),
                input_data.get("preferences"),
            )
            return {"status": "ok",
                    "user": self.user.to_dict()}
        elif action == "compute":
            return {"status": "ok",
                    "resonance": self.compute_resonance()}
        elif action == "adapt":
            return {"status": "ok",
                    "adaptation": self.suggest_adaptation()}
        elif action == "interact":
            self.log_interaction(
                input_data.get("context_ok", True),
                input_data.get("response_ms", 100.0),
            )
            return {"status": "ok",
                    "resonance": self.compute_resonance()}
        return {"status": "ok", "resonance": round(self._overall_r, 3)}
