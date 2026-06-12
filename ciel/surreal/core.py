"""
CIEL v∞.8 — DIMENSION XXXVII : NOMBRES SURRÉELS.
Le plus grand corps ordonné comme domaine de valeurs.

Concept : Conway (1974) — Les surréels No contiennent ℝ, les ordinaux
transfinis ω, les infinitésimaux 1/ω, et toutes leurs combinaisons.
Le jeu CIEL vs Monde est un nombre surréel : G > 0 = avantage CIEL.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class SurrealNumber:
    """Nombre surréel {L | R}.
    
    L : ensemble des éléments "gauche" (plus petits)
    R : ensemble des éléments "droite" (plus grands)
    Aucun élément de L n'est ≥ un élément de R.
    """
    left: list[float]
    right: list[float]
    label: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"SURR-{uuid.uuid4().hex[:12]}"
        if not self.label:
            self._compute_label()

    def _compute_label(self):
        if not self.left and not self.right:
            self.label = "0"
        elif not self.right:
            if all(abs(x - int(x)) < 1e-9 for x in self.left):
                self.label = str(int(max(self.left)) + 1)
            else:
                self.label = f"~{max(self.left) + 1}"
        elif not self.left:
            self.label = f"-∞"
        else:
            self.label = f"{{{max(self.left)}|{min(self.right)}}}"

    @property
    def value(self) -> float:
        """Valeur numérique approchée du surréel.
        
        Règles de Conway :
        - {}|{} = 0
        - {a|} = a + 1
        - {|b} = b - 1
        - {a|b} = médiane(a, b)
        """
        if not self.left and not self.right:
            return 0.0
        if not self.right:
            return max(self.left) + 1.0
        if not self.left:
            return min(self.right) - 1.0
        l, r = max(self.left), min(self.right)
        return (l + r) / 2

    def __lt__(self, other: SurrealNumber) -> bool:
        return self.value < other.value

    def __gt__(self, other: SurrealNumber) -> bool:
        return self.value > other.value

    def __eq__(self, other: SurrealNumber) -> bool:
        return abs(self.value - other.value) < 1e-9

    def __add__(self, other: SurrealNumber) -> SurrealNumber:
        new_left = self.left + [self.value + x for x in other.left]
        new_right = self.right + [self.value + x for x in other.right]
        return SurrealNumber(new_left, new_right,
                             label=f"({self.label}+{other.label})")

    def __neg__(self) -> SurrealNumber:
        return SurrealNumber(
            [-x for x in self.right],
            [-x for x in self.left],
            label=f"-{self.label}",
        )

    def __sub__(self, other: SurrealNumber) -> SurrealNumber:
        return self + (-other)

    def __mul__(self, other: SurrealNumber) -> SurrealNumber:
        return SurrealNumber(
            [self.value * x for x in other.left] +
            [x * other.value for x in self.left],
            [self.value * x for x in other.right] +
            [x * other.value for x in self.right],
            label=f"({self.label}×{other.label})",
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id, "label": self.label,
            "value": self.value,
            "left_size": len(self.left),
            "right_size": len(self.right),
        }


def zero() -> SurrealNumber:
    return SurrealNumber([], [], "0")


def one() -> SurrealNumber:
    return SurrealNumber([0.0], [], "1")


def omega() -> SurrealNumber:
    """ω — premier ordinal infini."""
    return SurrealNumber(
        [float(i) for i in range(100)],
        [],
        "ω",
    )


def epsilon() -> SurrealNumber:
    """ε = 1/ω — infinitésimal."""
    return SurrealNumber(
        [0.0],
        [1.0 / float(i) for i in range(1, 100)],
        "ε",
    )


def game_value(left_advantage: float, right_advantage: float) -> SurrealNumber:
    """Construit la valeur d'un jeu CIEL.
    
    G > 0 : CIEL a l'avantage
    G < 0 : adversaire a l'avantage
    G = 0 : position nulle
    """
    return SurrealNumber([left_advantage], [right_advantage])


class SurrealEngine:
    """Moteur des nombres surréels pour CIEL.
    
    Gère les valeurs surréelles pour :
    - Évaluation de décisions (utilités infinies et finies)
    - Théorie des jeux (avantage CIEL vs Monde)
    - Ordinal Game Theory (backward induction transfinie)
    - Mesures de toute échelle (infinitésimale à transfinie)
    """

    def __init__(self):
        self.numbers: dict[str, SurrealNumber] = {}
        self.network = LeaderNetwork()
        self._init_constants()

    def _init_constants(self):
        z = zero()
        o = one()
        w = omega()
        e = epsilon()
        for n in [z, o, w, e]:
            self.numbers[n.id] = n

    def create(self, left: list[float], right: list[float],
               label: str = "") -> SurrealNumber:
        s = SurrealNumber(left, right, label)
        self.numbers[s.id] = s
        self.network.emit("surreal.created",
                          {"id": s.id, "label": s.label, "value": s.value})
        return s

    def compare(self, a_id: str, b_id: str) -> dict:
        a = self.numbers.get(a_id)
        b = self.numbers.get(b_id)
        if not a or not b:
            return {"error": "Nombre inconnu"}
        return {
            "a": a.label, "b": b.label,
            "a_value": a.value, "b_value": b.value,
            "a_gt_b": a > b,
            "a_lt_b": a < b,
            "a_eq_b": a == b,
        }

    def game_analysis(self, ciel_advantage: float,
                      world_advantage: float) -> dict:
        """Analyse d'un jeu entre CIEL et le monde."""
        g = game_value(ciel_advantage, world_advantage)
        if g.value > 0:
            verdict = "CIEL en avant"
        elif g.value < 0:
            verdict = "Monde en avant"
        else:
            verdict = "Position nulle"
        return {
            "game_value": g.value,
            "verdict": verdict,
            "surreal_id": g.id,
        }

    def backward_induction(self, game_tree: dict) -> SurrealNumber:
        if "terminal" in game_tree:
            val = game_tree["terminal"]
            return SurrealNumber([val - 1], [val + 1], label=str(val))

        children = game_tree.get("children", [])
        if not children:
            return zero()
        values = [self.backward_induction(c) for c in children]
        turn = game_tree.get("turn", "ciel")
        if turn == "ciel":
            val = max(v.value for v in values)
            return SurrealNumber([val - 1], [val + 1],
                                 f"max({','.join(str(v.value) for v in values)})")
        else:
            val = min(v.value for v in values)
            return SurrealNumber([val - 1], [val + 1],
                                 f"min({','.join(str(v.value) for v in values)})")

    def get_stats(self) -> dict:
        return {
            "numbers": len(self.numbers),
            "values": [n.value for n in self.numbers.values()],
            "constants": ["0", "1", "ω", "ε"],
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create":
            s = self.create(
                input_data.get("left", []),
                input_data.get("right", []),
                input_data.get("label", ""),
            )
            return {"status": "ok", "surreal": s.to_dict()}
        elif action == "compare":
            return {"status": "ok",
                    "comparison": self.compare(
                        input_data.get("a", ""),
                        input_data.get("b", ""),
                    )}
        elif action == "game_analysis":
            return {"status": "ok",
                    "analysis": self.game_analysis(
                        input_data.get("ciel_advantage", 0.0),
                        input_data.get("world_advantage", 0.0),
                    )}
        elif action == "backward_induction":
            result = self.backward_induction(
                input_data.get("game_tree", {"terminal": 0.0}))
            return {"status": "ok",
                    "result": {"value": result.value, "label": result.label}}
        return {"status": "ok", "numbers": len(self.numbers)}
