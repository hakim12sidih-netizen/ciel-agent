from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class ImmuneParams:
    population_size: int = 50
    dimensions: int = 10
    generations: int = 100
    bounds: tuple[float, float] = (-10.0, 10.0)
    clone_factor: float = 0.5
    mutation_rate: float = 0.1
    selection_ratio: float = 0.2


class CLONALG:
    """CLONal selection ALGorithm — artificial immune system."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        params: ImmuneParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or ImmuneParams()
        self.population: list[np.ndarray] = []
        self.affinities: list[float] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.population = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.affinities = [self.evaluate(p) for p in self.population]
        best_idx = int(np.argmin(self.affinities))
        self.best_solution = self.population[best_idx].copy()
        self.best_fitness = self.affinities[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size

        # Selection
        n_select = max(1, int(n * self.params.selection_ratio))
        idxs = np.argsort(self.affinities)[:n_select]

        # Clonal expansion
        clones: list[np.ndarray] = []
        for idx in idxs:
            n_clones = max(1, int(self.params.clone_factor * n / (idx + 1)))
            for _ in range(n_clones):
                clone = self.population[idx].copy()
                # Hypermutation inversely proportional to affinity
                mutation_rate = self.params.mutation_rate * (1.0 / (1.0 + self.affinities[idx]))
                for j in range(dim):
                    if random.random() < mutation_rate:
                        clone[j] += np.random.normal(0, abs(high - low) * mutation_rate)
                clone = np.clip(clone, low, high)
                clones.append(clone)

        # Evaluate clones
        clone_affs = [self.evaluate(c) for c in clones]

        # Replace worst antibodies with best clones
        all_sols = list(zip(self.population, self.affinities)) + list(zip(clones, clone_affs))
        all_sols.sort(key=lambda x: x[1])
        self.population = [s.copy() for s, _ in all_sols[:n]]
        self.affinities = [a for _, a in all_sols[:n]]

        best_idx = int(np.argmin(self.affinities))
        if self.affinities[best_idx] < self.best_fitness:
            self.best_fitness = self.affinities[best_idx]
            self.best_solution = self.population[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.population:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class NegativeSelection:
    """Negative Selection Algorithm — detect anomalies."""

    def __init__(self, params: ImmuneParams | None = None) -> None:
        self.params = params or ImmuneParams()
        self.detectors: list[np.ndarray] = []
        self.threshold: float = 0.1

    def generate_detectors(self, self_samples: np.ndarray, n_detectors: int = 100) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        self.detectors = []
        while len(self.detectors) < n_detectors:
            candidate = np.random.uniform(low, high, dim)
            if all(np.linalg.norm(candidate - s) > self.threshold for s in self_samples):
                self.detectors.append(candidate)

    def detect(self, sample: np.ndarray) -> bool:
        return any(np.linalg.norm(sample - d) < self.threshold for d in self.detectors)


class AINET:
    """Artificial Immune Network — clustering and optimization."""

    def __init__(self, params: ImmuneParams | None = None) -> None:
        self.params = params or ImmuneParams()
        self.network: list[np.ndarray] = []
        self.suppression_threshold: float = 0.2

    def train(self, data: np.ndarray, epochs: int = 10) -> list[np.ndarray]:
        low, high = self.params.bounds
        dim = self.params.dimensions
        self.network = [np.random.uniform(low, high, dim) for _ in range(20)]
        for _ in range(epochs):
            for x in data:
                affinities = [np.linalg.norm(x - c) for c in self.network]
                best_idx = int(np.argmin(affinities))
                self.network[best_idx] += 0.1 * (x - self.network[best_idx])
            # Suppression
            to_remove: list[int] = []
            for i in range(len(self.network)):
                for j in range(i + 1, len(self.network)):
                    if np.linalg.norm(self.network[i] - self.network[j]) < self.suppression_threshold:
                        to_remove.append(j)
            for idx in sorted(set(to_remove), reverse=True):
                self.network.pop(idx)
        return self.network


class DangerTheory:
    """Danger Theory — immune response based on danger signals."""

    def __init__(self) -> None:
        self.danger_signals: list[float] = []
        self.apc_activated: bool = False

    def receive_signal(self, signal: float, threshold: float = 0.5) -> bool:
        self.danger_signals.append(signal)
        if signal > threshold:
            self.apc_activated = True
        return self.apc_activated

    def immune_response(self) -> str:
        if self.apc_activated:
            return "adaptive_response"
        if sum(self.danger_signals[-10:]) / max(1, len(self.danger_signals[-10:])) > 0.3:
            return "innate_response"
        return "tolerance"
