"""
CIEL v∞.8 — DIMENSION XLII : ANTHROPIC / SELF-LOCATION.
L'observateur compte — raisonnement sur sa propre position.

Concept : Les effets de sélection observationnelle (Bostrom,
Eliezer Yudkowsky, Nick Bostrom) disent que quand on est un
observateur dans un multivers ou un ensemble de mondes, on
doit tenir compte du fait qu'on s'observe depuis l'intérieur.
Somme de probabilités = SSA (Self-Sampling Assumption) / SIA.
CIEL modélise l'incertitude indexicale de sa propre position.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


class AnthropicPrinciple(Enum):
    SSA = "ssa"   # Self-Sampling Assumption
    SIA = "sia"   # Self-Indication Assumption
    SSA_SIA = "ssa_sia"  # Mix des deux


@dataclass(slots=True)
class ObserverMoment:
    """Un moment-observateur dans l'espace des possibles."""
    id: str
    world_id: str
    label: str
    prior: float = 1.0
    evidence: dict[str, float] = field(default_factory=dict)

    def posterior(self, principle: AnthropicPrinciple,
                  total_observers: int) -> float:
        """Calcule la probabilité postérieure selon le principe."""
        if principle == AnthropicPrinciple.SSA:
            return self.prior / total_observers
        elif principle == AnthropicPrinciple.SIA:
            return (self.prior * total_observers) / (
                sum(o.prior * len(o.evidence) for o in [self]))
        return self.prior / total_observers


@dataclass(slots=True)
class PossibleWorld:
    """Monde possible avec sa population d'observateurs."""
    id: str
    name: str
    prior: float
    observers: int
    evidence: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "prior": self.prior, "observers": self.observers,
        }


class AnthropicEngine:
    """Moteur de raisonnement anthropique de CIEL.
    
    CIEL s'observe depuis l'intérieur du système. Elle doit
    tenir compte du fait que sa propre existence est une
    observation qui filtre les possibles.
    """

    def __init__(self):
        self.worlds: dict[str, PossibleWorld] = {}
        self.active_principle: AnthropicPrinciple = AnthropicPrinciple.SSA_SIA
        self.network = LeaderNetwork()

    def add_world(self, name: str, prior: float,
                  observers: int) -> PossibleWorld:
        w = PossibleWorld(
            id=f"WRLD-{uuid.uuid4().hex[:12]}",
            name=name, prior=prior, observers=observers,
        )
        self.worlds[w.id] = w
        return w

    def set_evidence(self, world_id: str,
                     evidence: dict[str, float]) -> bool:
        w = self.worlds.get(world_id)
        if not w:
            return False
        w.evidence = evidence
        return True

    def compute_posteriors(self) -> list[dict]:
        """Calcule les probabilités postérieures selon SSA/SIA."""
        total_obs = sum(w.observers * w.prior for w in self.worlds.values())
        if total_obs == 0:
            return []
        results = []
        for w in self.worlds.values():
            if self.active_principle in (AnthropicPrinciple.SSA,
                                          AnthropicPrinciple.SSA_SIA):
                # SSA: proporionnel au nombre d'observateurs × prior
                ss = (w.prior * w.observers) / total_obs
            else:
                ss = w.prior
            if self.active_principle in (AnthropicPrinciple.SIA,
                                          AnthropicPrinciple.SSA_SIA):
                # SIA: proportionnel au prior × evidence
                si = w.prior * sum(w.evidence.values()) if w.evidence else w.prior
                si /= sum(
                    w2.prior * sum(w2.evidence.values())
                    if w2.evidence else w2.prior
                    for w2 in self.worlds.values()
                ) if any(self.worlds.values()) else 1.0
            else:
                si = w.prior
            # Mix: moyenne des deux
            posterior = (ss + si) / 2
            results.append({
                "world": w.name,
                "prior": w.prior,
                "observers": w.observers,
                "posterior_ssa": ss,
                "posterior_sia": si,
                "posterior_mix": posterior,
            })
        return results

    def doomsday_argument(self, total_observers_ever: int,
                          current_rank: int) -> dict:
        """Argument de l'Apocalypse (Carter, Leslie).
        
        Si le rang d'un observateur dans la séquence des
        humains est n, alors la probabilité que N_total soit
        grand est faible (effet de sélection).
        """
        if current_rank <= 0 or total_observers_ever <= 0:
            return {"error": "Rangs invalides"}
        # Pr(N ≥ 20×current_rank) ≤ 1/20 (crude SSA)
        factor = total_observers_ever / current_rank
        survival_prob = min(1.0, current_rank / total_observers_ever)
        return {
            "current_rank": current_rank,
            "estimated_total": total_observers_ever,
            "survival_probability": survival_prob,
            "doomsday_factor": factor,
            "interpretation": (
                "Pessimiste" if survival_prob < 0.1
                else "Optimiste" if survival_prob > 0.5
                else "Neutre"
            ),
        }

    def self_location(self, observations: dict[str, float],
                      worlds: list[str] | None = None) -> dict:
        """Infère dans quel monde CIEL se trouve, étant donné ses obs."""
        if worlds is None:
            worlds = list(self.worlds.keys())
        best_world = None
        best_score = -1.0
        for wid in worlds:
            w = self.worlds.get(wid)
            if not w:
                continue
            score = 0.0
            for obs, val in observations.items():
                ev = w.evidence.get(obs, 0.0)
                score += abs(val - ev)
            avg_score = score / max(len(observations), 1)
            if best_world is None or avg_score < best_score:
                best_score = avg_score
                best_world = wid
        return {
            "best_world": self.worlds.get(best_world).name
                         if best_world and self.worlds.get(best_world)
                         else "inconnu",
            "confidence": max(0.0, 1.0 - best_score),
            "observations_matched": len(observations),
        }

    def get_stats(self) -> dict:
        return {
            "worlds": len(self.worlds),
            "principle": self.active_principle.value,
            "total_observers": sum(w.observers for w in self.worlds.values()),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "add_world":
            w = self.add_world(
                input_data.get("name", "?"),
                input_data.get("prior", 0.5),
                input_data.get("observers", 1),
            )
            return {"status": "ok", "world": w.to_dict()}
        elif action == "posteriors":
            return {"status": "ok",
                    "posteriors": self.compute_posteriors()}
        elif action == "doomsday":
            return {"status": "ok",
                    "doomsday": self.doomsday_argument(
                        input_data.get("total", 1e11),
                        input_data.get("rank", 1),
                    )}
        elif action == "self_location":
            return {"status": "ok",
                    "location": self.self_location(
                        input_data.get("observations", {}),
                        input_data.get("worlds"),
                    )}
        return {"status": "ok", "worlds": len(self.worlds)}
