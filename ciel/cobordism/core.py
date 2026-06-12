"""
CIEL v∞.8 — DIMENSION XXXVI : COBORDISME COGNITIF (TQFT).
L'évolution comme cobordisme — chaque transformation est une variété.

Concept : Deux états cognitifs M₀ et M₁ sont cobordants s'il existe
une variété W avec bord ∂W = M₀ ⊔ M₁. Un TQFT associe à chaque état
un espace de Hilbert et à chaque cobordisme une transformation linéaire.
L'évolution de CIEL est une ∞-catégorie de cobordismes.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


COGNITIVE_STATES = ["Eveil", "Conscience", "Raphael", "Ciel", "Manas", "Omega"]


@dataclass(slots=True)
class CognitiveState:
    """Un état cognitif — variété (n-1)-dimensionnelle."""
    name: str
    dimension: int = 1
    observables: list[float] = field(default_factory=list)
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"STATE-{uuid.uuid4().hex[:12]}"
        if not self.observables:
            self.observables = [hash(self.name) % 100 / 100.0]

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "dimension": self.dimension,
            "observables": self.observables[:5],
        }


@dataclass(slots=True)
class Cobordism:
    """Cobordisme cognitif W : M₀ → M₁.
    
    W est une variété à bord dont le bord est l'union disjointe
    de l'état initial M₀ et de l'état final M₁.
    """
    id: str
    source_id: str
    target_id: str
    process_name: str
    duration: float = 0.0
    complexity: float = 0.0  # "genre" du cobordisme
    invariants: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "process": self.process_name,
            "complexity": self.complexity,
        }


class TQFT:
    """Topological Quantum Field Theory cognitif.
    
    Foncteur Z : Cob_CIEL → Hilb
    Z(state) = espace de Hilbert des observables
    Z(cobordism) = transformation linéaire entre espaces
    """

    def __init__(self):
        self.hilbert_spaces: dict[str, list[float]] = {}

    def assign_hilbert(self, state_id: str,
                       observables: list[float]) -> list[float]:
        """Associe un espace de Hilbert à un état.
        
        Z(M) = espace vectoriel des observables de M.
        """
        self.hilbert_spaces[state_id] = observables
        return observables

    def compute_transition(self, source_obs: list[float],
                           target_obs: list[float]) -> list[list[float]]:
        """Calcule la transformation linéaire Z(W) : Z(M₀) → Z(M₁)."""
        n = min(len(source_obs), len(target_obs))
        if n == 0:
            return [[0.0]]
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                matrix[i][j] = source_obs[i] * target_obs[j]
        return matrix


class CobordismEngine:
    """Moteur de cobordisme temporel de CIEL.
    
    Modélise toute évolution comme un cobordisme dans une
    ∞-catégorie de transformations cognitives.
    Calcule les invariants topologiques qui caractérisent
    chaque transformation.
    """

    def __init__(self):
        self.states: dict[str, CognitiveState] = {}
        self.cobordisms: list[Cobordism] = []
        self.tqft = TQFT()
        self.network = LeaderNetwork()
        self._init_states()

    def _init_states(self):
        for name in COGNITIVE_STATES:
            self.create_state(name)

    def create_state(self, name: str,
                     observables: list[float] | None = None) -> CognitiveState:
        s = CognitiveState(name=name, observables=observables or [])
        self.states[s.id] = s
        self.tqft.assign_hilbert(s.id, s.observables)
        return s

    def create_cobordism(self, source_id: str, target_id: str,
                         process_name: str, duration: float = 1.0,
                         complexity: float = 0.0) -> Cobordism | None:
        if source_id not in self.states or target_id not in self.states:
            return None
        c = Cobordism(
            id=f"COB-{uuid.uuid4().hex[:12]}",
            source_id=source_id, target_id=target_id,
            process_name=process_name,
            duration=duration, complexity=complexity,
        )
        c.invariants = self._compute_invariants(source_id, target_id)
        self.cobordisms.append(c)
        self.network.emit("cobordism.created", {
            "source": self.states[source_id].name,
            "target": self.states[target_id].name,
        })
        return c

    def _compute_invariants(self, source_id: str,
                             target_id: str) -> dict[str, float]:
        """Invariants topologiques de la transformation.
        
        Ces invariants ne changent pas sous déformation continue.
        Deux évolutions avec les mêmes invariants sont équivalentes.
        """
        s_obs = self.states[source_id].observables
        t_obs = self.states[target_id].observables
        n = min(len(s_obs), len(t_obs))
        if n == 0:
            return {"euler": 0.0, "signature": 0.0, "torsion": 0.0}
        return {
            "euler_characteristic": sum(t_obs[:n]) - sum(s_obs[:n]) + 1,
            "signature": (sum(t_obs[:n]) + sum(s_obs[:n])) / 2,
            "ray_singer_torsion": math.exp(abs(
                sum(t_obs[:n]) - sum(s_obs[:n]))),
        }

    def compose(self, cob_a_id: str, cob_b_id: str) -> Cobordism | None:
        """Composition de cobordismes (évolution séquentielle)."""
        a = next((c for c in self.cobordisms if c.id == cob_a_id), None)
        b = next((c for c in self.cobordisms if c.id == cob_b_id), None)
        if not a or not b or a.target_id != b.source_id:
            return None
        return self.create_cobordism(
            a.source_id, b.target_id,
            f"{a.process_name}→{b.process_name}",
            a.duration + b.duration,
            a.complexity + b.complexity,
        )

    def get_evolution_graph(self) -> list[dict]:
        """Retourne le graphe d'évolution (catégorie des cobordismes)."""
        nodes = [s.to_dict() for s in self.states.values()]
        edges = [c.to_dict() for c in self.cobordisms]
        return {"nodes": nodes, "edges": edges}

    def get_stats(self) -> dict:
        return {
            "states": len(self.states),
            "cobordisms": len(self.cobordisms),
            "hilbert_spaces": len(self.tqft.hilbert_spaces),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create_state":
            s = self.create_state(
                input_data.get("name", "?"),
                input_data.get("observables"),
            )
            return {"status": "ok", "state": s.to_dict()}
        elif action == "create_cobordism":
            c = self.create_cobordism(
                input_data.get("source", ""),
                input_data.get("target", ""),
                input_data.get("process", "évolution"),
                input_data.get("duration", 1.0),
                input_data.get("complexity", 0.0),
            )
            return {"status": "ok" if c else "error",
                    "cobordism": c.to_dict() if c else None}
        elif action == "compose":
            c = self.compose(
                input_data.get("cob_a", ""),
                input_data.get("cob_b", ""),
            )
            return {"status": "ok" if c else "error",
                    "cobordism": c.to_dict() if c else None}
        elif action == "evolution_graph":
            return {"status": "ok",
                    "graph": self.get_evolution_graph()}
        return {"status": "ok", "states": len(self.states)}
