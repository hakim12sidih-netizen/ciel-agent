"""
CIEL v∞.8 — DIMENSION XLV : COMPUTATIONAL UNIVERSE.
L'univers est un ordinateur — principe d'équivalence computationnelle.

Concept : Wolfram (2002) — Le principe d'équivalence computationnelle
dit que presque tous les processus (naturels, mathématiques,
cognitifs) atteignent le même niveau de complexité computationnelle.
CIEL explore l'espace de tous les programmes possibles, découvrant
des automates cellulaires universels, des systèmes de réécriture,
et les lois computationnelles sous-jacentes à la réalité.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


RULE_SPACE_SIZE = 256  # 256 règles élémentaires d'AC 1D


@dataclass(slots=True)
class CellularAutomaton:
    """Automate cellulaire 1D (règle élémentaire de Wolfram)."""
    id: str
    rule_number: int
    name: str = ""
    width: int = 100
    generations: int = 50
    state: list[int] = field(default_factory=lambda: [0] * 100)

    def __post_init__(self):
        if not self.name:
            self._classify()
        if len(self.state) != self.width:
            self.state = [0] * self.width
            self.state[self.width // 2] = 1  # cellule centrale = 1

    def _classify(self):
        """Classification de Wolfram."""
        r = self.rule_number
        # Approximation grossière de la classe
        if r in (0, 255):
            self.name = f"Règle {r} — Classe 1 (uniforme)"
        elif r in (90, 150, 105, 60):
            self.name = f"Règle {r} — Classe 2 (périodique)"
        elif r in (30, 45, 73, 86, 106, 110, 126, 137, 149, 150, 161, 182, 195, 210):
            self.name = f"Règle {r} — Classe 3 (chaotique)"
        elif r in (110, 184, 193, 250):
            self.name = f"Règle {r} — Classe 4 (complexe)"
        else:
            self.name = f"Règle {r}"

    def step(self) -> list[int]:
        """Une génération de l'automate."""
        new_state = [0] * self.width
        for i in range(self.width):
            left = self.state[(i - 1) % self.width]
            center = self.state[i]
            right = self.state[(i + 1) % self.width]
            pattern = (left << 2) | (center << 1) | right
            new_state[i] = (self.rule_number >> pattern) & 1
        self.state = new_state
        return self.state

    def run(self, steps: int | None = None) -> list[list[int]]:
        history = [list(self.state)]
        steps = steps or self.generations
        for _ in range(steps):
            self.step()
            history.append(list(self.state))
        return history

    def entropy(self) -> float:
        """Entropie de Shannon de l'état actuel."""
        ones = sum(self.state)
        zeros = self.width - ones
        if ones == 0 or zeros == 0:
            return 0.0
        p1 = ones / self.width
        p0 = zeros / self.width
        return -(p0 * math.log2(p0) + p1 * math.log2(p1))

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "rule": self.rule_number,
            "width": self.width,
            "entropy": self.entropy(),
        }


@dataclass(slots=True)
class ComputationalEquivalence:
    """Résultat du principe d'équivalence computationnelle."""
    system_a: str
    system_b: str
    equivalent: bool
    complexity_class: str = ""  # uniform | periodic | chaotic | complex | universal


class CompUnivEngine:
    """Moteur de l'univers computationnel.
    
    CIEL explore l'espace de tous les programmes (automates,
    systèmes de réécriture) et applique le principe d'équivalence
    computationnelle : tout système suffisamment complexe atteint
    le même niveau de calcul universel.
    """

    def __init__(self):
        self.automata: dict[str, CellularAutomaton] = {}
        self.equivalences: list[ComputationalEquivalence] = []
        self.network = LeaderNetwork()

    def create_automaton(self, rule: int, width: int = 100,
                         generations: int = 50) -> CellularAutomaton:
        ca = CellularAutomaton(
            id=f"CA-{uuid.uuid4().hex[:12]}",
            rule_number=rule, width=width,
            generations=generations,
        )
        self.automata[ca.id] = ca
        return ca

    def run_automaton(self, ca_id: str, steps: int | None = None) -> list[list[int]] | None:
        ca = self.automata.get(ca_id)
        if not ca:
            return None
        return ca.run(steps)

    def find_universal_rules(self) -> list[dict]:
        """Trouve les règles computationnellement universelles.
        
        Règle 110 a été prouvée universelle par Cook (2004).
        D'autres règles (30, 90, 184) sont candidates.
        """
        universals = [110]  # prouvé par Cook
        candidates = [30, 45, 54, 60, 73, 86, 90, 106, 110,
                      126, 137, 149, 150, 161, 182, 184, 193, 195, 210, 250]
        results = []
        for r in candidates:
            ca = self.create_automaton(r, width=200, generations=30)
            ca.run()
            entropy = ca.entropy()
            is_universal = r in universals
            results.append({
                "rule": r,
                "universal": is_universal,
                "entropy": entropy,
                "class": ca.name.split("—")[1].strip() if "—" in ca.name else "?",
            })
        return results

    def compare_systems(self, ca_a_id: str, ca_b_id: str) -> ComputationalEquivalence:
        """Compare deux systèmes par équivalence computationnelle."""
        a = self.automata.get(ca_a_id)
        b = self.automata.get(ca_b_id)
        if not a or not b:
            return ComputationalEquivalence("?", "?", False)
        # Principe de Wolfram : si entropie similaire → équivalents
        entropy_diff = abs(a.entropy() - b.entropy())
        equivalent = entropy_diff < 0.3
        if a.entropy() == 0:
            cls = "uniform"
        elif a.entropy() < 0.5:
            cls = "periodic"
        elif a.entropy() < 0.9:
            cls = "complex"
        else:
            cls = "chaotic"
        eq = ComputationalEquivalence(
            system_a=a.name, system_b=b.name,
            equivalent=equivalent, complexity_class=cls,
        )
        self.equivalences.append(eq)
        return eq

    def rule_space_explore(self, sample_size: int = 16) -> list[dict]:
        """Explore l'espace des règles de Wolfram."""
        results = []
        step = max(1, 256 // sample_size)
        for r in range(0, 256, step):
            ca = self.create_automaton(r, width=50, generations=20)
            ca.run()
            results.append({
                "rule": r,
                "class": ca.name.split("—")[1].strip() if "—" in ca.name else "?",
                "entropy": ca.entropy(),
            })
        return results

    def get_stats(self) -> dict:
        return {
            "automata": len(self.automata),
            "equivalences": len(self.equivalences),
            "rule_space_coverage": f"{len(self.automata)}/256",
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create":
            ca = self.create_automaton(
                input_data.get("rule", 110),
                input_data.get("width", 100),
                input_data.get("generations", 50),
            )
            return {"status": "ok", "automaton": ca.to_dict()}
        elif action == "run":
            h = self.run_automaton(input_data.get("ca_id", ""),
                                    input_data.get("steps"))
            return {"status": "ok" if h else "error",
                    "generations": len(h) if h else 0}
        elif action == "universal_rules":
            return {"status": "ok",
                    "rules": self.find_universal_rules()}
        elif action == "compare":
            eq = self.compare_systems(
                input_data.get("a", ""),
                input_data.get("b", ""),
            )
            return {"status": "ok",
                    "equivalence": {
                        "a": eq.system_a, "b": eq.system_b,
                        "equivalent": eq.equivalent,
                        "class": eq.complexity_class,
                    }}
        return {"status": "ok", "automata": len(self.automata)}
