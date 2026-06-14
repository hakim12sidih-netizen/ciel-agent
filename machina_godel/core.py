from __future__ import annotations

import copy
import hashlib
import pickle
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, NamedTuple

import numpy as np


class ProofState(Enum):
    SEARCHING = auto()
    FOUND_PROOF = auto()
    REWRITING = auto()
    VERIFIED = auto()
    FAILED = auto()


class AxiomSchema(Enum):
    PEANO_ARITHMETIC = auto()
    ZFC = auto()
    CUSTOM = auto()


class Formula(NamedTuple):
    connective: str
    args: tuple[Formula | str, ...]

    def __repr__(self) -> str:
        if len(self.args) == 1:
            return f"{self.connective}({self.args[0]})"
        return f"({self.args[0]} {self.connective} {self.args[1]})"


class UndecidableProposition(NamedTuple):
    formula: Formula
    detected_at_step: int
    reason: str


TheoremProver = Callable[[list[Formula], Formula], bool]


@dataclass(slots=True)
class Checkpoint:
    state_hash: str
    code_snapshot: str
    theorem_cache: dict[int, bool]
    utility_estimate: float


@dataclass(slots=True)
class GödelMachine:
    axioms: list[Formula] = field(default_factory=list)
    theorems: dict[int, bool] = field(default_factory=dict)
    proof_state: ProofState = ProofState.SEARCHING
    axiom_schema: AxiomSchema = AxiomSchema.PEANO_ARITHMETIC
    utility_discount: float = 0.95
    current_code: str = field(default_factory=lambda: "")
    checkpoints: list[Checkpoint] = field(default_factory=list)
    undecidable_propositions: list[UndecidableProposition] = field(default_factory=list)
    max_proof_depth: int = 100
    _prover: TheoremProver | None = None

    def __post_init__(self) -> None:
        if not self.axioms:
            self.axioms = self._default_axioms()
        if not self.current_code:
            import inspect
            self.current_code = inspect.getsource(type(self))

    def _default_axioms(self) -> list[Formula]:
        if self.axiom_schema == AxiomSchema.PEANO_ARITHMETIC:
            return [
                Formula("∀", ("n", Formula("=", ("0", "s(n)")))),
                Formula("∀", ("n", Formula("=", ("n", "n")))),
                Formula("∀∀", (Formula("→", ("n=m", "s(n)=s(m)")),)),
            ]
        if self.axiom_schema == AxiomSchema.ZFC:
            return [
                Formula("∀∀", (Formula("↔", ("x=y", "∀(z∈x ↔ z∈y)")),)),
                Formula("∀", (Formula("∃", ("y", Formula("∀", ("x", Formula("¬", ("x∈y",)))))),)),
            ]
        return []

    def set_prover(self, prover: TheoremProver) -> None:
        self._prover = prover

    def forward_chain(self, goals: list[Formula], max_depth: int | None = None) -> list[Formula]:
        derived: list[Formula] = []
        depth = max_depth or self.max_proof_depth
        working = list(self.axioms)
        seen: set[Formula] = set()

        for _ in range(depth):
            new: list[Formula] = []
            for a in working:
                for b in working:
                    if a is b:
                        continue
                    resolved = self._resolve(a, b)
                    if resolved is not None and resolved not in seen:
                        seen.add(resolved)
                        new.append(resolved)
                        derived.append(resolved)
            if not new:
                break
            working.extend(new)

            if goals and all(g in derived for g in goals):
                break

        return derived

    def _resolve(self, a: Formula, b: Formula) -> Formula | None:
        if a.connective == "→" and a.args[0] == b:
            return a.args[1] if isinstance(a.args[1], Formula) else None
        return None

    def resolution_prove(self, goal: Formula) -> bool:
        clauses = list(self.axioms)
        negated = Formula("¬", (goal,))
        clauses.append(negated)
        derived: set[Formula] = set(clauses)

        for _ in range(self.max_proof_depth):
            new_clauses: set[Formula] = set()
            clauses_list = list(derived)
            for i, ci in enumerate(clauses_list):
                for cj in clauses_list[i + 1:]:
                    resolvent = self._resolve(ci, cj)
                    if resolvent is not None:
                        if self._is_empty_clause(resolvent):
                            return True
                        new_clauses.add(resolvent)
            if not new_clauses:
                return False
            derived.update(new_clauses)
        return False

    def _is_empty_clause(self, f: Formula) -> bool:
        return f.connective == "⊥"

    def theorem_prover(self, formula: Formula) -> bool:
        if self._prover is not None:
            return self._prover(self.axioms, formula)
        return self.resolution_prove(formula)

    def prove(self, formula: Formula) -> bool:
        h = hash(formula)
        if h in self.theorems:
            return self.theorems[h]

        known_undecidable = any(u.formula == formula for u in self.undecidable_propositions)
        if known_undecidable:
            return False

        result = self.theorem_prover(formula)
        self.theorems[h] = result
        return result

    def utility(self, state: dict[str, Any]) -> float:
        reward = 0.0
        if "immediate_reward" in state:
            reward += float(state["immediate_reward"])
        if "future_states" in state:
            future = state["future_states"]
            for i, s in enumerate(future):
                r = float(s.get("reward", 0.0))
                reward += (self.utility_discount ** (i + 1)) * r
        return reward

    def expected_utility_gain(self, current_state: dict[str, Any],
                              proposed_rewrite: str) -> float:
        current_u = self.utility(current_state)
        sim_state = dict(current_state)
        sim_state["code_snapshot"] = proposed_rewrite
        new_u = self.utility(sim_state)
        return new_u - current_u

    def prove_self_modification(self, new_code: str) -> bool:
        current_u_formula = Formula("utility_gain", (Formula("code", (self.current_code,)),
                                                     Formula("code", (new_code,))))
        if not self.prove(current_u_formula):
            return False
        safety_formula = Formula("safe", (Formula("rewrite", (new_code,)),))
        return self.prove(safety_formula)

    def create_checkpoint(self) -> Checkpoint:
        snap = Checkpoint(
            state_hash=hashlib.sha256(
                pickle.dumps((self.axioms, list(self.theorems.keys()), self.proof_state))
            ).hexdigest(),
            code_snapshot=self.current_code,
            theorem_cache=dict(self.theorems),
            utility_estimate=self.utility({"immediate_reward": 0.0, "future_states": []}),
        )
        self.checkpoints.append(snap)
        return snap

    def rollback(self, checkpoint: Checkpoint | None = None) -> bool:
        if not self.checkpoints:
            return False
        target = checkpoint if checkpoint is not None else self.checkpoints[-1]
        if target not in self.checkpoints:
            return False
        self.current_code = target.code_snapshot
        self.theorems = dict(target.theorem_cache)
        self.proof_state = ProofState.SEARCHING
        return True

    def execute_rewrite(self, new_code: str) -> bool:
        if not self.prove_self_modification(new_code):
            self.proof_state = ProofState.FAILED
            return False
        cp = self.create_checkpoint()
        self.proof_state = ProofState.REWRITING
        try:
            old_code = self.current_code
            exec(compile(new_code, "<rewrite>", "exec"), globals())
            self.current_code = new_code
            self.proof_state = ProofState.VERIFIED
            return True
        except Exception:
            self.rollback(cp)
            self.proof_state = ProofState.FAILED
            return False

    def detect_godel_sentence(self, formula: Formula) -> bool:
        def self_referential(f: Formula) -> bool:
            if isinstance(f.args, tuple | list):
                for arg in f.args:
                    if isinstance(arg, Formula) and self_referential(arg):
                        return True
                    if isinstance(arg, str) and arg == "self":
                        return True
            return False

        if not self_referential(formula):
            return False

        provable = self.prove(formula)
        neg_provable = self.prove(Formula("¬", (formula,)))

        if not provable and not neg_provable:
            self.undecidable_propositions.append(
                UndecidableProposition(formula, len(self.theorems),
                                      "Gödel sentence detected: neither P nor ¬P is provable")
            )
            return True
        return False

    def is_incompleteness_aware(self) -> bool:
        return len(self.undecidable_propositions) > 0

    def list_undecidable(self) -> list[UndecidableProposition]:
        return list(self.undecidable_propositions)

    def self_improve_step(self, state: dict[str, Any],
                          candidate_rewrites: list[str]) -> bool:
        self.proof_state = ProofState.SEARCHING
        best_rewrite: str | None = None
        best_gain = -np.inf

        for rewrite in candidate_rewrites:
            gain = self.expected_utility_gain(state, rewrite)
            if gain > best_gain and self.prove_self_modification(rewrite):
                best_gain = gain
                best_rewrite = rewrite

        if best_rewrite is not None and best_gain > 0:
            return self.execute_rewrite(best_rewrite)

        self.proof_state = ProofState.FAILED
        return False
