from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class OEEParams:
    population_size: int = 50
    dimensions: int = 10
    generations: int = 200
    bounds: tuple[float, float] = (-10.0, 10.0)
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    mc_lower: float = 0.5  # Minimal criterion lower bound
    transfer_strength: float = 0.1


class POET:
    """Paired Open-Ended Trailblazer.

    Co-evolves environments and solutions, transferring solutions between
    environments that meet a minimal criterion.
    """

    def __init__(
        self,
        evaluate: Callable[[np.ndarray, np.ndarray], float],
        env_generate: Callable[[np.ndarray], np.ndarray],
        params: OEEParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.env_generate = env_generate
        self.params = params or OEEParams()
        self.solutions: list[np.ndarray] = []
        self.environments: list[np.ndarray] = []
        self.env_params: list[np.ndarray] = []  # Parameters governing environment difficulty
        self.fitness: list[float] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[int] = []  # Number of env-solution pairs that meet MC
        self.generation = 0

    def initialize(self, n_pairs: int = 10) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        for _ in range(n_pairs):
            sol = np.random.uniform(low, high, dim)
            env = self.env_generate(np.random.uniform(low, high, 2))
            ep = np.random.uniform(0.1, 1.0, 2)
            fit = self.evaluate(sol, env)
            self.solutions.append(sol)
            self.environments.append(env)
            self.env_params.append(ep)
            self.fitness.append(fit)
        best_idx = int(np.argmin(self.fitness))
        self.best_solution = self.solutions[best_idx].copy()
        self.best_fitness = self.fitness[best_idx]
        self.history.append(sum(1 for f in self.fitness if f < self.params.mc_lower))

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = len(self.solutions)

        # Evaluate all pairs
        self.fitness = [self.evaluate(s, e) for s, e in zip(self.solutions, self.environments)]

        # Check minimal criterion
        mc_met = [i for i, f in enumerate(self.fitness) if f < self.params.mc_lower]

        # Transfer solutions between environments that meet MC
        if len(mc_met) >= 2:
            for _ in range(len(mc_met)):
                i, j = random.sample(mc_met, 2)
                if random.random() < self.params.crossover_rate:
                    alpha = random.random()
                    child_sol = alpha * self.solutions[i] + (1 - alpha) * self.solutions[j]
                    child_sol = np.clip(child_sol, low, high)
                    child_fit = self.evaluate(child_sol, self.environments[j])
                    if child_fit < self.fitness[j]:
                        self.solutions[j] = child_sol
                        self.fitness[j] = child_fit

        # Mutate solutions
        for i in range(n):
            if random.random() < self.params.mutation_rate:
                self.solutions[i] += np.random.normal(0, self.params.transfer_strength, dim)
                self.solutions[i] = np.clip(self.solutions[i], low, high)

        # Add new environment-solution pairs when MC is widely met
        if len(mc_met) > n * 0.5:
            new_sol = np.random.uniform(low, high, dim)
            new_env = self.env_generate(np.random.uniform(low, high, 2))
            new_ep = np.random.uniform(0.1, 1.0, 2)
            new_fit = self.evaluate(new_sol, new_env)
            self.solutions.append(new_sol)
            self.environments.append(new_env)
            self.env_params.append(new_ep)
            self.fitness.append(new_fit)

        best_idx = int(np.argmin(self.fitness))
        if self.fitness[best_idx] < self.best_fitness:
            self.best_fitness = self.fitness[best_idx]
            self.best_solution = self.solutions[best_idx].copy()
        self.history.append(sum(1 for f in self.fitness if f < self.params.mc_lower))
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.solutions:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class EnhancedPOET(POET):
    """Enhanced POET with environment mutation and complexity scoring."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray, np.ndarray], float],
        env_generate: Callable[[np.ndarray], np.ndarray],
        env_mutate: Callable[[np.ndarray], np.ndarray],
        params: OEEParams | None = None,
    ) -> None:
        super().__init__(evaluate, env_generate, params)
        self.env_mutate = env_mutate

    def step(self) -> None:
        super().step()
        # Mutate environments of top performers
        n = len(self.environments)
        idxs = np.argsort(self.fitness)
        for i in idxs[:max(1, n // 4)]:
            if random.random() < self.params.mutation_rate:
                self.environments[i] = self.env_mutate(self.environments[i])
                self.env_params[i] += np.random.normal(0, 0.1, self.env_params[i].shape)
                self.env_params[i] = np.clip(self.env_params[i], 0.1, 5.0)


class OMNI:
    """OMNI — Open-endedness via Meta-learning and Novelty Induction.

    Placeholder for future implementation.
    """

    def __init__(self) -> None:
        self.novelty_archive: list[np.ndarray] = []

    def novelty_score(self, solution: np.ndarray, k: int = 5) -> float:
        if len(self.novelty_archive) < k:
            return 1.0
        dists = sorted(np.linalg.norm(solution - a) for a in self.novelty_archive)
        return sum(dists[:k]) / k
