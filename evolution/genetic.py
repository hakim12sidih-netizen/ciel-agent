from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

import numpy as np

T = TypeVar("T")


class GeneticOperator(Enum):
    TOURNAMENT = "tournament"
    ROULETTE = "roulette"
    RANK = "rank"
    UNIFORM = "uniform"
    STOCHASTIC_UNIVERSAL = "stochastic_universal"


@dataclass(slots=True, frozen=True)
class GAParams:
    population_size: int = 200
    generations: int = 100
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    elite_ratio: float = 0.05
    tournament_size: int = 3
    selection: GeneticOperator = GeneticOperator.TOURNAMENT
    adaptive_mutation: bool = True
    niching: bool = False
    fitness_sharing_sigma: float = 0.1


@dataclass(slots=True)
class Individual(Generic[T]):
    genome: T
    fitness: float = -float("inf")
    age: int = 0
    diversity_share: float = 1.0

    def __lt__(self, other: Individual[T]) -> bool:
        return self.fitness < other.fitness


class GeneticAlgorithm(Generic[T]):
    def __init__(
        self,
        create_genome: Callable[[], T],
        evaluate: Callable[[T], float],
        crossover: Callable[[T, T], tuple[T, T]],
        mutate: Callable[[T, float], T],
        params: GAParams | None = None,
    ) -> None:
        self.create_genome = create_genome
        self.evaluate = evaluate
        self.crossover = crossover
        self.mutate = mutate
        self.params = params or GAParams()
        self.population: list[Individual[T]] = []
        self.generation = 0
        self.best_fitness: float = -float("inf")
        self.best_individual: Individual[T] | None = None
        self.fitness_history: list[float] = []
        self.population: list[Individual[T]] = []
        self.generation = 0
        self.best_fitness: float = -float("inf")
        self.best_individual: Individual[T] | None = None
        self.fitness_history: list[float] = []

    def initialize_population(self) -> None:
        self.population = [
            Individual(genome=self.create_genome())
            for _ in range(self.params.population_size)
        ]

    def evaluate_population(self) -> None:
        for ind in self.population:
            if ind.fitness == -float("inf"):
                ind.fitness = self.evaluate(ind.genome)

    def _tournament_select(self) -> Individual[T]:
        k = self.params.tournament_size
        best = random.choice(self.population)
        for _ in range(k - 1):
            contender = random.choice(self.population)
            if contender.fitness > best.fitness:
                best = contender
        return best

    def _roulette_select(self) -> Individual[T]:
        total = sum(max(0.0, ind.fitness) for ind in self.population)
        if total == 0.0:
            return random.choice(self.population)
        target = random.random() * total
        cumulative = 0.0
        for ind in self.population:
            cumulative += max(0.0, ind.fitness)
            if cumulative >= target:
                return ind
        return self.population[-1]

    def _rank_select(self) -> Individual[T]:
        sorted_pop = sorted(self.population, key=lambda x: x.fitness)
        n = len(sorted_pop)
        total = n * (n + 1) / 2.0
        target = random.random() * total
        cumulative = 0.0
        for i, ind in enumerate(sorted_pop):
            cumulative += i + 1
            if cumulative >= target:
                return ind
        return sorted_pop[-1]

    def select(self) -> Individual[T]:
        match self.params.selection:
            case GeneticOperator.TOURNAMENT:
                return self._tournament_select()
            case GeneticOperator.ROULETTE:
                return self._roulette_select()
            case GeneticOperator.RANK:
                return self._rank_select()
            case _:
                return random.choice(self.population)

    def _compute_sharing(self, ind_a: Individual[T], ind_b: Individual[T]) -> float:
        # Approximate genome distance via a simple heuristic;
        # subclasses should override with domain-specific distance.
        return 1.0

    def _apply_niching(self) -> None:
        if not self.params.niching:
            return
        sigma = self.params.fitness_sharing_sigma
        for i, ind in enumerate(self.population):
            niche_count = 0.0
            for j, other in enumerate(self.population):
                if i == j:
                    continue
                d = self._compute_sharing(ind, other)
                if d < sigma:
                    niche_count += 1.0 - d / sigma
            ind.diversity_share = niche_count if niche_count > 0.0 else 1.0
            ind.fitness /= ind.diversity_share

    def step(self) -> None:
        self.evaluate_population()
        self._apply_niching()
        self._update_stats()

        elite_count = max(1, int(self.params.population_size * self.params.elite_ratio))
        elites = sorted(self.population, reverse=True)[:elite_count]
        next_pop = [Individual(genome=elite.genome, fitness=self.evaluate(elite.genome)) for elite in elites]

        rate = self.params.mutation_rate
        if self.params.adaptive_mutation:
            variance = self._population_variance()
            rate = rate * (1.0 / (1.0 + variance)) if variance > 0 else rate

        while len(next_pop) < self.params.population_size:
            p1 = self.select()
            p2 = self.select()
            if random.random() < self.params.crossover_rate:
                g1, g2 = self.crossover(p1.genome, p2.genome)
            else:
                g1, g2 = p1.genome, p2.genome
            c1 = Individual(genome=self.mutate(g1, rate), age=0)
            c2 = Individual(genome=self.mutate(g2, rate), age=0)
            next_pop.append(c1)
            if len(next_pop) < self.params.population_size:
                next_pop.append(c2)

        self.population = next_pop
        self.generation += 1

    def run(self, generations: int | None = None) -> Individual[T]:
        if not self.population:
            self.initialize_population()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_individual

    def _update_stats(self) -> None:
        current_best = max(self.population)
        if current_best.fitness > self.best_fitness:
            self.best_fitness = current_best.fitness
            self.best_individual = current_best
        self.fitness_history.append(self.best_fitness)

    def _population_variance(self) -> float:
        if len(self.population) < 2:
            return 0.0
        fits = [ind.fitness for ind in self.population if ind.fitness != -float("inf")]
        if not fits:
            return 0.0
        return float(np.var(fits))
