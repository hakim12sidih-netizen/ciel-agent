from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class CMAESParams:
    dimension: int = 10
    population_size: int | None = None
    generations: int = 500
    init_sigma: float = 1.0
    init_mean: np.ndarray | None = None
    bounds: tuple[float, float] | None = None
    tol_x: float = 1e-12
    tol_fun: float = 1e-12
    restarts: int = 0
    restart_multiplier: float = 2.0


class CMAES:
    """Covariance Matrix Adaptation Evolution Strategy."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        params: CMAESParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or CMAESParams()
        self.dim = self.params.dimension
        lam = self.params.population_size or (4 + int(3 * math.log(self.dim)))
        self.lam = lam
        self.mu = lam // 2
        self.weights = np.log(self.mu + 0.5) - np.log(np.arange(1, self.mu + 1))
        self.weights /= self.weights.sum()
        self.mueff = 1.0 / np.sum(self.weights**2)
        self.cc = (4 + self.mueff / self.dim) / (self.dim + 4 + 2 * self.mueff / self.dim)
        self.cs = (self.mueff + 2) / (self.dim + self.mueff + 5)
        self.c1 = 2.0 / ((self.dim + 1.3) ** 2 + self.mueff)
        self.cmu = min(1 - self.c1, 2 * (self.mueff - 2 + 1 / self.mueff) / ((self.dim + 2) ** 2 + self.mueff))
        self.damps = 1 + 2 * max(0, math.sqrt((self.mueff - 1) / (self.dim + 1)) - 1) + self.cs
        self.mean: np.ndarray = np.zeros(self.dim)
        self.sigma: float = 1.0
        self.C: np.ndarray = np.eye(self.dim)
        self.pc: np.ndarray = np.zeros(self.dim)
        self.ps: np.ndarray = np.zeros(self.dim)
        self.eigenvalues: np.ndarray = np.ones(self.dim)
        self.eigenvectors: np.ndarray = np.eye(self.dim)
        self.generation: int = 0
        self.best_fitness: float = float("inf")
        self.best_vector: np.ndarray = np.array([])
        self.history: list[float] = []
        self._eigenvalid: bool = False
        self._force_update: bool = False

    def initialize(self, mean: np.ndarray | None = None) -> None:
        self.mean = mean if mean is not None else (self.params.init_mean if self.params.init_mean is not None else np.zeros(self.dim))
        self.sigma = self.params.init_sigma
        self.C = np.eye(self.dim)
        self.pc = np.zeros(self.dim)
        self.ps = np.zeros(self.dim)
        self._update_eigensystem()
        self.generation = 0
        self.best_fitness = float("inf")
        self.best_vector = self.mean.copy()
        self.history = []

    def _update_eigensystem(self) -> None:
        if self._eigenvalid and not self._force_update:
            return
        self.eigenvalues, self.eigenvectors = np.linalg.eigh(self.C)
        self.eigenvalues = np.maximum(self.eigenvalues, 1e-20)
        self._eigenvalid = True
        self._force_update = False

    def _sample_population(self) -> np.ndarray:
        self._update_eigensystem()
        A = self.eigenvectors @ np.diag(np.sqrt(self.eigenvalues))
        Z = np.random.randn(self.lam, self.dim)
        return self.mean + self.sigma * (Z @ A.T)

    def _select_and_recombine(self, population: np.ndarray, fitness: np.ndarray) -> None:
        idxs = np.argsort(fitness)
        self.mean = np.zeros(self.dim)
        for i in range(self.mu):
            self.mean += self.weights[i] * population[idxs[i]]

    def _update_covariance(self, population: np.ndarray, fitness: np.ndarray, old_mean: np.ndarray) -> None:
        idxs = np.argsort(fitness)
        y = (self.mean - old_mean) / self.sigma
        self.ps = (1 - self.cs) * self.ps + math.sqrt(self.cs * (2 - self.cs) * self.mueff) * (self.eigenvectors.T @ y)
        hsig = (np.linalg.norm(self.ps) / math.sqrt(1 - (1 - self.cs) ** (2 * (self.generation + 1))) < (1.4 + 2.0 / (self.dim + 1)) * self.eigenvalues[0])
        self.pc = (1 - self.cc) * self.pc + hsig * math.sqrt(self.cc * (2 - self.cc) * self.mueff) * y
        delta_hsig = (1 - hsig) * self.cc * (2 - self.cc)
        artmp = np.zeros((self.dim, self.dim))
        for i in range(self.mu):
            z = (population[idxs[i]] - old_mean) / self.sigma
            artmp += self.weights[i] * np.outer(z, z)
        self.C = (1 - self.c1 - self.cmu) * self.C + self.c1 * np.outer(self.pc, self.pc - delta_hsig * y) + self.cmu * artmp
        self.C = (self.C + self.C.T) / 2
        self._force_update = True

    def _update_stepsize(self) -> None:
        ps_norm = np.linalg.norm(self.ps)
        expected = math.sqrt(self.dim) * (1 - 1.0 / (4 * self.dim) + 1.0 / (21 * self.dim**2))
        self.sigma *= math.exp((self.cs / self.damps) * (ps_norm / expected - 1))

    def step(self) -> None:
        old_mean = self.mean.copy()
        population = self._sample_population()
        bounds = self.params.bounds
        if bounds is not None:
            population = np.clip(population, bounds[0], bounds[1])
        fitness = np.array([self.evaluate(ind) for ind in population])
        best_idx = int(np.argmin(fitness))
        if fitness[best_idx] < self.best_fitness:
            self.best_fitness = float(fitness[best_idx])
            self.best_vector = population[best_idx].copy()
        self._select_and_recombine(population, fitness)
        self._update_covariance(population, fitness, old_mean)
        self._update_stepsize()
        self.generation += 1
        self.history.append(self.best_fitness)

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if self.generation == 0:
            self.initialize()
        g = generations or self.params.generations
        restarts = self.params.restarts
        best_overall = self.best_fitness
        best_vec_overall = self.best_vector.copy()
        for _ in range(g):
            self.step()
            if self.best_fitness < best_overall:
                best_overall = self.best_fitness
                best_vec_overall = self.best_vector.copy()
        factor = self.params.restart_multiplier
        for r in range(restarts):
            self.sigma = self.params.init_sigma * (factor**r)
            self.mean = np.random.uniform(-2, 2, self.dim) * (factor**r)
            self.C = np.eye(self.dim)
            self.pc = np.zeros(self.dim)
            self.ps = np.zeros(self.dim)
            self.generation = 0
            self._eigenvalid = False
            for _ in range(g):
                self.step()
                if self.best_fitness < best_overall:
                    best_overall = self.best_fitness
                    best_vec_overall = self.best_vector.copy()
        return best_vec_overall, best_overall


class SepCMAES(CMAES):
    """Separable CMA-ES — diagonal covariance only."""

    def _update_covariance(self, population: np.ndarray, fitness: np.ndarray, old_mean: np.ndarray) -> None:
        idxs = np.argsort(fitness)
        y = (self.mean - old_mean) / self.sigma
        self.ps = (1 - self.cs) * self.ps + math.sqrt(self.cs * (2 - self.cs) * self.mueff) * y / np.sqrt(np.diag(self.C) + 1e-20)
        hsig = (np.linalg.norm(self.ps) / math.sqrt(1 - (1 - self.cs) ** (2 * (self.generation + 1))) < (1.4 + 2.0 / (self.dim + 1)))
        self.pc = (1 - self.cc) * self.pc + hsig * math.sqrt(self.cc * (2 - self.cc) * self.mueff) * y
        diag_C = np.diag(self.C)
        diag_C *= 1 - self.c1 - self.cmu
        diag_C += self.c1 * self.pc**2
        artmp = np.zeros(self.dim)
        for i in range(self.mu):
            z = (population[idxs[i]] - old_mean) / self.sigma
            artmp += self.weights[i] * z**2
        diag_C += self.cmu * artmp
        diag_C = np.maximum(diag_C, 1e-20)
        self.C = np.diag(diag_C)
        self._force_update = True
