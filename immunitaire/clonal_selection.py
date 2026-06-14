from __future__ import annotations

import random
from collections.abc import Callable

import numpy as np


class AffinityMaturation:
    """Maturation par affinité — hypermutation somatique et sélection."""

    def __init__(self, mutation_rate: float = 0.1, affinity_threshold: float = 0.5) -> None:
        self.mutation_rate = mutation_rate
        self.affinity_threshold = affinity_threshold

    def mutate(self, antibody: np.ndarray, affinity: float, bounds: tuple[float, float] = (-1.0, 1.0)) -> np.ndarray:
        rate = self.mutation_rate * (1.0 / (1.0 + affinity * 5))
        mutant = antibody + np.random.normal(0, rate, antibody.shape)
        return np.clip(mutant, bounds[0], bounds[1])

    def select(self, population: list[np.ndarray], affinities: list[float], keep_ratio: float = 0.3) -> tuple[list[np.ndarray], list[float]]:
        paired = list(zip(population, affinities))
        paired.sort(key=lambda x: x[1], reverse=True)
        n_keep = max(1, int(len(paired) * keep_ratio))
        kept = paired[:n_keep]
        return [p[0] for p in kept], [p[1] for p in kept]


class ClonalSelector:
    """Sélection clonale — CLONALG adapté pour le stratum immunitaire."""

    def __init__(
        self,
        dimension: int = 10,
        population_size: int = 50,
        clone_factor: float = 0.5,
        mutation_rate: float = 0.1,
        selection_ratio: float = 0.2,
    ) -> None:
        self.dimension = dimension
        self.population_size = population_size
        self.clone_factor = clone_factor
        self.mutation_rate = mutation_rate
        self.selection_ratio = selection_ratio
        self.population: list[np.ndarray] = []
        self.affinities: list[float] = []

    def initialize(self, bounds: tuple[float, float] = (-1.0, 1.0)) -> None:
        self.population = [np.random.uniform(bounds[0], bounds[1], self.dimension) for _ in range(self.population_size)]
        self.affinities = [0.0] * self.population_size

    def evaluate(self, antigen: np.ndarray) -> list[float]:
        self.affinities = [1.0 / (1.0 + float(np.linalg.norm(ab - antigen))) for ab in self.population]
        return self.affinities

    def step(self, antigen: np.ndarray, bounds: tuple[float, float] = (-1.0, 1.0)) -> tuple[np.ndarray, float]:
        self.evaluate(antigen)
        n = self.population_size
        n_select = max(1, int(n * self.selection_ratio))
        idxs = np.argsort(self.affinities)[-n_select:]

        clones: list[np.ndarray] = []
        for idx in idxs:
            n_clones = max(1, int(self.clone_factor * n / (idx + 1)))
            for _ in range(n_clones):
                clone = self.population[idx].copy()
                rate = self.mutation_rate * (1.0 / (1.0 + self.affinities[idx] * 5))
                clone += np.random.normal(0, rate, self.dimension)
                clone = np.clip(clone, bounds[0], bounds[1])
                clones.append(clone)

        clone_affs = [1.0 / (1.0 + float(np.linalg.norm(c - antigen))) for c in clones]
        all_ab = list(zip(self.population, self.affinities)) + list(zip(clones, clone_affs))
        all_ab.sort(key=lambda x: x[1], reverse=True)
        self.population = [ab.copy() for ab, _ in all_ab[:n]]
        self.affinities = [aff for _, aff in all_ab[:n]]

        best_idx = int(np.argmax(self.affinities))
        return self.population[best_idx].copy(), self.affinities[best_idx]

    def run(self, antigen: np.ndarray, generations: int = 20) -> tuple[np.ndarray, float]:
        best_solution = self.population[0].copy() if self.population else np.zeros(self.dimension)
        best_aff = 0.0
        for _ in range(generations):
            sol, aff = self.step(antigen)
            if aff > best_aff:
                best_aff = aff
                best_solution = sol.copy()
        return best_solution, best_aff
