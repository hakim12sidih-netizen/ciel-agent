from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Generic, TypeVar

import numpy as np

T = TypeVar("T")


class QuineType(Enum):
    SOURCE_QUINE = auto()
    AST_QUINE = auto()
    SELF_REPRODUCING = auto()


@dataclass(slots=True)
class QuineProgram:
    source: str
    representation: str = ""
    quine_type: QuineType = QuineType.SOURCE_QUINE

    def output(self) -> str:
        if self.quine_type == QuineType.SOURCE_QUINE:
            return self.source
        return self.representation

    def is_quine(self) -> bool:
        return self.output() == str(self)

    def __str__(self) -> str:
        return f"QuineProgram({self.source[:40]}...)"

    def __repr__(self) -> str:
        return self.source


class SelfReproducingAutomaton(ABC):
    @abstractmethod
    def describe_self(self) -> str:
        ...

    @abstractmethod
    def construct_from(self, description: str) -> SelfReproducingAutomaton:
        ...

    def reproduce(self) -> SelfReproducingAutomaton:
        desc = self.describe_self()
        return self.construct_from(desc)

    def verify_reproduction(self, other: SelfReproducingAutomaton) -> bool:
        return type(self) is type(other) and self.describe_self() == other.describe_self()


@dataclass(slots=True)
class SimpleSelfReproducer(SelfReproducingAutomaton):
    payload: str = ""

    def describe_self(self) -> str:
        return self.payload

    def construct_from(self, description: str) -> SimpleSelfReproducer:
        return SimpleSelfReproducer(payload=description)


class RecursiveSelfImprovement:
    def __init__(self, base_program: str) -> None:
        self.generations: list[str] = [base_program]
        self.history: list[dict[str, Any]] = []

    def descend(self, transform: Callable[[str], str]) -> str:
        current = self.generations[-1]
        next_gen = transform(current)
        self.generations.append(next_gen)
        self.history.append({"step": len(self.generations) - 1, "direction": "descend"})
        return next_gen

    def ascend(self, transform: Callable[[str], str]) -> str:
        if len(self.generations) <= 1:
            raise ValueError("Cannot ascend: at root generation")
        current = self.generations[-1]
        parent = transform(current)
        self.generations.append(parent)
        self.history.append({"step": len(self.generations) - 1, "direction": "ascend"})
        return parent

    def n_generations(self) -> int:
        return len(self.generations)

    def complexity_sequence(self) -> list[float]:
        seq: list[float] = []
        for g in self.generations:
            seq.append(float(len(g)))
        return seq

    def estimated_complexity_growth(self) -> float:
        if len(self.generations) < 2:
            return 0.0
        lengths = [len(g) for g in self.generations]
        return float(np.mean(np.diff(lengths)))


@dataclass(slots=True)
class QuineHierarchy:
    levels: list[QuineProgram] = field(default_factory=list)

    def add_level(self, program: QuineProgram) -> None:
        self.levels.append(program)

    def meta_level(self, n: int) -> QuineProgram | None:
        try:
            return self.levels[n]
        except IndexError:
            return None

    def generate_meta_chain(self, base: str, depth: int) -> None:
        current = base
        self.levels.clear()
        for i in range(depth):
            meta_src = f"meta_{i}: {current}"
            qp = QuineProgram(source=meta_src, representation=f"L{i}", quine_type=QuineType.AST_QUINE)
            self.levels.append(qp)
            current = f"quote({meta_src})"

    def __len__(self) -> int:
        return len(self.levels)


@dataclass(slots=True)
class VonNeumannConstructor:
    tape: list[str] = field(default_factory=list)
    head_position: int = 0
    description: str = ""

    def load_description(self, desc: str) -> None:
        self.description = desc
        self.tape = list(desc)
        self.head_position = 0

    def read(self) -> str | None:
        if 0 <= self.head_position < len(self.tape):
            return self.tape[self.head_position]
        return None

    def write(self, symbol: str) -> None:
        if self.head_position >= len(self.tape):
            self.tape.append(symbol)
        else:
            self.tape[self.head_position] = symbol

    def move(self, direction: int) -> None:
        self.head_position = max(0, self.head_position + direction)

    def construct(self) -> VonNeumannConstructor:
        child = VonNeumannConstructor()
        desc = "".join(self.tape)
        child.load_description(desc)
        return child

    def universal_construction(self) -> bool:
        child = self.construct()
        return self.description == child.description


@dataclass(slots=True)
class FixedPointFinder(Generic[T]):
    domain: list[T] = field(default_factory=list)
    max_iterations: int = 100

    def find_fixed_point(self, f: Callable[[T], T], start: T) -> T | None:
        current = start
        seen: set[int] = set()

        for _ in range(self.max_iterations):
            h = hash(current)
            if h in seen:
                return current
            seen.add(h)
            nxt = f(current)
            if nxt == current:
                return current
            current = nxt
        return None

    def kleene_recursion(self, f: Callable[[Callable[[T], T]], Callable[[T], T]],
                         approx: Callable[[T], T] | None = None) -> Callable[[T], T]:
        def mock(_x: T) -> T:
            raise NotImplementedError

        current: Callable[[T], T] = approx if approx is not None else mock

        for _ in range(self.max_iterations):
            nxt = f(current)
            if nxt is current:
                return nxt
            current = nxt
        return current


@dataclass(slots=True)
class StrangeLoop:
    nodes: list[str] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)
    self_referential_cycles: list[list[str]] = field(default_factory=list)

    def add_edge(self, a: str, b: str) -> None:
        self.edges.append((a, b))
        if a not in self.nodes:
            self.nodes.append(a)
        if b not in self.nodes:
            self.nodes.append(b)

    def find_cycles(self) -> list[list[str]]:
        adj: dict[str, list[str]] = {n: [] for n in self.nodes}
        for a, b in self.edges:
            adj[a].append(b)

        cycles: list[list[str]] = []

        def dfs(node: str, path: list[str], visited: set[str]) -> None:
            if node in visited:
                idx = path.index(node)
                cycle = path[idx:]
                if cycle not in cycles:
                    cycles.append(cycle)
                return
            visited.add(node)
            path.append(node)
            for neighbor in adj.get(node, []):
                dfs(neighbor, path, visited)
            path.pop()
            visited.remove(node)

        for n in self.nodes:
            dfs(n, [], set())

        self.self_referential_cycles = cycles
        return cycles

    def is_strange_loop(self, node: str) -> bool:
        self.find_cycles()
        return any(node in cycle for cycle in self.self_referential_cycles)


@dataclass(slots=True)
class QuineGenerator:
    template: str = "lambda s: s + repr(s)"

    def generate_quine(self, payload: str = "") -> QuineProgram:
        if not payload:
            source = self.template
        else:
            source = f"(lambda p: lambda: p + repr(p))({payload!r})"
        return QuineProgram(source=source, representation=payload, quine_type=QuineType.SOURCE_QUINE)

    def generate_from_ast(self, ast_nodes: list[str]) -> QuineProgram:
        combined = "|".join(ast_nodes)
        source = f"Q({combined!r})"
        return QuineProgram(source=source, representation=combined, quine_type=QuineType.AST_QUINE)

    def verify_quine(self, program: QuineProgram) -> bool:
        try:
            return program.is_quine()
        except Exception:
            return False


@dataclass(slots=True)
class RecursiveEnrichment:
    initial_program: str = ""
    generations: list[str] = field(default_factory=list)
    complexity_metric: Callable[[str], float] = field(default=lambda s: float(len(s)))

    def __post_init__(self) -> None:
        if self.initial_program and not self.generations:
            self.generations = [self.initial_program]

    def apply_self(self, f: Callable[[str], str], n: int = 1) -> list[str]:
        current = self.generations[-1] if self.generations else self.initial_program
        for _ in range(n):
            current = f(current)
            self.generations.append(current)
        return self.generations

    def complexity_trace(self) -> list[float]:
        return [self.complexity_metric(g) for g in self.generations]

    def diversity(self) -> float:
        if len(self.generations) < 2:
            return 0.0
        unique = len(set(self.generations))
        return unique / len(self.generations)

    def compress(self, program: str) -> str:
        return hashlib.sha256(program.encode()).hexdigest()[:16]

    def enriched_programs(self) -> list[str]:
        return list(self.generations)
