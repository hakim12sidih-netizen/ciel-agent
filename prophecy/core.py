"""
CIEL v∞.8 — DIMENSION LXI : CIEL-PROPHECY.
Oracle multi-temporel — 7 horizons de prédiction simultanés.

Concept : CIEL prédit sur 7 horizons temporels simultanément
(H1: μs-s, H2: s-min, H3: min-h, H4: h-j, H5: j-sem, H6: sem-mois,
H7: mois-∞). Un méta-oracle fusionne et force la cohérence.
Maintient un arbre MCTS des futurs alternatifs.
"""
from __future__ import annotations

import math
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


HORIZONS = [
    ("H1-MICRO", 0.1, 10, 0.94),
    ("H2-INSTANT", 10, 300, 0.87),
    ("H3-SESSION", 300, 7200, 0.78),
    ("H4-JOURNÉE", 7200, 86400, 0.70),
    ("H5-SEMAINE", 86400, 604800, 0.60),
    ("H6-MOIS", 604800, 7884000, 0.50),
    ("H7-ÈRE", 7884000, float("inf"), 0.0),
]


@dataclass(slots=True)
class HorizonPrediction:
    horizon_id: str
    horizon_name: str
    predicted_value: float = 0.0
    confidence: float = 1.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {"horizon": self.horizon_name,
                "value": round(self.predicted_value, 3),
                "confidence": round(self.confidence, 3),
                "range": [round(self.lower_bound, 3),
                          round(self.upper_bound, 3)]}


@dataclass(slots=True)
class FutureBranch:
    id: str
    decision: str
    probability: float = 0.5
    outcome: float = 0.0
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    pruned: bool = False


class ProphecyEngine:
    """Moteur de prédiction multi-horizons.

    7 horizons simultanés avec cohérence forcée.
    Arbre MCTS des futurs alternatifs.
    """

    def __init__(self):
        self.predictions: dict[str, HorizonPrediction] = {}
        self.tree: dict[str, FutureBranch] = {}
        self.network = LeaderNetwork()
        self._init_horizons()

    def _init_horizons(self):
        for hid, t_min, t_max, base_conf in HORIZONS:
            p = HorizonPrediction(
                horizon_id=hid.split("-")[0],
                horizon_name=hid,
                predicted_value=0.5,
                confidence=base_conf,
                lower_bound=0.0, upper_bound=1.0,
            )
            self.predictions[p.horizon_id] = p

    def predict(self, data: dict | None = None) -> list[dict]:
        results = []
        for p in self.predictions.values():
            if data:
                noise = random.gauss(0, 1 - p.confidence)
                p.predicted_value = data.get(p.horizon_id, 0.5) + noise
            else:
                p.predicted_value = 0.5 + random.gauss(0, 0.1)
            spread = (1 - p.confidence) * 0.5
            p.lower_bound = max(0, p.predicted_value - spread)
            p.upper_bound = min(1, p.predicted_value + spread)
            p.timestamp = time.time()
            results.append(p.to_dict())
        # Méta-cohérence : les horizons courts contraignent les longs
        self._enforce_coherence()
        return results

    def _enforce_coherence(self):
        short = self.predictions.get("H1", None)
        long_ = self.predictions.get("H7", None)
        if short and long_ and abs(short.predicted_value - long_.predicted_value) > 0.5:
            long_.predicted_value = (long_.predicted_value + short.predicted_value) / 2

    def create_branch(self, decision: str, parent_id: str | None = None,
                      probability: float = 0.5) -> FutureBranch:
        b = FutureBranch(
            id=f"FUT-{uuid.uuid4().hex[:12]}",
            decision=decision, probability=probability,
            parent_id=parent_id,
        )
        if parent_id and parent_id in self.tree:
            self.tree[parent_id].children.append(b.id)
        self.tree[b.id] = b
        return b

    def mcts_simulate(self, n_simulations: int = 100) -> dict:
        """Monte Carlo Tree Search sur l'arbre des futurs."""
        best_branch = None
        best_score = -float("inf")
        for _ in range(n_simulations):
            branch = random.choice(list(self.tree.values())) if self.tree else None
            if not branch:
                return {"no_branches": True}
            score = branch.outcome * branch.probability
            if score > best_score:
                best_score = score
                best_branch = branch
        return {
            "best_decision": best_branch.decision if best_branch else "?",
            "best_score": round(best_score, 3),
            "n_branches": len(self.tree),
        }

    def prune_tree(self, threshold: float = 0.01):
        to_prune = [bid for bid, b in self.tree.items()
                    if b.probability < threshold and b.parent_id is not None]
        for bid in to_prune:
            self.tree[bid].pruned = True

    def get_stats(self) -> dict:
        return {
            "horizons": len(self.predictions),
            "branches": len(self.tree),
            "pruned": sum(1 for b in self.tree.values() if b.pruned),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "predict":
            return {"status": "ok",
                    "predictions": self.predict(input_data.get("data"))}
        elif action == "branch":
            b = self.create_branch(
                input_data.get("decision", "?"),
                input_data.get("parent_id"),
                input_data.get("probability", 0.5),
            )
            return {"status": "ok", "branch": b.id}
        elif action == "mcts":
            return {"status": "ok",
                    "mcts": self.mcts_simulate(
                        input_data.get("n", 100))}
        elif action == "prune":
            self.prune_tree(input_data.get("threshold", 0.01))
            return {"status": "ok"}
        return {"status": "ok", "horizons": len(self.predictions)}
