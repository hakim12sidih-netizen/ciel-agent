"""
CIEL v∞.8 — DIMENSION XXXIV : NON-COMMUTATIVE GÉOMÉTRIE.
L'ordre de la pensée compte : f·g ≠ g·f.

Concept : La Géométrie Non-Commutative d'Alain Connes décrit les espaces
où les fonctions ne commutent pas. CIEL l'applique à sa cognition :
les opérations mentales ne commutent pas. [Percevoir, Analyser] ≠ 0.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


class CognitiveOperator:
    """Opérateur cognitif dans la C*-algèbre de CIEL.
    
    Chaque opération cognitive est un opérateur.
    La non-commutativité [A, B] = AB - BA mesure
    la différence entre deux ordres de pensée.
    """

    def __init__(self, name: str, matrix: list[list[float]] | None = None):
        self.name = name
        self.matrix = matrix or [[1.0]]
        self.id = f"OP-{uuid.uuid4().hex[:12]}"
        self._validate()

    def _validate(self):
        n = len(self.matrix)
        assert all(len(row) == n for row in self.matrix), \
            "La matrice doit être carrée"

    @property
    def dimension(self) -> int:
        return len(self.matrix)

    def __matmul__(self, other: CognitiveOperator) -> CognitiveOperator:
        """Multiplication d'opérateurs (AB)."""
        assert self.dimension == other.dimension
        n = self.dimension
        result = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for k in range(n):
                if self.matrix[i][k]:
                    for j in range(n):
                        result[i][j] += self.matrix[i][k] * other.matrix[k][j]
        return CognitiveOperator(f"{self.name}∘{other.name}", result)

    def commutator(self, other: CognitiveOperator) -> list[list[float]]:
        """[A, B] = AB - BA."""
        ab = (self @ other).matrix
        ba = (other @ self).matrix
        n = self.dimension
        return [[ab[i][j] - ba[i][j] for j in range(n)] for i in range(n)]

    def commutator_norm(self, other: CognitiveOperator) -> float:
        """||[A, B]|| — norme du commutateur (mesure de non-commutativité)."""
        c = self.commutator(other)
        return math.sqrt(sum(sum(x*x for x in row) for row in c))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "dimension": self.dimension}


@dataclass(slots=True)
class SpectralTriple:
    """Triplet spectral (A, H, D) de Connes.
    
    A : C*-algèbre des opérations cognitives
    H : Espace de Hilbert des états cognitifs
    D : Opérateur de Dirac (différentiation cognitive)
    """
    algebra_dim: int
    hilbert_dim: int
    dirac_operator: list[list[float]] = field(default_factory=lambda: [[1.0]])
    delta: float = 0.0  # Constante de Planck cognitive

    def connes_distance(self, state_i: list[float],
                        state_j: list[float]) -> float:
        """Distance de Connes entre deux états cognitifs.
        
        d(φ, ψ) = sup{|φ(a) - ψ(a)| : a ∈ A, ||[D, a]|| ≤ 1}
        """
        n = min(len(state_i), len(state_j), self.algebra_dim)
        diffs = []
        for k in range(n):
            d = abs(state_i[k] - state_j[k])
            if d <= 1.0:
                diffs.append(d)
        return max(diffs) if diffs else 0.0


class NonCommutativeEngine:
    """Moteur de géométrie non-commutative cognitive.
    
    Gère les opérateurs cognitifs, leurs relations de commutation,
    et le triplet spectral (A, H, D) qui encode la géométrie
    de l'espace de pensée de CIEL.
    """

    def __init__(self):
        self.operators: dict[str, CognitiveOperator] = {}
        self.spectral_triple: SpectralTriple | None = None
        self.heisenberg_constant: float = 0.1  # ħ_CIEL
        self.network = LeaderNetwork()
        self._init_base_operators()

    def _init_base_operators(self):
        """Crée les opérateurs fondamentaux P, A, S."""
        # Opérateur de Perception
        self.create_operator("Perception", [
            [0.8, 0.2],
            [0.1, 0.9],
        ])
        # Opérateur d'Analyse
        self.create_operator("Analyse", [
            [0.9, 0.1],
            [0.3, 0.7],
        ])
        # Opérateur de Synthèse
        self.create_operator("Synthese", [
            [0.7, 0.3],
            [0.2, 0.8],
        ])
        # Initialiser le triplet spectral
        self.spectral_triple = SpectralTriple(
            algebra_dim=3,
            hilbert_dim=4,
            dirac_operator=[[1.0, 0.0], [0.0, 1.0]],
            delta=self.heisenberg_constant,
        )

    def create_operator(self, name: str,
                        matrix: list[list[float]]) -> CognitiveOperator:
        op = CognitiveOperator(name, matrix)
        self.operators[op.id] = op
        self.network.emit("noncomm.operator_created",
                          {"id": op.id, "name": name,
                           "dim": op.dimension})
        return op

    def measure_commutation(self, op_a_id: str,
                            op_b_id: str) -> dict:
        """Mesure [A, B] pour deux opérateurs."""
        a = self.operators.get(op_a_id)
        b = self.operators.get(op_b_id)
        if not a or not b:
            return {"error": "Opérateur inconnu"}
        norm = a.commutator_norm(b)
        return {
            "operator_a": a.name,
            "operator_b": b.name,
            "commutator_norm": norm,
            "commutes": norm < 0.01,
            "heisenberg_relation": norm >= self.heisenberg_constant,
        }

    def measure_state_distance(self, state_i: list[float],
                                state_j: list[float]) -> float:
        """Mesure la distance de Connes entre états."""
        if not self.spectral_triple:
            return 0.0
        return self.spectral_triple.connes_distance(state_i, state_j)

    def uncertainty(self, op_a_id: str, op_b_id: str) -> float:
        """Relation d'incertitude : ΔA · ΔB ≥ ½ |⟨[A,B]⟩|."""
        result = self.measure_commutation(op_a_id, op_b_id)
        if "error" in result:
            return 0.0
        return result["commutator_norm"] / 2

    def get_stats(self) -> dict:
        return {
            "operators": len(self.operators),
            "algebra_dim": self.spectral_triple.algebra_dim
                           if self.spectral_triple else 0,
            "hilbert_dim": self.spectral_triple.hilbert_dim
                           if self.spectral_triple else 0,
            "hc_constant": self.heisenberg_constant,
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create_operator":
            op = self.create_operator(
                input_data.get("name", "?"),
                input_data.get("matrix", [[1.0]]),
            )
            return {"status": "ok", "operator": op.to_dict()}
        elif action == "commute":
            return {"status": "ok",
                    "result": self.measure_commutation(
                        input_data.get("a", ""),
                        input_data.get("b", ""),
                    )}
        elif action == "distance":
            d = self.measure_state_distance(
                input_data.get("state_i", [0.0]),
                input_data.get("state_j", [1.0]),
            )
            return {"status": "ok", "connes_distance": d}
        return {"status": "ok", "operators": len(self.operators)}
