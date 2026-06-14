from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.logics.core import Formula, FormulaType, LogicSystem, ClassicalLogic


class RepresentationType(Enum):
    SYMBOLIC = "symbolic"
    SUBSYMBOLIC = "subsymbolic"
    HYBRID = "hybrid"


@dataclass(slots=True)
class Symbol:
    name: str
    arity: int = 0
    args: list[Any] = field(default_factory=list)
    embedding: list[float] | None = None
    groundings: list[str] = field(default_factory=list)  # sensorimotor anchors

    def to_formula(self) -> Formula:
        if not self.args:
            return Formula(FormulaType.ATOM, (self.name,))
        inner = tuple(a if isinstance(a, Formula) else Formula(FormulaType.ATOM, (str(a),)) for a in self.args)
        return Formula(FormulaType.ATOM, (self.name,) + inner)


@dataclass(slots=True)
class Concept:
    id: str
    name: str
    symbols: list[Symbol] = field(default_factory=list)
    prototype: list[float] = field(default_factory=list)  # subsymbolic prototype
    exemplars: list[list[float]] = field(default_factory=list)
    abstraction_level: int = 0

    def distance(self, vector: list[float]) -> float:
        if not self.prototype or not vector:
            return 1.0
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(self.prototype, vector))) / math.sqrt(len(self.prototype))

    def update_prototype(self) -> None:
        if not self.exemplars:
            return
        dims = len(self.exemplars[0])
        self.prototype = [sum(e[i] for e in self.exemplars) / len(self.exemplars) for i in range(dims)]

    def add_exemplar(self, vector: list[float]) -> None:
        self.exemplars.append(vector)
        self.update_prototype()


class SymbolGrounding:
    """Grounding symbolique — lie les symboles aux représentations subsymboliques."""

    def __init__(self, dim: int = 64):
        self.dim = dim
        self.grounding_map: dict[str, list[float]] = {}
        self._grounding_fn: Callable[[str], list[float]] | None = None

    def set_grounding_fn(self, fn: Callable[[str], list[float]]) -> None:
        self._grounding_fn = fn

    def ground(self, symbol: str, vector: list[float] | None = None) -> list[float]:
        if vector is not None:
            self.grounding_map[symbol] = vector
            return vector
        if symbol in self.grounding_map:
            return self.grounding_map[symbol]
        if self._grounding_fn:
            vec = self._grounding_fn(symbol)
            self.grounding_map[symbol] = vec
            return vec
        vec = [random.gauss(0, 0.1) for _ in range(self.dim)]
        self.grounding_map[symbol] = vec
        return vec

    def similarity(self, a: str, b: str) -> float:
        va = self.ground(a)
        vb = self.ground(b)
        dot = sum(x * y for x, y in zip(va, vb))
        na = math.sqrt(sum(x * x for x in va))
        nb = math.sqrt(sum(y * y for y in vb))
        if na * nb == 0:
            return 0.0
        return max(-1.0, min(1.0, dot / (na * nb)))


class NeuralSymbolicBridge:
    """Pont neuro-symbolique — traduit entre réseaux neuronaux et logique."""

    def __init__(self, logic: LogicSystem | None = None):
        self.logic = logic or ClassicalLogic()
        self.grounding = SymbolGrounding()
        self.concepts: dict[str, Concept] = {}
        self._neural_forward: Callable[[list[float]], list[float]] | None = None

    def set_neural_forward(self, fn: Callable[[list[float]], list[float]]) -> None:
        self._neural_forward = fn

    def neural_forward(self, input_vec: list[float]) -> list[float]:
        if self._neural_forward:
            return self._neural_forward(input_vec)
        return [v * 0.5 + 0.1 for v in input_vec]

    def symbolize(self, vector: list[float], label: str | None = None) -> Symbol:
        name = label or f"sym_{len(self.grounding.grounding_map)}"
        sym = Symbol(name=name, embedding=vector)
        self.grounding.ground(name, vector)
        return sym

    def evaluate_symbolic(self, symbol: Symbol) -> bool:
        formula = symbol.to_formula()
        return self.logic.evaluate(formula)

    def concept_from_exemplars(self, name: str, vectors: list[list[float]]) -> Concept:
        concept = Concept(id=name, name=name, exemplars=vectors)
        concept.update_prototype()
        self.concepts[name] = concept
        return concept

    def classify(self, vector: list[float]) -> str | None:
        best_name = None
        best_dist = float("inf")
        for cname, concept in self.concepts.items():
            d = concept.distance(vector)
            if d < best_dist:
                best_dist = d
                best_name = cname
        return best_name

    def symbol_to_vector(self, symbol: Symbol) -> list[float]:
        if symbol.embedding:
            return symbol.embedding
        emb = self.grounding.ground(symbol.name)
        symbol.embedding = emb
        return emb


class HybridReasoner:
    """Raisonnement hybride — combine inférence symbolique et subsymbolique."""

    def __init__(self, bridge: NeuralSymbolicBridge | None = None):
        self.bridge = bridge or NeuralSymbolicBridge()
        self.confidence_threshold: float = 0.6

    def reason_hybrid(self, premises: list[Symbol], target: Symbol) -> tuple[bool, float]:
        """Hybrid reasoning: symbolic inference + neural confidence."""
        symbolic_result = all(self.bridge.evaluate_symbolic(p) for p in premises)
        neural_confidence = 0.5
        if premises and target.embedding:
            combined = [0.0] * len(target.embedding)
            for p in premises:
                if p.embedding:
                    for i in range(len(combined)):
                        combined[i] += p.embedding[i] / len(premises)
            output = self.bridge.neural_forward(combined)
            if target.embedding:
                sim = sum(a * b for a, b in zip(output, target.embedding))
                n_a = math.sqrt(sum(x * x for x in output))
                n_b = math.sqrt(sum(x * x for x in target.embedding))
                neural_confidence = sim / (n_a * n_b) if n_a * n_b > 0 else 0.0
                neural_confidence = max(0.0, min(1.0, neural_confidence))
        combined_conf = 0.6 * (1.0 if symbolic_result else 0.0) + 0.4 * neural_confidence
        return combined_conf >= self.confidence_threshold, combined_conf

    def abduce(self, observation: Symbol, background_knowledge: list[Formula]) -> list[Formula]:
        """Abduction — find best explanation for observation."""
        candidates: list[tuple[Formula, float]] = []
        for bk in background_knowledge:
            if bk.type == FormulaType.IMPLICATION and len(bk.args) == 2:
                consequent = bk.args[1]
                antecedent = bk.args[0]
                if str(consequent) == str(observation.to_formula()):
                    score = random.uniform(0.3, 0.9)
                    candidates.append((antecedent, score))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in candidates[:3]]


class AbstractionEngine:
    """Moteur d'abstraction — apprentissage de concepts de haut niveau."""

    def __init__(self):
        self.layers: list[list[Concept]] = []
        self._abstraction_fn: Callable[[list[Concept]], Concept] | None = None

    def set_abstraction_fn(self, fn: Callable[[list[Concept]], Concept]) -> None:
        self._abstraction_fn = fn

    def abstract(self, concepts: list[Concept], name: str) -> Concept:
        if self._abstraction_fn:
            return self._abstraction_fn(concepts)
        if not concepts:
            return Concept(id=name, name=name)
        dims = len(concepts[0].prototype)
        avg_proto = [sum(c.prototype[i] for c in concepts) / len(concepts) for i in range(dims)] if dims > 0 else []
        abstracted = Concept(id=name, name=name, prototype=avg_proto, abstraction_level=concepts[0].abstraction_level + 1)
        while len(self.layers) <= abstracted.abstraction_level:
            self.layers.append([])
        self.layers[abstracted.abstraction_level].append(abstracted)
        return abstracted

    def get_layer(self, level: int) -> list[Concept]:
        if level < len(self.layers):
            return self.layers[level]
        return []


class NeuroSymbolicNetwork:
    """Réseau neuro-symbolique intégré — coeur de CIEL Phase 10."""

    def __init__(self, input_dim: int = 64):
        self.input_dim = input_dim
        self.bridge = NeuralSymbolicBridge()
        self.reasoner = HybridReasoner(self.bridge)
        self.abstraction = AbstractionEngine()
        self.symbols: dict[str, Symbol] = {}
        self._processors: list[Callable[[Any], Any]] = []

    def register_processor(self, processor: Callable[[Any], Any]) -> None:
        self._processors.append(processor)

    def create_symbol(self, name: str, vector: list[float] | None = None) -> Symbol:
        sym = Symbol(name=name)
        if vector:
            sym.embedding = vector
            self.bridge.grounding.ground(name, vector)
        self.symbols[name] = sym
        return sym

    def create_concept(self, name: str, vectors: list[list[float]]) -> Concept:
        return self.bridge.concept_from_exemplars(name, vectors)

    def forward(self, input_vec: list[float]) -> dict[str, Any]:
        vec = self.bridge.neural_forward(input_vec)
        sym = self.bridge.symbolize(vec)
        concept = self.abstraction.abstract([Concept(id="in", name="input", prototype=vec)], "abstrait")
        output = {
            "vector": vec,
            "symbol": sym,
            "concept": concept,
            "class": self.bridge.classify(vec),
        }
        for p in self._processors:
            p(output)
        return output

    def train_concept(self, name: str, positive: list[list[float]], negative: list[list[float]]) -> Concept:
        concept = self.create_concept(name, positive)
        return concept

    def reason(self, premises: list[Symbol], target: Symbol) -> tuple[bool, float]:
        return self.reasoner.reason_hybrid(premises, target)

    def abduce(self, observation: Symbol, background: list[Formula]) -> list[Formula]:
        return self.reasoner.abduce(observation, background)

    def grounding_similarity(self, a: str, b: str) -> float:
        return self.bridge.grounding.similarity(a, b)
