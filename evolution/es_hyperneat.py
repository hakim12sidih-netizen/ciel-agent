from __future__ import annotations

import random
from collections.abc import Callable

import numpy as np


class ES_HyperNEAT:
    """Evolutionary Strategy for HyperNEAT — placeholders.

    Uses ES to evolve CPPN weights for HyperNEAT substrate development.
    """

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        genome_dim: int = 100,
        population_size: int = 50,
        generations: int = 200,
        sigma: float = 0.1,
    ) -> None:
        self.evaluate = evaluate
        self.genome_dim = genome_dim
        self.population_size = population_size
        self.generations = generations
        self.sigma = sigma
        self.mean = np.zeros(genome_dim)
        self.history: list[float] = []
        self.generation = 0

    def step(self) -> None:
        # Simple (mu, lambda)-ES
        noise = np.random.randn(self.population_size, self.genome_dim) * self.sigma
        candidates = self.mean + noise
        fitness = np.array([self.evaluate(c) for c in candidates])
        best_idx = int(np.argmin(fitness))
        self.mean = candidates[best_idx].copy()
        self.history.append(float(fitness[best_idx]))
        self.generation += 1

    def run(self, generations: int | None = None) -> np.ndarray:
        g = generations or self.generations
        for _ in range(g):
            self.step()
        return self.mean
