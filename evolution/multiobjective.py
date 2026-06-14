from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class MOParams:
    population_size: int = 100
    dimensions: int = 10
    generations: int = 500
    bounds: tuple[float, float] = (-10.0, 10.0)
    n_objectives: int = 2
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    crossover_index: float = 20.0
    mutation_index: float = 20.0


def _sbx(p1: np.ndarray, p2: np.ndarray, eta: float, low: float, high: float) -> tuple[np.ndarray, np.ndarray]:
    dim = len(p1)
    c1, c2 = p1.copy(), p2.copy()
    for i in range(dim):
        if random.random() <= 0.5:
            if abs(p1[i] - p2[i]) > 1e-14:
                y1, y2 = min(p1[i], p2[i]), max(p1[i], p2[i])
                beta = 1.0 + 2.0 * (y1 - low) / (y2 - y1 + 1e-14)
                alpha = 2.0 - beta ** (-(eta + 1.0))
                rand = random.random()
                if rand <= 1.0 / alpha:
                    betaq = (rand * alpha) ** (1.0 / (eta + 1.0))
                else:
                    betaq = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta + 1.0))
                c1[i] = 0.5 * ((y1 + y2) - betaq * (y2 - y1))
                beta = 1.0 + 2.0 * (high - y2) / (y2 - y1 + 1e-14)
                alpha = 2.0 - beta ** (-(eta + 1.0))
                if rand <= 1.0 / alpha:
                    betaq = (rand * alpha) ** (1.0 / (eta + 1.0))
                else:
                    betaq = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (eta + 1.0))
                c2[i] = 0.5 * ((y1 + y2) + betaq * (y2 - y1))
                c1[i] = np.clip(c1[i], low, high)
                c2[i] = np.clip(c2[i], low, high)
    return c1, c2


def _polynomial_mutation(x: np.ndarray, eta: float, low: float, high: float, rate: float) -> np.ndarray:
    child = x.copy()
    for i in range(len(x)):
        if random.random() < rate:
            delta = random.random()
            if delta < 0.5:
                multiplier = (2.0 * delta) ** (1.0 / (eta + 1.0)) - 1.0
            else:
                multiplier = 1.0 - (2.0 * (1.0 - delta)) ** (1.0 / (eta + 1.0))
            child[i] += multiplier * (high - low)
            child[i] = np.clip(child[i], low, high)
    return child


def _non_dominated_sort(fitness: np.ndarray) -> list[list[int]]:
    n = len(fitness)
    domination_count = np.zeros(n, dtype=int)
    dominated_set: list[list[int]] = [[] for _ in range(n)]
    fronts: list[list[int]] = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if all(fitness[i] <= fitness[j]) and any(fitness[i] < fitness[j]):
                dominated_set[i].append(j)
            elif all(fitness[j] <= fitness[i]) and any(fitness[j] < fitness[i]):
                domination_count[i] += 1
        if domination_count[i] == 0:
            fronts.append([i])
    current = 0
    while current < len(fronts):
        next_front: list[int] = []
        for i in fronts[current]:
            for j in dominated_set[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    next_front.append(j)
        if next_front:
            fronts.append(next_front)
        current += 1
    return fronts


def _crowding_distance(fitness: np.ndarray, front: list[int]) -> np.ndarray:
    n_obj = fitness.shape[1]
    m = len(front)
    dist = np.zeros(m)
    for obj in range(n_obj):
        idxs = sorted(range(m), key=lambda i: fitness[front[i], obj])
        dist[idxs[0]] = float("inf")
        dist[idxs[-1]] = float("inf")
        if m > 2:
            obj_range = fitness[front[idxs[-1]], obj] - fitness[front[idxs[0]], obj]
            if obj_range > 0:
                for i in range(1, m - 1):
                    dist[idxs[i]] += (fitness[front[idxs[i + 1]], obj] - fitness[front[idxs[i - 1]], obj]) / obj_range
    return dist


class NSGA2:
    """Non-dominated Sorting Genetic Algorithm II."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], np.ndarray],
        params: MOParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or MOParams()
        self.population: list[np.ndarray] = []
        self.fitness: np.ndarray = np.array([])
        self.history: list[int] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.population = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.fitness = np.array([self.evaluate(p) for p in self.population])

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size

        # Create offspring via tournament + SBX + PM
        offspring: list[np.ndarray] = []
        while len(offspring) < n:
            p1 = random.choice(self.population)
            p2 = random.choice(self.population)
            if random.random() < self.params.crossover_rate:
                c1, c2 = _sbx(p1, p2, self.params.crossover_index, low, high)
            else:
                c1, c2 = p1.copy(), p2.copy()
            c1 = _polynomial_mutation(c1, self.params.mutation_index, low, high, self.params.mutation_rate)
            c2 = _polynomial_mutation(c2, self.params.mutation_index, low, high, self.params.mutation_rate)
            offspring.append(c1)
            if len(offspring) < n:
                offspring.append(c2)

        # Combined population
        combined = self.population + offspring
        combined_fit = np.array([self.evaluate(p) for p in combined])

        # Non-dominated sort
        fronts = _non_dominated_sort(combined_fit)

        # Select next generation
        next_pop: list[np.ndarray] = []
        next_fit: list[np.ndarray] = []
        for front in fronts:
            if len(next_pop) + len(front) <= n:
                for i in front:
                    next_pop.append(combined[i])
                    next_fit.append(combined_fit[i])
            else:
                dist = _crowding_distance(combined_fit, front)
                order = np.argsort(-dist)
                remaining = n - len(next_pop)
                for i in order[:remaining]:
                    next_pop.append(combined[front[i]])
                    next_fit.append(combined_fit[front[i]])
                break

        self.population = next_pop
        self.fitness = np.array(next_fit)
        self.history.append(len(fronts[0]) if fronts else 0)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[list[np.ndarray], np.ndarray]:
        if not self.population:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.population, self.fitness

    def get_pareto_front(self) -> tuple[list[np.ndarray], np.ndarray]:
        fronts = _non_dominated_sort(self.fitness)
        pareto_idxs = fronts[0] if fronts else []
        return [self.population[i] for i in pareto_idxs], self.fitness[pareto_idxs]


class NSGA3(NSGA2):
    """NSGA-III — reference-point based many-objective EA."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], np.ndarray],
        n_ref_points: int = 10,
        params: MOParams | None = None,
    ) -> None:
        super().__init__(evaluate, params)
        self.n_ref_points = n_ref_points
        self.ref_points = self._generate_reference_points()

    def _generate_reference_points(self) -> np.ndarray:
        n_obj = self.params.n_objectives
        points = []
        for _ in range(self.n_ref_points):
            p = np.random.dirichlet(np.ones(n_obj))
            points.append(p)
        return np.array(points)


class MOEAD:
    """Multi-Objective Evolutionary Algorithm based on Decomposition."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], np.ndarray],
        params: MOParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or MOParams()
        self.population: list[np.ndarray] = []
        self.fitness: np.ndarray = np.array([])
        self.weights: np.ndarray = np.array([])
        self.neighbors: list[list[int]] = []
        self.neighbor_size: int = 20
        self.T: int = 20
        self.z_star: np.ndarray = np.array([])
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        n_obj = self.params.n_objectives
        self.population = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.fitness = np.array([self.evaluate(p) for p in self.population])
        self.weights = np.random.dirichlet(np.ones(n_obj), n)
        self.z_star = np.min(self.fitness, axis=0)
        # Compute neighbor indices
        for i in range(n):
            dists = [np.linalg.norm(self.weights[i] - self.weights[j]) for j in range(n)]
            self.neighbors.append(np.argsort(dists)[:self.neighbor_size].tolist())

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        for i in range(n):
            # Select parents from neighbors
            nb = self.neighbors[i]
            p1, p2 = random.sample(nb, 2)
            parent1, parent2 = self.population[p1], self.population[p2]
            if random.random() < self.params.crossover_rate:
                child, _ = _sbx(parent1, parent2, self.params.crossover_index, low, high)
            else:
                child = parent1.copy()
            child = _polynomial_mutation(child, self.params.mutation_index, low, high, self.params.mutation_rate)
            child_fit = self.evaluate(child)
            self.z_star = np.minimum(self.z_star, child_fit)
            # Update neighbors
            for j in nb:
                f1 = np.max(self.weights[j] * (self.fitness[j] - self.z_star))
                f2 = np.max(self.weights[j] * (child_fit - self.z_star))
                if f2 < f1:
                    self.population[j] = child.copy()
                    self.fitness[j] = child_fit
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[list[np.ndarray], np.ndarray]:
        if not self.population:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.population, self.fitness


class IBEA:
    """Indicator-Based Evolutionary Algorithm."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], np.ndarray],
        params: MOParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or MOParams()
        self.population: list[np.ndarray] = []
        self.fitness: np.ndarray = np.array([])
        self.kappa: float = 0.05
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.population = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.fitness = np.array([self.evaluate(p) for p in self.population])

    def _indicator(self, a: np.ndarray, b: np.ndarray) -> float:
        return min(a - b)  # Simplified epsilon indicator

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        # Binary tournament + variation
        offspring: list[np.ndarray] = []
        while len(offspring) < n:
            p1, p2 = random.choices(self.population, k=2)
            if random.random() < self.params.crossover_rate:
                c1, c2 = _sbx(p1, p2, self.params.crossover_index, low, high)
            else:
                c1, c2 = p1.copy(), p2.copy()
            offspring.append(_polynomial_mutation(c1, self.params.mutation_index, low, high, self.params.mutation_rate))
        combined = self.population + offspring
        combined_fit = np.array([self.evaluate(p) for p in combined])
        # Indicator-based fitness assignment
        n_combined = len(combined)
        ind_fitness = np.zeros(n_combined)
        for i in range(n_combined):
            for j in range(n_combined):
                if i != j:
                    ind_fitness[i] -= math.exp(-self._indicator(combined_fit[j], combined_fit[i]) / (self.kappa * n_combined))
        # Truncation
        order = np.argsort(ind_fitness)[:n]
        self.population = [combined[i] for i in order]
        self.fitness = combined_fit[order]
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[list[np.ndarray], np.ndarray]:
        if not self.population:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.population, self.fitness


class HypE:
    """Hypervolume Estimation Algorithm."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], np.ndarray],
        params: MOParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or MOParams()
        self.population: list[np.ndarray] = []
        self.fitness: np.ndarray = np.array([])
        self.n_samples: int = 10000
        self.generation = 0

    def _estimate_hypervolume(self, fit: np.ndarray, ref: np.ndarray) -> float:
        # Simple Monte Carlo hypervolume estimation
        n = len(fit)
        if n == 0:
            return 0.0
        dominated = 0
        for _ in range(self.n_samples):
            point = np.random.uniform(np.min(fit, axis=0), ref)
            dominated_flag = any(np.all(point >= f) for f in fit)
            if dominated_flag:
                dominated += 1
        vol = np.prod(ref - np.min(fit, axis=0)) * dominated / self.n_samples
        return vol

    def step(self) -> None:
        pass  # Placeholder

    def run(self, generations: int | None = None) -> tuple[list[np.ndarray], np.ndarray]:
        return self.population, self.fitness
