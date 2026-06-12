"""
CIEL v∞.8 — DIMENSION LI : NEXUS.
Réseau de causalité hyper-dimensionnel à N niveaux.

Concept : La causalité opère à N niveaux simultanément (physique,
système, cognitif, social, symbolique...). L'hypergraphe causal
HCG = (L, V, E, Φ, Ψ) relie les variables intra et inter-niveaux.
Interventions do-calculus multi-niveaux et détection de leviers.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


CAUSAL_LEVELS = [
    "physique", "système", "applicatif", "cognitif",
    "social", "temporel", "symbolique", "émergent",
]


@dataclass(slots=True)
class CausalVariable:
    id: str
    name: str
    level: str = "cognitif"
    value: float = 0.0
    is_lever: bool = False

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "level": self.level, "value": self.value,
                "lever": self.is_lever}


@dataclass(slots=True)
class CausalArc:
    source_id: str
    target_id: str
    strength: float = 0.5
    direction: float = 1.0  # 1 = positif, -1 = négatif
    intra_level: bool = True


@dataclass(slots=True)
class Intervention:
    var_id: str
    value: float
    level: str = "cognitif"
    timestamp: float = 0.0


class NexusEngine:
    """Moteur de causalité multi-niveaux.

    Maintient un hypergraphe causal HCG = (L, V, E, Φ, Ψ).
    Permet les interventions do-calculus, les contrefactuels,
    la détection de leviers causaux et la découverte causale.
    """

    def __init__(self):
        self.variables: dict[str, CausalVariable] = {}
        self.arcs: list[CausalArc] = []
        self.levels: list[str] = list(CAUSAL_LEVELS)
        self.network = LeaderNetwork()

    def add_variable(self, name: str, level: str = "cognitif",
                     value: float = 0.0) -> CausalVariable:
        v = CausalVariable(
            id=f"VAR-{uuid.uuid4().hex[:12]}",
            name=name, level=level, value=value,
        )
        self.variables[v.id] = v
        return v

    def add_cause(self, source_id: str, target_id: str,
                  strength: float = 0.5, direction: float = 1.0) -> bool:
        if source_id not in self.variables or target_id not in self.variables:
            return False
        src = self.variables[source_id]
        tgt = self.variables[target_id]
        intra = src.level == tgt.level
        self.arcs.append(CausalArc(source_id, target_id, strength,
                                    direction, intra))
        return True

    def do_intervention(self, var_id: str, value: float) -> list[dict]:
        """Intervention do-calculus : fixe X à x et propage."""
        var = self.variables.get(var_id)
        if not var:
            return []
        var.value = value
        effects = []
        for arc in self.arcs:
            if arc.source_id == var_id:
                target = self.variables.get(arc.target_id)
                if target:
                    delta = value * arc.strength * arc.direction
                    target.value += delta * 0.1
                    effects.append({
                        "source": var.name,
                        "target": target.name,
                        "delta": delta,
                        "level": target.level,
                    })
        return effects

    def counterfactual(self, var_id: str, actual: float,
                       hypothetical: float) -> dict:
        """'Si X = hyp au lieu de act, quel serait l'état ?' """
        original = {vid: v.value for vid, v in self.variables.items()}
        self.do_intervention(var_id, hypothetical)
        counter_state = {
            vid: v.value for vid, v in self.variables.items()
            if vid != var_id
        }
        # Restore
        for vid, val in original.items():
            if vid in self.variables:
                self.variables[vid].value = val
        var = self.variables.get(var_id)
        return {
            "variable": var.name if var else "?",
            "actual": actual,
            "hypothetical": hypothetical,
            "counterfactual_state": counter_state,
            "diff_count": sum(1 for v in counter_state.values()
                              if abs(v - original.get(var_id, 0)) > 0.01),
        }

    def find_levers(self, objective_var_id: str) -> list[dict]:
        """Trouve les 5 leviers les plus puissants."""
        target = self.variables.get(objective_var_id)
        if not target:
            return []
        scores = []
        for vid, var in self.variables.items():
            if vid == objective_var_id:
                continue
            score = 0.0
            for arc in self.arcs:
                if arc.source_id == vid and arc.target_id == objective_var_id:
                    score += abs(arc.strength * arc.direction)
            scores.append({
                "variable": var.name,
                "level": var.level,
                "lever_score": score,
            })
        scores.sort(key=lambda s: s["lever_score"], reverse=True)
        for s in scores[:5]:
            vid = next((v for v in self.variables.values()
                       if v.name == s["variable"]), None)
            if vid:
                vid.is_lever = True
        return scores[:5]

    def get_stats(self) -> dict:
        levels_count = {}
        for v in self.variables.values():
            levels_count[v.level] = levels_count.get(v.level, 0) + 1
        return {
            "variables": len(self.variables),
            "arcs": len(self.arcs),
            "levels": levels_count,
            "levers": sum(1 for v in self.variables.values() if v.is_lever),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "add_variable":
            v = self.add_variable(
                input_data.get("name", "?"),
                input_data.get("level", "cognitif"),
                input_data.get("value", 0.0),
            )
            return {"status": "ok", "variable": v.to_dict()}
        elif action == "add_cause":
            ok = self.add_cause(
                input_data.get("source", ""),
                input_data.get("target", ""),
                input_data.get("strength", 0.5),
                input_data.get("direction", 1.0),
            )
            return {"status": "ok" if ok else "error"}
        elif action == "intervene":
            effects = self.do_intervention(
                input_data.get("var_id", ""),
                input_data.get("value", 0.0),
            )
            return {"status": "ok", "effects": effects}
        elif action == "counterfactual":
            return {"status": "ok",
                    "result": self.counterfactual(
                        input_data.get("var_id", ""),
                        input_data.get("actual", 0.0),
                        input_data.get("hypothetical", 1.0),
                    )}
        elif action == "levers":
            return {"status": "ok",
                    "levers": self.find_levers(
                        input_data.get("objective", ""))}
        return {"status": "ok", "variables": len(self.variables)}
