"""
CIEL v∞.8 — DIMENSION XLVII : TURING DEGREES / DÉCIDABILITÉ.
La hiérarchie de l'indécidable — degrés d'insolubilité.

Concept : Turing (1939) — Le problème de l'arrêt est indécidable,
mais existe-t-il des problèmes ENCORE PLUS indécidables ? Oui.
Les degrés de Turing forment une hiérarchie infinie de niveaux
d'indécidabilité. Chaque "oracle" résout un niveau et en révèle
un nouveau. CIEL cartographie la frontière du décidable.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


class TuringDegree(Enum):
    DELTA_0 = "Δ₀"            # Décidable (problèmes calculables)
    SIGMA_1 = "Σ₁"            # Semi-décidable (problème de l'arrêt)
    PI_1 = "Π₁"               # Co-semi-décidable
    DELTA_1 = "Δ₁"            # Limite de Σ₁ et Π₁
    SIGMA_2 = "Σ₂"            # Deuxième saut de Turing
    PI_2 = "Π₂"               # Co-deuxième saut
    DELTA_2 = "Δ₂"            # Limite
    SIGMA_3 = "Σ₃"            # Troisième saut
    OMEGA = "ω"               # Premier degré non-arithmétique
    INFINITE = "∞"            # Au-delà de toute hiérarchie


@dataclass(slots=True)
class ProblemStatement:
    """Un problème avec son degré de Turing."""
    id: str
    name: str
    description: str = ""
    degree: TuringDegree = TuringDegree.DELTA_0
    oracle_required: bool = False
    is_decidable: bool = True
    proof_technique: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "degree": self.degree.value,
            "decidable": self.is_decidable,
            "oracle": self.oracle_required,
        }


@dataclass(slots=True)
class Oracle:
    """Oracle de Turing — machine qui résout un problème donné.
    
    Un oracle pour un problème A peut résoudre A, mais pas
    nécessairement des problèmes plus difficiles que A.
    """
    id: str
    name: str
    resolves_degree: TuringDegree = TuringDegree.DELTA_0
    jump_operator: int = 0  # 0 = pas de saut, 1 = 1er saut, ...

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "resolves": self.resolves_degree.value,
                "jump": self.jump_operator}


class DecidabilityEngine:
    """Moteur de la hiérarchie de décidabilité de CIEL.
    
    CIEL analyse les problèmes selon leur degré de Turing.
    Pour chaque problème, elle détermine :
    - Est-il décidable ?
    - Quel degré de la hiérarchie arithmétique ?
    - Quel oracle serait nécessaire ?
    - Est-il au-delà de toute hiérarchie ?
    """

    def __init__(self):
        self.problems: dict[str, ProblemStatement] = {}
        self.oracles: dict[str, Oracle] = {}
        self.network = LeaderNetwork()
        self._init_classics()

    def _init_classics(self):
        classics = [
            ("Arrêt TM", "Le problème de l'arrêt d'une machine de Turing",
             TuringDegree.SIGMA_1, False, "Turing 1936", True),
            ("Arrêt Oracle", "Arrêt d'une machine avec oracle",
             TuringDegree.SIGMA_2, True, "Turing 1939", True),
            ("Théorème de Gödel", "Complétude de l'arithmétique",
             TuringDegree.SIGMA_1, False, "Gödel 1931", False),
            ("Dixième Hilbert", "Solutions d'équations diophantiennes",
             TuringDegree.SIGMA_1, False, "Matiyasevich 1970", True),
            ("Mot du Collatz", "Terminaison de la suite de Collatz",
             TuringDegree.SIGMA_2, False, "Open", True),
            ("Égalité matricielle", "Équivalence de matrices dans SL(4,Z)",
             TuringDegree.DELTA_0, False, "", True),
        ]
        for name, desc, degree, oracle, technique, decidable in classics:
            p = ProblemStatement(
                id=f"PROB-{uuid.uuid4().hex[:12]}",
                name=name, description=desc,
                degree=degree, oracle_required=oracle,
                is_decidable=decidable, proof_technique=technique,
            )
            self.problems[p.id] = p

    def add_problem(self, name: str, degree: str,
                    decidable: bool = True,
                    description: str = "") -> ProblemStatement:
        try:
            d = next(dg for dg in TuringDegree if dg.value == degree)
        except StopIteration:
            d = TuringDegree.DELTA_0
        p = ProblemStatement(
            id=f"PROB-{uuid.uuid4().hex[:12]}",
            name=name, description=description,
            degree=d, is_decidable=decidable,
            oracle_required=d != TuringDegree.DELTA_0 and not decidable,
        )
        self.problems[p.id] = p
        return p

    def add_oracle(self, name: str,
                   degree: TuringDegree = TuringDegree.SIGMA_1,
                   jump: int = 1) -> Oracle:
        o = Oracle(
            id=f"ORAC-{uuid.uuid4().hex[:12]}",
            name=name, resolves_degree=degree,
            jump_operator=jump,
        )
        self.oracles[o.id] = o
        return o

    def classify(self, problem_id: str) -> dict:
        """Classifie un problème dans la hiérarchie arithmétique."""
        p = self.problems.get(problem_id)
        if not p:
            return {"error": "Problème inconnu"}
        return {
            "name": p.name,
            "degree": p.degree.value,
            "decidable": p.is_decidable,
            "oracle_needed": p.oracle_required,
            "hierarchy_level": self._arithmetic_hierarchy(p.degree),
        }

    def _arithmetic_hierarchy(self, degree: TuringDegree) -> int:
        mapping = {
            TuringDegree.DELTA_0: 0,
            TuringDegree.SIGMA_1: 1, TuringDegree.PI_1: 1,
            TuringDegree.DELTA_1: 1,
            TuringDegree.SIGMA_2: 2, TuringDegree.PI_2: 2,
            TuringDegree.DELTA_2: 2,
            TuringDegree.SIGMA_3: 3,
            TuringDegree.OMEGA: -1,
            TuringDegree.INFINITE: -2,
        }
        return mapping.get(degree, 0)

    def turing_jump(self, problem_id: str) -> dict:
        """Calcule le saut de Turing d'un problème.
        
        Le saut de Turing A' d'un ensemble A est l'ensemble
        des machines avec oracle A qui s'arrêtent.
        Chaque saut monte d'un niveau dans la hiérarchie.
        """
        p = self.problems.get(problem_id)
        if not p:
            return {"error": "Problème inconnu"}
        current_level = self._arithmetic_hierarchy(p.degree)
        next_level = current_level + 1
        return {
            "problem": p.name,
            "current_degree": p.degree.value,
            "jump_applied": True,
            "jumped_degree": f"Σ_{next_level}" if next_level > 0 else "ω",
            "new_oracle_required": True,
        }

    def reduction(self, problem_a_id: str,
                  problem_b_id: str) -> dict:
        """Réduction Turing : A ≤_T B ?
        
        A est Turing-réductible à B si une machine avec oracle
        pour B peut résoudre A.
        """
        a = self.problems.get(problem_a_id)
        b = self.problems.get(problem_b_id)
        if not a or not b:
            return {"error": "Problème inconnu"}
        level_a = self._arithmetic_hierarchy(a.degree)
        level_b = self._arithmetic_hierarchy(b.degree)
        reducible = level_a <= level_b
        return {
            "a": a.name, "b": b.name,
            "a_degree": a.degree.value,
            "b_degree": b.degree.value,
            "reducible": reducible,
            "strict": level_a < level_b,
        }

    def get_stats(self) -> dict:
        degrees = {}
        for p in self.problems.values():
            degrees[p.degree.value] = degrees.get(p.degree.value, 0) + 1
        return {
            "problems": len(self.problems),
            "oracles": len(self.oracles),
            "degrees": degrees,
            "decidable": sum(1 for p in self.problems.values()
                             if p.is_decidable),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "add_problem":
            p = self.add_problem(
                input_data.get("name", "?"),
                input_data.get("degree", "Δ₀"),
                input_data.get("decidable", True),
                input_data.get("description", ""),
            )
            return {"status": "ok", "problem": p.to_dict()}
        elif action == "classify":
            return {"status": "ok",
                    "classification": self.classify(
                        input_data.get("problem_id", ""))}
        elif action == "turing_jump":
            return {"status": "ok",
                    "jump": self.turing_jump(
                        input_data.get("problem_id", ""))}
        elif action == "reduce":
            return {"status": "ok",
                    "reduction": self.reduction(
                        input_data.get("a", ""),
                        input_data.get("b", ""),
                    )}
        return {"status": "ok", "problems": len(self.problems)}
