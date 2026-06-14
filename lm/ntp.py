from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ciel.logics.core import Formula, FormulaType, LogicSystem


@dataclass(slots=True)
class Theorem:
    formula: Formula
    proof_steps: list[str] = field(default_factory=list)
    confidence: float = 0.0
    is_proved: bool = False
    proof_depth: int = 0


class NeuralTheoremProver:
    """Neural Theorem Proving — prouvabilité neuronale guidée.

    Utilise un modèle de scoring (simulé) pour guider la recherche
    de preuves dans un espace logique.
    """

    def __init__(
        self,
        logic: LogicSystem | None = None,
        max_depth: int = 10,
        beam_width: int = 5,
    ) -> None:
        self.logic = logic
        self.max_depth = max_depth
        self.beam_width = beam_width
        self._scorer: Callable[[Formula, int], float] | None = None
        self._expander: Callable[[Formula], list[Formula]] | None = None
        self.theorems: list[Theorem] = []

    def set_scorer(self, scorer: Callable[[Formula, int], float]) -> None:
        self._scorer = scorer

    def set_expander(self, expander: Callable[[Formula], list[Formula]]) -> None:
        self._expander = expander

    def score(self, formula: Formula, depth: int) -> float:
        if self._scorer:
            return self._scorer(formula, depth)
        return 1.0 / (1.0 + depth * 0.2 + random.random() * 0.1)

    def expand(self, formula: Formula) -> list[Formula]:
        """Generate candidate sub-goals / proof steps."""
        if self._expander:
            return self._expander(formula)
        candidates: list[Formula] = []
        if formula.type == FormulaType.IMPLICATION and len(formula.args) == 2:
            candidates.append(formula.args[1])
            candidates.append(Formula(FormulaType.NEGATION, [formula.args[0]]))
        if formula.type == FormulaType.CONJUNCTION:
            for a in formula.args:
                candidates.append(a)
        if formula.type == FormulaType.DISJUNCTION:
            candidates.append(formula.args[0])
        return candidates[:3]

    def prove(
        self,
        formula: Formula,
        context: list[Formula] | None = None,
        beam: bool = True,
    ) -> Theorem:
        theorem = Theorem(formula=formula, proof_steps=[])
        if beam:
            return self._beam_search(formula, theorem)
        return self._dfs_prove(formula, theorem, set(), 0)

    def _beam_search(self, formula: Formula, theorem: Theorem) -> Theorem:
        beam: list[tuple[Formula, list[str], float, int]] = [(formula, [], 0.0, 0)]
        best_conf = 0.0
        best_proof: list[str] = []

        for _ in range(self.max_depth):
            candidates: list[tuple[Formula, list[str], float, int]] = []
            for f, steps, conf, depth in beam:
                if self.logic and self.logic.evaluate(f):
                    theorem.is_proved = True
                    theorem.proof_steps = steps + ["✓ prouvé"]
                    theorem.confidence = conf + 1.0
                    return theorem
                expansions = self.expand(f)
                for ef in expansions:
                    s = self.score(ef, depth + 1)
                    new_steps = steps + [f"d^{depth}: {f} → {ef}"]
                    candidates.append((ef, new_steps, conf + s, depth + 1))
                    if s > best_conf:
                        best_conf = s
                        best_proof = new_steps
            if not candidates:
                break
            candidates.sort(key=lambda x: x[2] / (x[3] + 1), reverse=True)
            beam = candidates[:self.beam_width]

        theorem.is_proved = False
        theorem.proof_steps = best_proof or ["Aucune preuve trouvée"]
        theorem.confidence = best_conf / max(len(best_proof), 1)
        return theorem

    def _dfs_prove(
        self,
        formula: Formula,
        theorem: Theorem,
        visited: set[str],
        depth: int,
    ) -> Theorem:
        if depth > self.max_depth:
            theorem.is_proved = False
            return theorem
        fstr = str(formula)
        if fstr in visited:
            theorem.is_proved = False
            return theorem
        visited.add(fstr)

        if self.logic and self.logic.evaluate(formula):
            theorem.is_proved = True
            theorem.proof_steps.append(f"d^{depth}: ✓ {formula}")
            theorem.confidence += 1.0 / (1.0 + depth * 0.1)
            return theorem

        expansions = self.expand(formula)
        for ef in expansions:
            theorem.proof_steps.append(f"d^{depth}: {formula} → {ef}")
            result = self._dfs_prove(ef, theorem, visited, depth + 1)
            if result.is_proved:
                return result

        theorem.is_proved = False
        return theorem

    def batch_prove(self, formulas: list[Formula]) -> list[Theorem]:
        self.theorems = []
        for f in formulas:
            self.theorems.append(self.prove(f))
        return self.theorems

    def proved_count(self) -> int:
        return sum(1 for t in self.theorems if t.is_proved)

    def average_confidence(self) -> float:
        if not self.theorems:
            return 0.0
        return sum(t.confidence for t in self.theorems) / len(self.theorems)
