from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class DEStrategy(Enum):
    RAND_1_BIN = "rand_1_bin"
    BEST_1_BIN = "best_1_bin"
    CURRENT_TO_BEST_1_BIN = "current_to_best_1_bin"
    RAND_1_EXP = "rand_1_exp"
    RAND_2_BIN = "rand_2_bin"
    BEST_2_BIN = "best_2_bin"
    JADE = "jade"
    SHADE = "shade"


@dataclass(slots=True, frozen=True)
class DEParams:
    population_size: int = 100
    generations: int = 500
    F: float = 0.5
    CR: float = 0.9
    bounds: tuple[float, float] = (-10.0, 10.0)
    strategy: DEStrategy = DEStrategy.RAND_1_BIN
    dither: bool = True
    jitter: bool = False
    adaptation: bool = False
    dimension: int = 10


class DifferentialEvolution:
    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        params: DEParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or DEParams()
        self.population: np.ndarray = np.array([])
        self.fitness: np.ndarray = np.array([])
        self.best_idx: int = 0
        self.best_vector: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation: int = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimension
        self.population = np.random.uniform(low, high, (self.params.population_size, dim))
        self.fitness = np.array([self.evaluate(ind) for ind in self.population])
        self.best_idx = int(np.argmin(self.fitness))
        self.best_vector = self.population[self.best_idx].copy()
        self.best_fitness = float(self.fitness[self.best_idx])
        self.history.append(self.best_fitness)

    def _mutate_rand_1(self, i: int, F: float) -> np.ndarray:
        idxs = list(range(self.params.population_size))
        idxs.remove(i)
        a, b, c = random.sample(idxs, 3)
        return self.population[a] + F * (self.population[b] - self.population[c])

    def _mutate_best_1(self, i: int, F: float) -> np.ndarray:
        idxs = list(range(self.params.population_size))
        idxs.remove(i)
        a, b = random.sample(idxs, 2)
        return self.best_vector + F * (self.population[a] - self.population[b])

    def _mutate_current_to_best_1(self, i: int, F: float) -> np.ndarray:
        idxs = list(range(self.params.population_size))
        idxs.remove(i)
        a, b = random.sample(idxs, 2)
        x = self.population[i]
        return x + F * (self.best_vector - x) + F * (self.population[a] - self.population[b])

    def _mutate_rand_2(self, i: int, F: float) -> np.ndarray:
        idxs = list(range(self.params.population_size))
        idxs.remove(i)
        a, b, c, d, e = random.sample(idxs, 5)
        return self.population[a] + F * (self.population[b] - self.population[c]) + F * (self.population[d] - self.population[e])

    def _mutate_best_2(self, i: int, F: float) -> np.ndarray:
        idxs = list(range(self.params.population_size))
        idxs.remove(i)
        a, b, c, d = random.sample(idxs, 4)
        return self.best_vector + F * (self.population[a] - self.population[b]) + F * (self.population[c] - self.population[d])

    def _crossover_bin(self, trial: np.ndarray, target: np.ndarray, CR: float) -> np.ndarray:
        dim = self.params.dimension
        j_rand = random.randint(0, dim - 1)
        return np.array([trial[j] if random.random() < CR or j == j_rand else target[j] for j in range(dim)])

    def _crossover_exp(self, trial: np.ndarray, target: np.ndarray, CR: float) -> np.ndarray:
        dim = self.params.dimension
        child = target.copy()
        j = random.randint(0, dim - 1)
        L = 0
        while random.random() < CR and L < dim:
            child[j] = trial[j]
            j = (j + 1) % dim
            L += 1
        return child

    def step(self) -> None:
        F = self.params.F * (1.0 + 0.5 * (random.random() - 0.5)) if self.params.dither else self.params.F
        CR = self.params.CR
        new_pop = np.empty_like(self.population)
        new_fitness = np.empty(self.params.population_size)

        for i in range(self.params.population_size):
            match self.params.strategy:
                case DEStrategy.RAND_1_BIN:
                    mutant = self._mutate_rand_1(i, F)
                case DEStrategy.BEST_1_BIN:
                    mutant = self._mutate_best_1(i, F)
                case DEStrategy.CURRENT_TO_BEST_1_BIN:
                    mutant = self._mutate_current_to_best_1(i, F)
                case DEStrategy.RAND_2_BIN:
                    mutant = self._mutate_rand_2(i, F)
                case DEStrategy.BEST_2_BIN:
                    mutant = self._mutate_best_2(i, F)
                case _:
                    mutant = self._mutate_rand_1(i, F)

            if self.params.jitter:
                mutant += np.random.normal(0, 0.01, self.params.dimension)

            match self.params.strategy:
                case DEStrategy.RAND_1_EXP:
                    trial = self._crossover_exp(mutant, self.population[i], CR)
                case _:
                    trial = self._crossover_bin(mutant, self.population[i], CR)

            trial = np.clip(trial, self.params.bounds[0], self.params.bounds[1])
            ftrial = self.evaluate(trial)

            if ftrial <= self.fitness[i]:
                new_pop[i] = trial
                new_fitness[i] = ftrial
            else:
                new_pop[i] = self.population[i]
                new_fitness[i] = self.fitness[i]

        self.population = new_pop
        self.fitness = new_fitness
        self.best_idx = int(np.argmin(self.fitness))
        if self.fitness[self.best_idx] < self.best_fitness:
            self.best_fitness = float(self.fitness[self.best_idx])
            self.best_vector = self.population[self.best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if self.population.size == 0:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_vector, self.best_fitness
