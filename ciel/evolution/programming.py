from __future__ import annotations

import math
import random
import operator
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GPTree:
    value: str | float
    children: list[GPTree]
    arity: int = 0

    def __repr__(self) -> str:
        if not self.children:
            return str(self.value)
        return f"({self.value} {' '.join(repr(c) for c in self.children)})"

    def clone(self) -> GPTree:
        return GPTree(value=self.value, children=[c.clone() for c in self.children], arity=self.arity)

    def depth(self) -> int:
        return 1 + max((c.depth() for c in self.children), default=0)


_FUNCTIONS: dict[str, Callable[..., float]] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b if abs(b) > 1e-10 else 1.0,
    "sin": lambda a: math.sin(a),
    "cos": lambda a: math.cos(a),
    "exp": lambda a: math.exp(min(a, 50.0)),
    "log": lambda a: math.log(abs(a) + 1e-10),
    "pow": lambda a, b: a ** b if abs(b) < 10 else math.exp(b * math.log(abs(a) + 1e-10)),
    "sqrt": lambda a: math.sqrt(abs(a)),
    "neg": lambda a: -a,
    "abs": lambda a: abs(a),
    "max": lambda a, b: max(a, b),
    "min": lambda a, b: min(a, b),
    "ifle": lambda a, b, c, d: c if a <= b else d,
}

_ARITIES: dict[str, int] = {
    "+": 2, "-": 2, "*": 2, "/": 2,
    "sin": 1, "cos": 1, "exp": 1, "log": 1,
    "pow": 2, "sqrt": 1, "neg": 1, "abs": 1,
    "max": 2, "min": 2, "ifle": 4,
}


class GeneticProgramming:
    """Genetic Programming (tree-based)."""

    def __init__(
        self,
        fitness: Callable[[GPTree], float],
        n_variables: int = 2,
        population_size: int = 100,
        generations: int = 100,
        max_depth: int = 6,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        tournament_size: int = 3,
    ) -> None:
        self.fitness = fitness
        self.n_variables = n_variables
        self.population_size = population_size
        self.generations = generations
        self.max_depth = max_depth
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        self.population: list[GPTree] = []
        self.fitness_values: list[float] = []
        self.best_individual: GPTree | None = None
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0
        self._terminals = [f"x{i}" for i in range(n_variables)] + [random.uniform(-1, 1) for _ in range(10)]

    def _random_tree(self, max_depth: int, full: bool = False) -> GPTree:
        if max_depth == 0:
            return GPTree(value=random.choice(self._terminals), children=[], arity=0)
        if full or random.random() < 0.7:
            func_name = random.choice(list(_FUNCTIONS.keys()))
            arity = _ARITIES[func_name]
            children = [self._random_tree(max_depth - 1, full) for _ in range(arity)]
            return GPTree(value=func_name, children=children, arity=arity)
        else:
            return GPTree(value=random.choice(self._terminals), children=[], arity=0)

    def _grow(self, max_depth: int) -> GPTree:
        return self._random_tree(max_depth, full=False)

    def _full(self, max_depth: int) -> GPTree:
        return self._random_tree(max_depth, full=True)

    def _ramped_half_half(self) -> list[GPTree]:
        pop: list[GPTree] = []
        for depth in range(2, self.max_depth + 1):
            for _ in range(self.population_size // (2 * (self.max_depth - 1))):
                if random.random() < 0.5:
                    pop.append(self._grow(depth))
                else:
                    pop.append(self._full(depth))
        while len(pop) < self.population_size:
            pop.append(self._grow(random.randint(2, self.max_depth)))
        return pop[:self.population_size]

    def _evaluate_tree(self, tree: GPTree, variables: dict[str, float]) -> float:
        if not tree.children:
            if isinstance(tree.value, str) and tree.value.startswith("x"):
                return variables.get(tree.value, 0.0)
            return float(tree.value)
        args = [self._evaluate_tree(c, variables) for c in tree.children]
        func = _FUNCTIONS.get(str(tree.value))
        if func is None:
            return 0.0
        try:
            return func(*args)
        except (OverflowError, ValueError, ZeroDivisionError):
            return float("inf")

    def _tournament_select(self) -> GPTree:
        best = random.choice(self.population)
        best_f = self.fitness_values[self.population.index(best)]
        for _ in range(self.tournament_size - 1):
            contender = random.choice(self.population)
            contender_f = self.fitness_values[self.population.index(contender)]
            if contender_f < best_f:
                best = contender
                best_f = contender_f
        return best

    def _crossover(self, p1: GPTree, p2: GPTree) -> tuple[GPTree, GPTree]:
        nodes1: list[GPTree] = [p1]
        def collect(n: GPTree) -> None:
            for c in n.children:
                nodes1.append(c)
                collect(c)
        collect(p1)
        nodes2: list[GPTree] = [p1]
        collect(p2)
        if len(nodes1) < 2 or len(nodes2) < 2:
            return p1.clone(), p2.clone()
        pt1 = random.choice(nodes1[1:]) if len(nodes1) > 1 else p1
        pt2 = random.choice(nodes2[1:]) if len(nodes2) > 1 else p2

        def replace(root: GPTree, target: GPTree, replacement: GPTree) -> GPTree:
            if root is target:
                return replacement.clone()
            new_children = []
            for c in root.children:
                if c is target:
                    new_children.append(replacement.clone())
                else:
                    new_children.append(replace(c, target, replacement))
            root.children = new_children
            return root

        child1 = replace(p1.clone(), pt1, pt2)
        child2 = replace(p2.clone(), pt2, pt1)
        return child1, child2

    def _mutate(self, tree: GPTree) -> GPTree:
        nodes: list[GPTree] = [tree]
        def collect(n: GPTree) -> None:
            for c in n.children:
                nodes.append(c)
                collect(c)
        collect(tree)
        if len(nodes) < 2:
            return tree.clone()
        pt = random.choice(nodes[1:]) if len(nodes) > 1 else tree
        replacement = self._random_tree(min(3, self.max_depth))
        def replace(root: GPTree, target: GPTree, repl: GPTree) -> GPTree:
            if root is target:
                return repl.clone()
            root.children = [replace(c, target, repl) for c in root.children]
            return root
        return replace(tree.clone(), pt, replacement)

    def initialize(self) -> None:
        self.population = self._ramped_half_half()
        self.fitness_values = [self.fitness(ind) for ind in self.population]
        best_idx = int(np.argmin(self.fitness_values))
        self.best_individual = self.population[best_idx].clone()
        self.best_fitness = self.fitness_values[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        new_pop: list[GPTree] = []
        while len(new_pop) < self.population_size:
            p1 = self._tournament_select()
            p2 = self._tournament_select()
            if random.random() < self.crossover_rate:
                c1, c2 = self._crossover(p1, p2)
            else:
                c1, c2 = p1.clone(), p2.clone()
            if random.random() < self.mutation_rate:
                c1 = self._mutate(c1)
            if random.random() < self.mutation_rate:
                c2 = self._mutate(c2)
            new_pop.append(c1)
            if len(new_pop) < self.population_size:
                new_pop.append(c2)
        self.population = new_pop
        self.fitness_values = [self.fitness(ind) for ind in self.population]
        best_idx = int(np.argmin(self.fitness_values))
        if self.fitness_values[best_idx] < self.best_fitness:
            self.best_fitness = self.fitness_values[best_idx]
            self.best_individual = self.population[best_idx].clone()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> GPTree:
        if not self.population:
            self.initialize()
        g = generations or self.generations
        for _ in range(g):
            self.step()
        return self.best_individual


# Need numpy import
import numpy as np


class CGP:
    """Cartesian Genetic Programming."""

    def __init__(
        self,
        fitness: Callable[["CGPChromosome"], float],
        n_inputs: int = 2,
        n_outputs: int = 1,
        n_cols: int = 10,
        n_rows: int = 5,
        levels_back: int = 10,
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.05,
    ) -> None:
        self.fitness = fitness
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        self.n_cols = n_cols
        self.n_rows = n_rows
        self.levels_back = levels_back
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.func_table = ["+", "-", "*", "/", "sin", "cos", "exp", "sqrt", "abs", "neg"]
        self.n_funcs = len(self.func_table)
        self.population: list[CGPChromosome] = []
        self.best: CGPChromosome | None = None
        self.generation = 0

    def _create_chromosome(self) -> CGPChromosome:
        n_nodes = self.n_cols * self.n_rows
        genes: list[list[int]] = []
        node_idx = 0
        for col in range(self.n_cols):
            for row in range(self.n_rows):
                func = random.randrange(self.n_funcs)
                max_input = self.n_inputs + node_idx
                min_input = max(0, max_input - self.levels_back * self.n_rows)
                if col == 0:
                    min_input = 0
                inputs = [random.randint(min_input, max_input - 1) for _ in range(2)]
                genes.append([func, inputs[0], inputs[1]])
                node_idx += 1
        outputs = [random.randint(0, self.n_inputs + n_nodes - 1) for _ in range(self.n_outputs)]
        return CGPChromosome(genes=genes, outputs=outputs, n_inputs=self.n_inputs)

    def initialize(self) -> None:
        self.population = [self._create_chromosome() for _ in range(self.population_size)]
        for ind in self.population:
            ind.fitness = self.fitness(ind)

    def step(self) -> None:
        for i in range(self.population_size):
            mutant = self.population[i].copy()
            self._mutate(mutant)
            mutant.fitness = self.fitness(mutant)
            if mutant.fitness <= self.population[i].fitness:
                self.population[i] = mutant
        self.population.sort(key=lambda x: x.fitness)
        if self.population[0].fitness < (self.best.fitness if self.best else float("inf")):
            self.best = self.population[0].copy()
        self.generation += 1

    def _mutate(self, chrom: CGPChromosome) -> None:
        n_total = len(chrom.genes) * 3 + len(chrom.outputs)
        for i in range(n_total):
            if random.random() < self.mutation_rate:
                if i < len(chrom.genes) * 3:
                    gene_idx = i // 3
                    gene_part = i % 3
                    if gene_part == 0:
                        chrom.genes[gene_idx][0] = random.randrange(self.n_funcs)
                    else:
                        max_input = self.n_inputs + gene_idx
                        col = gene_idx // self.n_rows
                        min_input = 0 if col == 0 else max(0, max_input - self.levels_back * self.n_rows)
                        chrom.genes[gene_idx][gene_part] = random.randint(min_input, max_input - 1)
                else:
                    out_idx = i - len(chrom.genes) * 3
                    max_val = self.n_inputs + len(chrom.genes) - 1
                    chrom.outputs[out_idx] = random.randint(0, max_val)

    def run(self, generations: int | None = None) -> CGPChromosome:
        if not self.population:
            self.initialize()
        g = generations or self.generations
        for _ in range(g):
            self.step()
        return self.best


class CGPChromosome:
    def __init__(self, genes: list[list[int]], outputs: list[int], n_inputs: int) -> None:
        self.genes = genes
        self.outputs = outputs
        self.n_inputs = n_inputs
        self.fitness = float("inf")

    def copy(self) -> CGPChromosome:
        return CGPChromosome(
            genes=[g[:] for g in self.genes],
            outputs=self.outputs[:],
            n_inputs=self.n_inputs,
        )

    def evaluate(self, inputs: list[float]) -> list[float]:
        node_values: list[float] = inputs[:]
        for gene in self.genes:
            func_idx, in1, in2 = gene
            a = node_values[in1] if in1 < len(node_values) else 0.0
            b = node_values[in2] if in2 < len(node_values) else 0.0
            func_name = ["+", "-", "*", "/", "sin", "cos", "exp", "sqrt", "abs", "neg"][func_idx]
            func = _FUNCTIONS.get(func_name, lambda x, y: 0.0)
            try:
                if func_name in ("sin", "cos", "exp", "sqrt", "abs", "neg"):
                    val = func(a)
                else:
                    val = func(a, b)
            except (OverflowError, ValueError):
                val = 0.0
            node_values.append(val)
        return [node_values[o] if o < len(node_values) else 0.0 for o in self.outputs]


class ES_HyperNEAT:
    """Evolutionary Strategy HyperNEAT — placeholders."""

    def __init__(self) -> None:
        pass
