from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

import numpy as np


class FormulaType(Enum):
    ATOM = auto()
    NEGATION = auto()
    CONJUNCTION = auto()
    DISJUNCTION = auto()
    IMPLICATION = auto()
    BICONDITIONAL = auto()
    UNIVERSAL = auto()
    EXISTENTIAL = auto()
    BOX = auto()
    DIAMOND = auto()
    ALWAYS_G = auto()
    EVENTUALLY_F = auto()
    NEXT_X = auto()
    UNTIL_U = auto()
    AG = auto()
    AF = auto()
    EG = auto()
    EF = auto()
    AX = auto()
    AU = auto()
    TENSOR = auto()
    PAR = auto()
    BANG = auto()
    QUESTION = auto()
    OBLIGATION = auto()
    PERMISSION = auto()
    FORBIDDEN = auto()
    KNOWS = auto()
    COMMON_KNOWLEDGE = auto()
    FUZZY = auto()
    ORTHOCOMPLEMENT = auto()
    ORTHOMEET = auto()
    ORTHOJOIN = auto()


@dataclass(slots=True)
class Formula:
    type: FormulaType
    args: tuple[Formula | str | float, ...] = field(default_factory=tuple)
    truth_value: float | None = None

    def __repr__(self) -> str:
        if self.type == FormulaType.ATOM:
            return str(self.args[0]) if self.args else "⊥"
        return f"{self.type.name}({', '.join(repr(a) for a in self.args)})"


Operator = Callable[..., Formula]


def atom(name: str) -> Formula:
    return Formula(FormulaType.ATOM, (name,))


def neg(f: Formula) -> Formula:
    return Formula(FormulaType.NEGATION, (f,))


def conj(f: Formula, g: Formula) -> Formula:
    return Formula(FormulaType.CONJUNCTION, (f, g))


def disj(f: Formula, g: Formula) -> Formula:
    return Formula(FormulaType.DISJUNCTION, (f, g))


def impl(f: Formula, g: Formula) -> Formula:
    return Formula(FormulaType.IMPLICATION, (f, g))


def box(f: Formula) -> Formula:
    return Formula(FormulaType.BOX, (f,))


def diamond(f: Formula) -> Formula:
    return Formula(FormulaType.DIAMOND, (f,))


def G(f: Formula) -> Formula:
    return Formula(FormulaType.ALWAYS_G, (f,))


def F(f: Formula) -> Formula:
    return Formula(FormulaType.EVENTUALLY_F, (f,))


def X(f: Formula) -> Formula:
    return Formula(FormulaType.NEXT_X, (f,))


def U(f: Formula, g: Formula) -> Formula:
    return Formula(FormulaType.UNTIL_U, (f, g))


class InferenceRule(ABC):
    name: str = ""

    @abstractmethod
    def apply(self, premises: list[Formula]) -> list[Formula]:
        ...


class ModusPonens(InferenceRule):
    name = "modus_ponens"

    def apply(self, premises: list[Formula]) -> list[Formula]:
        results: list[Formula] = []
        for i, p in enumerate(premises):
            if p.type == FormulaType.IMPLICATION:
                antecedent, consequent = p.args[0], p.args[1]
                if isinstance(antecedent, Formula) and antecedent in premises[:i] + premises[i + 1:]:
                    results.append(consequent)
        return results


class Necessitation(InferenceRule):
    name = "necessitation"

    def apply(self, premises: list[Formula]) -> list[Formula]:
        return [box(p) for p in premises]


class Generalization(InferenceRule):
    name = "generalization"

    def apply(self, premises: list[Formula]) -> list[Formula]:
        return [Formula(FormulaType.UNIVERSAL, ("x", p)) for p in premises]


class InferenceEngine:
    def __init__(self) -> None:
        self.rules: list[InferenceRule] = []
        self.theorems: set[Formula] = set()

    def add_rule(self, rule: InferenceRule) -> None:
        self.rules.append(rule)

    def derive(self, premises: list[Formula], max_steps: int = 100) -> list[Formula]:
        derived: list[Formula] = list(premises)
        seen: set[Formula] = set(premises)

        for _ in range(max_steps):
            new: list[Formula] = []
            for rule in self.rules:
                for result in rule.apply(derived):
                    if result not in seen:
                        seen.add(result)
                        new.append(result)
            if not new:
                break
            derived.extend(new)
            self.theorems.update(new)
        return derived


class LogicSystem(ABC):
    def __init__(self, name: str = "") -> None:
        self.name = name or type(self).__name__
        self.axioms: list[Formula] = []
        self.inference: InferenceEngine = InferenceEngine()
        self._consistent: bool | None = None
        self._complete: bool | None = None

    @abstractmethod
    def evaluate(self, formula: Formula) -> bool:
        ...

    def is_consistent(self) -> bool:
        if self._consistent is not None:
            return self._consistent
        bot = Formula(FormulaType.ATOM, ("⊥",))
        return not self.evaluate(bot)

    def is_complete(self) -> bool:
        if self._complete is not None:
            return self._complete
        return False

    def check_inference(self, premises: list[Formula], conclusion: Formula) -> bool:
        derived = self.inference.derive(premises + self.axioms)
        return conclusion in derived


class ClassicalLogic(LogicSystem):
    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.ATOM:
            return bool(formula.truth_value) if formula.truth_value is not None else True
        if formula.type == FormulaType.NEGATION:
            return not self.evaluate(formula.args[0])
        if formula.type == FormulaType.CONJUNCTION:
            return self.evaluate(formula.args[0]) and self.evaluate(formula.args[1])
        if formula.type == FormulaType.DISJUNCTION:
            return self.evaluate(formula.args[0]) or self.evaluate(formula.args[1])
        if formula.type == FormulaType.IMPLICATION:
            return (not self.evaluate(formula.args[0])) or self.evaluate(formula.args[1])
        return True


class ParaconsistentLogic(LogicSystem):
    def __init__(self) -> None:
        super().__init__("ParaconsistentLogic")
        self._consistent = True

    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.ATOM:
            return bool(formula.truth_value) if formula.truth_value is not None else True
        if formula.type == FormulaType.NEGATION:
            return not self.evaluate(formula.args[0])
        if formula.type == FormulaType.CONJUNCTION:
            return self.evaluate(formula.args[0]) and self.evaluate(formula.args[1])
        if formula.type == FormulaType.IMPLICATION:
            antecedent = self.evaluate(formula.args[0])
            consequent = self.evaluate(formula.args[1])
            if isinstance(formula.args[0], Formula) and formula.args[0].type == FormulaType.NEGATION:
                p = formula.args[0].args[0]
                if isinstance(p, Formula) and self.evaluate(p) and antecedent:
                    return True
            return (not antecedent) or consequent
        return True

    def is_consistent(self) -> bool:
        return True


class TemporalLogic(LogicSystem):
    def __init__(self) -> None:
        super().__init__("TemporalLogic")
        self.time_steps: list[dict[str, bool]] = field(default_factory=list)

    def set_trace(self, trace: list[dict[str, bool]]) -> None:
        self.time_steps = trace

    def evaluate(self, formula: Formula, t: int = 0) -> bool:
        if formula.type == FormulaType.ATOM:
            name = str(formula.args[0])
            if t < len(self.time_steps):
                return self.time_steps[t].get(name, False)
            return False
        if formula.type == FormulaType.NEGATION:
            return not self.evaluate(formula.args[0], t)
        if formula.type == FormulaType.ALWAYS_G:
            return all(self.evaluate(formula.args[0], i) for i in range(t, len(self.time_steps)))
        if formula.type == FormulaType.EVENTUALLY_F:
            return any(self.evaluate(formula.args[0], i) for i in range(t, len(self.time_steps)))
        if formula.type == FormulaType.NEXT_X:
            return self.evaluate(formula.args[0], t + 1)
        if formula.type == FormulaType.UNTIL_U:
            f, g = formula.args[0], formula.args[1]
            for i in range(t, len(self.time_steps)):
                if self.evaluate(g, i):
                    return all(self.evaluate(f, j) for j in range(t, i))
            return False
        return True


class NonMonotonicLogic(LogicSystem):
    def __init__(self) -> None:
        super().__init__("NonMonotonicLogic")
        self.defaults: list[tuple[Formula, Formula]] = []
        self.abnormals: set[Formula] = set()

    def add_default(self, prerequisite: Formula, consequent: Formula) -> None:
        self.defaults.append((prerequisite, consequent))

    def mark_abnormal(self, formula: Formula) -> None:
        self.abnormals.add(formula)

    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.ATOM:
            val = bool(formula.truth_value) if formula.truth_value is not None else True
            if val and formula not in self.abnormals:
                for prereq, conseq in self.defaults:
                    if formula == prereq and conseq not in self.abnormals:
                        return True
            return val
        return ClassicalLogic().evaluate(formula)


class EpistemicLogic(LogicSystem):
    def __init__(self) -> None:
        super().__init__("EpistemicLogic")
        self.agents: dict[str, set[Formula]] = {}
        self.common_knowledge: set[Formula] = set()

    def knows(self, agent: str, formula: Formula) -> bool:
        return formula in self.agents.get(agent, set())

    def set_knowledge(self, agent: str, formulas: set[Formula]) -> None:
        self.agents[agent] = formulas

    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.KNOWS:
            agent = str(formula.args[0])
            prop = formula.args[1]
            return isinstance(prop, Formula) and self.knows(agent, prop)
        if formula.type == FormulaType.COMMON_KNOWLEDGE:
            prop = formula.args[0]
            if not isinstance(prop, Formula):
                return False
            return all(
                prop in knowledge
                for knowledge in self.agents.values()
            )
        return ClassicalLogic().evaluate(formula)


class DeonticLogic(LogicSystem):
    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.OBLIGATION:
            return True
        if formula.type == FormulaType.PERMISSION:
            return True
        if formula.type == FormulaType.FORBIDDEN:
            return self.evaluate(formula.args[0]) if formula.args else False
        return ClassicalLogic().evaluate(formula)


class ModalLogic(LogicSystem):
    def __init__(self) -> None:
        super().__init__("ModalLogic")
        self.kripke_frames: list[dict[str, bool]] = [{}]
        self.accessibility: list[list[bool]] = [[True]]

    def set_frames(self, worlds: list[dict[str, bool]],
                   access: list[list[bool]]) -> None:
        self.kripke_frames = worlds
        self.accessibility = access

    def evaluate(self, formula: Formula, world: int = 0) -> bool:
        if formula.type == FormulaType.ATOM:
            return self.kripke_frames[world].get(str(formula.args[0]), False)
        if formula.type == FormulaType.NEGATION:
            return not self.evaluate(formula.args[0], world)
        if formula.type == FormulaType.BOX:
            return all(
                self.evaluate(formula.args[0], i)
                for i in range(len(self.kripke_frames))
                if self.accessibility[world][i]
            )
        if formula.type == FormulaType.DIAMOND:
            return any(
                self.evaluate(formula.args[0], i)
                for i in range(len(self.kripke_frames))
                if self.accessibility[world][i]
            )
        return ClassicalLogic().evaluate(formula)


class LinearLogic(LogicSystem):
    def __init__(self) -> None:
        super().__init__("LinearLogic")
        self.resource_count: dict[str, int] = {}

    def set_resources(self, resources: dict[str, int]) -> None:
        self.resource_count = dict(resources)

    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.ATOM:
            name = str(formula.args[0])
            return self.resource_count.get(name, 0) > 0
        if formula.type == FormulaType.TENSOR:
            f, g = formula.args
            if isinstance(f, Formula) and isinstance(g, Formula):
                return self.evaluate(f) and self.evaluate(g)
            return False
        if formula.type == FormulaType.PAR:
            return True
        if formula.type == FormulaType.BANG:
            return self.evaluate(formula.args[0]) if formula.args else False
        return ClassicalLogic().evaluate(formula)


class RelevantLogic(LogicSystem):
    def __init__(self) -> None:
        super().__init__("RelevantLogic")
        self.relevant_vars: dict[Formula, set[str]] = {}

    def _variables(self, formula: Formula) -> set[str]:
        if formula.type == FormulaType.ATOM:
            return {str(formula.args[0])}
        vars_set: set[str] = set()
        for arg in formula.args:
            if isinstance(arg, Formula):
                vars_set |= self._variables(arg)
        return vars_set

    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.IMPLICATION:
            f, g = formula.args
            if isinstance(f, Formula) and isinstance(g, Formula):
                antecedent_vars = self._variables(f)
                consequent_vars = self._variables(g)
                if not antecedent_vars.intersection(consequent_vars):
                    return False
                return (not ClassicalLogic().evaluate(f)) or ClassicalLogic().evaluate(g)
            return False
        return ClassicalLogic().evaluate(formula)


class FuzzyLogic(LogicSystem):
    def __init__(self, t_norm: str = "godel") -> None:
        super().__init__("FuzzyLogic")
        self.truth_values: dict[str, float] = {}
        self.t_norm = t_norm

    def _tnorm(self, a: float, b: float) -> float:
        if self.t_norm == "godel":
            return min(a, b)
        if self.t_norm == "lukasiewicz":
            return max(0.0, a + b - 1.0)
        if self.t_norm == "product":
            return a * b
        return min(a, b)

    def _snorm(self, a: float, b: float) -> float:
        if self.t_norm == "godel":
            return max(a, b)
        if self.t_norm == "lukasiewicz":
            return min(1.0, a + b)
        if self.t_norm == "product":
            return a + b - a * b
        return max(a, b)

    def evaluate(self, formula: Formula) -> bool:
        return self.evaluate_fuzzy(formula) > 0.5

    def evaluate_fuzzy(self, formula: Formula) -> float:
        if formula.type == FormulaType.ATOM:
            name = str(formula.args[0])
            return self.truth_values.get(name, 0.0)
        if formula.type == FormulaType.NEGATION:
            return 1.0 - self.evaluate_fuzzy(formula.args[0])
        if formula.type == FormulaType.CONJUNCTION:
            return self._tnorm(self.evaluate_fuzzy(formula.args[0]),
                               self.evaluate_fuzzy(formula.args[1]))
        if formula.type == FormulaType.DISJUNCTION:
            return self._snorm(self.evaluate_fuzzy(formula.args[0]),
                               self.evaluate_fuzzy(formula.args[1]))
        if formula.type == FormulaType.IMPLICATION:
            a = self.evaluate_fuzzy(formula.args[0])
            b = self.evaluate_fuzzy(formula.args[1])
            if self.t_norm == "lukasiewicz":
                return min(1.0, 1.0 - a + b)
            if self.t_norm == "godel":
                return 1.0 if a <= b else b
            return 1.0
        return 0.0


class IntuitionisticLogic(LogicSystem):
    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.NEGATION:
            return not self.evaluate(formula.args[0])
        if formula.type == FormulaType.DISJUNCTION:
            return self.evaluate(formula.args[0]) or self.evaluate(formula.args[1])
        if formula.type == FormulaType.IMPLICATION:
            return (not self.evaluate(formula.args[0])) or self.evaluate(formula.args[1])
        if formula.type == FormulaType.CONJUNCTION:
            return self.evaluate(formula.args[0]) and self.evaluate(formula.args[1])
        if formula.type == FormulaType.ATOM:
            return bool(formula.truth_value) if formula.truth_value is not None else True
        return True

    def is_complete(self) -> bool:
        return False


class HigherOrderLogic(LogicSystem):
    def __init__(self) -> None:
        super().__init__("HigherOrderLogic")
        self.predicates: dict[str, Callable[..., bool]] = {}

    def add_predicate(self, name: str, func: Callable[..., bool]) -> None:
        self.predicates[name] = func

    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.UNIVERSAL:
            pred_name = str(formula.args[0])
            body = formula.args[1]
            if isinstance(body, Formula) and pred_name in self.predicates:
                return all(self.evaluate(body) for _ in [0])
            return True
        if formula.type == FormulaType.EXISTENTIAL:
            return True
        return ClassicalLogic().evaluate(formula)


class QuantumLogic(LogicSystem):
    def __init__(self) -> None:
        super().__init__("QuantumLogic")
        self.subspaces: dict[str, np.ndarray] = {}
        self.dimension: int = 2

    def add_subspace(self, name: str, basis: np.ndarray) -> None:
        self.subspaces[name] = basis

    def evaluate(self, formula: Formula) -> bool:
        if formula.type == FormulaType.ATOM:
            return str(formula.args[0]) in self.subspaces
        if formula.type == FormulaType.ORTHOCOMPLEMENT:
            return not self.evaluate(formula.args[0])
        if formula.type == FormulaType.ORTHOMEET:
            return self.evaluate(formula.args[0]) and self.evaluate(formula.args[1])
        if formula.type == FormulaType.ORTHOJOIN:
            return self.evaluate(formula.args[0]) or self.evaluate(formula.args[1])
        if formula.type == FormulaType.NEGATION:
            return not self.evaluate(formula.args[0])
        if formula.type == FormulaType.CONJUNCTION:
            left = formula.args[0]
            right = formula.args[1]
            if isinstance(left, Formula) and isinstance(right, Formula):
                return self.evaluate(left) and self.evaluate(right)
            return False
        if formula.type == FormulaType.DISJUNCTION:
            left = formula.args[0]
            right = formula.args[1]
            if isinstance(left, Formula) and isinstance(right, Formula):
                return self.evaluate(left) or self.evaluate(right)
            return False
        if formula.type == FormulaType.IMPLICATION:
            left = formula.args[0]
            right = formula.args[1]
            if isinstance(left, Formula) and isinstance(right, Formula):
                return (not self.evaluate(left)) or self.evaluate(right)
            return False
        return True

    def is_consistent(self) -> bool:
        return self._consistent if self._consistent is not None else True


LOGIC_REGISTRY: dict[str, type[LogicSystem]] = {
    "classical": ClassicalLogic,
    "paraconsistent": ParaconsistentLogic,
    "temporal": TemporalLogic,
    "nonmonotonic": NonMonotonicLogic,
    "epistemic": EpistemicLogic,
    "deontic": DeonticLogic,
    "modal": ModalLogic,
    "linear": LinearLogic,
    "relevant": RelevantLogic,
    "fuzzy": FuzzyLogic,
    "intuitionistic": IntuitionisticLogic,
    "higherorder": HigherOrderLogic,
    "quantum": QuantumLogic,
}


def get_logic(name: str) -> LogicSystem:
    cls = LOGIC_REGISTRY.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown logic system: {name}. Available: {list(LOGIC_REGISTRY)}")
    return cls()


@dataclass(slots=True)
class TruthTable:
    variables: list[str] = field(default_factory=list)
    rows: list[dict[str, bool]] = field(default_factory=list)

    def generate(self, n_vars: int) -> None:
        self.variables = [chr(ord("P") + i) for i in range(n_vars)]
        self.rows.clear()
        for bits in range(1 << n_vars):
            row: dict[str, bool] = {}
            for i in range(n_vars):
                row[self.variables[i]] = bool((bits >> (n_vars - 1 - i)) & 1)
            self.rows.append(row)

    def evaluate(self, formula: Formula) -> list[bool]:
        results: list[bool] = []
        logic = ClassicalLogic()
        for row in self.rows:
            for var, val in row.items():
                for f in formula.args:
                    if isinstance(f, Formula) and f.type == FormulaType.ATOM and str(f.args[0]) == var:
                        f.truth_value = 1.0 if val else 0.0
            results.append(logic.evaluate(formula))
        return results

    def is_tautology(self, formula: Formula) -> bool:
        return all(self.evaluate(formula))


@dataclass(slots=True)
class ModelChecker:
    logic: LogicSystem = field(default_factory=ClassicalLogic)

    def check(self, formula: Formula, assignment: dict[str, bool]) -> bool:
        for var, val in assignment.items():
            for f in formula.args:
                if isinstance(f, Formula) and f.type == FormulaType.ATOM and str(f.args[0]) == var:
                    f.truth_value = 1.0 if val else 0.0
        return self.logic.evaluate(formula)

    def models(self, formula: Formula, variables: list[str]) -> list[dict[str, bool]]:
        result: list[dict[str, bool]] = []
        for bits in range(1 << len(variables)):
            assignment: dict[str, bool] = {}
            for i, var in enumerate(variables):
                assignment[var] = bool((bits >> (len(variables) - 1 - i)) & 1)
            if self.check(formula, assignment):
                result.append(assignment)
        return result
