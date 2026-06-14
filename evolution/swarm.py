from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class SwarmParams:
    population_size: int = 30
    dimensions: int = 10
    generations: int = 200
    bounds: tuple[float, float] = (-10.0, 10.0)
    w: float = 0.7
    c1: float = 1.5
    c2: float = 1.5
    limit: float | None = None  # For ABC limit


class Particle:
    __slots__ = ("position", "velocity", "fitness", "best_position", "best_fitness")

    def __init__(self, position: np.ndarray, velocity: np.ndarray) -> None:
        self.position = position
        self.velocity = velocity
        self.fitness = float("inf")
        self.best_position = position.copy()
        self.best_fitness = float("inf")


class PSO:
    """Particle Swarm Optimization."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        params: SwarmParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams()
        self.swarm: list[Particle] = []
        self.global_best_position: np.ndarray = np.array([])
        self.global_best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        self.swarm = []
        for _ in range(self.params.population_size):
            pos = np.random.uniform(low, high, dim)
            vel = np.random.uniform(-abs(high - low) * 0.1, abs(high - low) * 0.1, dim)
            p = Particle(pos, vel)
            p.fitness = self.evaluate(pos)
            p.best_fitness = p.fitness
            self.swarm.append(p)
        self.global_best_position = min(self.swarm, key=lambda x: x.fitness).best_position.copy()
        self.global_best_fitness = min(p.fitness for p in self.swarm)
        self.history.append(self.global_best_fitness)

    def step(self) -> None:
        w = self.params.w
        c1 = self.params.c1
        c2 = self.params.c2
        low, high = self.params.bounds
        for p in self.swarm:
            r1, r2 = random.random(), random.random()
            p.velocity = w * p.velocity + c1 * r1 * (p.best_position - p.position) + c2 * r2 * (self.global_best_position - p.position)
            p.position = np.clip(p.position + p.velocity, low, high)
            p.fitness = self.evaluate(p.position)
            if p.fitness < p.best_fitness:
                p.best_fitness = p.fitness
                p.best_position = p.position.copy()
            if p.fitness < self.global_best_fitness:
                self.global_best_fitness = p.fitness
                self.global_best_position = p.position.copy()
        self.history.append(self.global_best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.swarm:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.global_best_position, self.global_best_fitness


class ACO:
    """Ant Colony Optimization for continuous domains (ACOR)."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        params: SwarmParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=50)
        self.archive: list[tuple[np.ndarray, float, float]] = []  # (solution, fitness, weight)
        self.q: float = 0.5
        self.xi: float = 0.85
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        solutions = [np.random.uniform(low, high, dim) for _ in range(n)]
        fitnesses = [self.evaluate(s) for s in solutions]
        idxs = np.argsort(fitnesses)
        self.archive = []
        for i in idxs:
            w = (1.0 / (n * math.sqrt(2 * math.pi) * self.q)) * math.exp(-0.5 * ((i) / (self.q * n)) ** 2)
            self.archive.append((solutions[i], fitnesses[i], w))
        self.archive.sort(key=lambda x: x[1])
        self.history.append(self.archive[0][1])

    def _sample_gaussian(self, mean: float, sigma: float) -> float:
        return random.gauss(mean, sigma)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = len(self.archive)
        new_solutions: list[np.ndarray] = []
        for _ in range(n):
            # Select guiding solution via roulette on weights
            total_w = sum(w for _, _, w in self.archive)
            r = random.random() * total_w
            cum = 0.0
            chosen_idx = 0
            for i, (_, _, w) in enumerate(self.archive):
                cum += w
                if cum >= r:
                    chosen_idx = i
                    break
            guide = self.archive[chosen_idx][0]
            sigmas = np.zeros(dim)
            for d in range(dim):
                distances = [abs(self.archive[i][0][d] - guide[d]) for i in range(n)]
                sigmas[d] = self.xi * sum(distances) / (n - 1) if n > 1 else 0.1
            new_sol = np.array([self._sample_gaussian(guide[d], sigmas[d]) for d in range(dim)])
            new_sol = np.clip(new_sol, low, high)
            new_solutions.append(new_sol)
        new_fitnesses = [self.evaluate(s) for s in new_solutions]
        combined = list(zip(new_solutions, new_fitnesses))
        all_items = [(s, f) for s, f, _ in self.archive] + combined
        all_items.sort(key=lambda x: x[1])
        all_items = all_items[:n]
        self.archive = []
        for i, (s, f) in enumerate(all_items):
            w = (1.0 / (n * math.sqrt(2 * math.pi) * self.q)) * math.exp(-0.5 * ((i) / (self.q * n)) ** 2)
            self.archive.append((s, f, w))
        self.history.append(self.archive[0][1])
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.archive:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.archive[0][0], self.archive[0][1]


class ABC:
    """Artificial Bee Colony."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        params: SwarmParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=50, limit=100)
        self.limit = self.params.limit or 100
        self.food_sources: list[np.ndarray] = []
        self.fitness: list[float] = []
        self.trials: list[int] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.food_sources = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.fitness = [self.evaluate(s) for s in self.food_sources]
        self.trials = [0] * n
        best_idx = int(np.argmin(self.fitness))
        self.best_solution = self.food_sources[best_idx].copy()
        self.best_fitness = self.fitness[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size

        # Employed bees phase
        for i in range(n):
            phi = np.random.uniform(-1, 1, dim)
            k = random.choice([j for j in range(n) if j != i])
            new_sol = self.food_sources[i] + phi * (self.food_sources[i] - self.food_sources[k])
            new_sol = np.clip(new_sol, low, high)
            new_fit = self.evaluate(new_sol)
            if new_fit < self.fitness[i]:
                self.food_sources[i] = new_sol
                self.fitness[i] = new_fit
                self.trials[i] = 0
            else:
                self.trials[i] += 1

        # Onlooker bees phase
        total = sum(1.0 / (1.0 + f) for f in self.fitness)
        for _ in range(n):
            r = random.random() * total
            cum = 0.0
            chosen = 0
            for i, f in enumerate(self.fitness):
                cum += 1.0 / (1.0 + f)
                if cum >= r:
                    chosen = i
                    break
            phi = np.random.uniform(-1, 1, dim)
            k = random.choice([j for j in range(n) if j != chosen])
            new_sol = self.food_sources[chosen] + phi * (self.food_sources[chosen] - self.food_sources[k])
            new_sol = np.clip(new_sol, low, high)
            new_fit = self.evaluate(new_sol)
            if new_fit < self.fitness[chosen]:
                self.food_sources[chosen] = new_sol
                self.fitness[chosen] = new_fit
                self.trials[chosen] = 0
            else:
                self.trials[chosen] += 1

        # Scout bees phase
        for i in range(n):
            if self.trials[i] >= self.limit:
                self.food_sources[i] = np.random.uniform(low, high, dim)
                self.fitness[i] = self.evaluate(self.food_sources[i])
                self.trials[i] = 0

        best_idx = int(np.argmin(self.fitness))
        if self.fitness[best_idx] < self.best_fitness:
            self.best_fitness = self.fitness[best_idx]
            self.best_solution = self.food_sources[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.food_sources:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class CS:
    """Cuckoo Search via Lévy flights."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        params: SwarmParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=25)
        self.pa: float = 0.25
        self.alpha: float = 0.01
        self.nests: list[np.ndarray] = []
        self.fitness: list[float] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def _levy_flight(self, dim: int) -> np.ndarray:
        beta = 1.5
        sigma = (math.gamma(1 + beta) * math.sin(math.pi * beta / 2) / (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))) ** (1 / beta)
        u = np.random.normal(0, sigma, dim)
        v = np.random.normal(0, 1, dim)
        return u / (np.abs(v) ** (1 / beta))

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.nests = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.fitness = [self.evaluate(s) for s in self.nests]
        best_idx = int(np.argmin(self.fitness))
        self.best_solution = self.nests[best_idx].copy()
        self.best_fitness = self.fitness[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size

        for i in range(n):
            step = self.alpha * self._levy_flight(dim) * (self.nests[i] - self.best_solution)
            new_nest = np.clip(self.nests[i] + step, low, high)
            new_fit = self.evaluate(new_nest)
            j = random.randrange(n)
            if new_fit < self.fitness[j]:
                self.nests[j] = new_nest
                self.fitness[j] = new_fit

        # Abandon worst nests
        for i in range(n):
            if random.random() < self.pa:
                self.nests[i] = np.random.uniform(low, high, dim)
                self.fitness[i] = self.evaluate(self.nests[i])

        best_idx = int(np.argmin(self.fitness))
        if self.fitness[best_idx] < self.best_fitness:
            self.best_solution = self.nests[best_idx].copy()
            self.best_fitness = self.fitness[best_idx]
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.nests:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class GWO:
    """Grey Wolf Optimizer."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        params: SwarmParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=30)
        self.wolves: list[np.ndarray] = []
        self.alpha: tuple[np.ndarray, float] = (np.array([]), float("inf"))
        self.beta: tuple[np.ndarray, float] = (np.array([]), float("inf"))
        self.delta: tuple[np.ndarray, float] = (np.array([]), float("inf"))
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.wolves = [np.random.uniform(low, high, dim) for _ in range(n)]
        self._update_hierarchy()
        self.history.append(self.alpha[1])

    def _update_hierarchy(self) -> None:
        fitnesses = [(i, self.evaluate(w)) for i, w in enumerate(self.wolves)]
        fitnesses.sort(key=lambda x: x[1])
        self.alpha = (self.wolves[fitnesses[0][0]].copy(), fitnesses[0][1])
        self.beta = (self.wolves[fitnesses[1][0]].copy(), fitnesses[1][1])
        self.delta = (self.wolves[fitnesses[2][0]].copy(), fitnesses[2][1])

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        a = 2.0 - 2.0 * self.generation / self.params.generations
        new_wolves: list[np.ndarray] = []
        for i in range(n):
            r1, r2 = random.random(), random.random()
            A1, C1 = 2 * a * r1 - a, 2 * r2
            D_alpha = abs(C1 * self.alpha[0] - self.wolves[i])
            X1 = self.alpha[0] - A1 * D_alpha
            r1, r2 = random.random(), random.random()
            A2, C2 = 2 * a * r1 - a, 2 * r2
            D_beta = abs(C2 * self.beta[0] - self.wolves[i])
            X2 = self.beta[0] - A2 * D_beta
            r1, r2 = random.random(), random.random()
            A3, C3 = 2 * a * r1 - a, 2 * r2
            D_delta = abs(C3 * self.delta[0] - self.wolves[i])
            X3 = self.delta[0] - A3 * D_delta
            new_pos = np.clip((X1 + X2 + X3) / 3.0, low, high)
            new_wolves.append(new_pos)
        self.wolves = new_wolves
        self._update_hierarchy()
        self.history.append(self.alpha[1])
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.wolves:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.alpha[0], self.alpha[1]


class WOA:
    """Whale Optimization Algorithm."""

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        params: SwarmParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=30)
        self.whales: list[np.ndarray] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.whales = [np.random.uniform(low, high, dim) for _ in range(n)]
        fit = [self.evaluate(w) for w in self.whales]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.whales[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        a = 2.0 - 2.0 * self.generation / self.params.generations
        a2 = -1.0 + self.generation * (-1.0) / self.params.generations
        new_whales: list[np.ndarray] = []
        for i in range(n):
            r1, r2 = random.random(), random.random()
            A = 2 * a * r1 - a
            C = 2 * r2
            b, l = 1.0, random.uniform(-1, 1)
            p = random.random()
            if p < 0.5:
                if abs(A) < 1:
                    D = abs(C * self.best_solution - self.whales[i])
                    new_pos = self.best_solution - A * D
                else:
                    rand_idx = random.randrange(n)
                    rand_whale = self.whales[rand_idx]
                    D = abs(C * rand_whale - self.whales[i])
                    new_pos = rand_whale - A * D
            else:
                D_prime = abs(self.best_solution - self.whales[i])
                new_pos = D_prime * math.exp(b * l) * math.cos(2 * math.pi * l) + self.best_solution
            new_whales.append(np.clip(new_pos, low, high))
        self.whales = new_whales
        fit = [self.evaluate(w) for w in self.whales]
        best_idx = int(np.argmin(fit))
        if fit[best_idx] < self.best_fitness:
            self.best_fitness = fit[best_idx]
            self.best_solution = self.whales[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.whales:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


# Simplified stubs for remaining swarm algorithms
class GOA:
    """Grasshopper Optimization Algorithm."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=30)
        self.grasshoppers: list[np.ndarray] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.grasshoppers = [np.random.uniform(low, high, dim) for _ in range(n)]
        fit = [self.evaluate(g) for g in self.grasshoppers]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.grasshoppers[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        c_max, c_min = 1.0, 0.00001
        c = c_max - self.generation * (c_max - c_min) / self.params.generations
        new_hoppers: list[np.ndarray] = []
        for i in range(n):
            Si = np.zeros(dim)
            for j in range(n):
                if i == j:
                    continue
                d = np.linalg.norm(self.grasshoppers[j] - self.grasshoppers[i])
                if d < 1e-10:
                    d = 1e-10
                xij = (self.grasshoppers[j] - self.grasshoppers[i]) / d
                f = c * c / 2.0 * math.exp(-d / c) * d  # simplified attraction
                Si += f * xij
            new_pos = c * Si + self.best_solution
            new_hoppers.append(np.clip(new_pos, low, high))
        self.grasshoppers = new_hoppers
        fit = [self.evaluate(g) for g in self.grasshoppers]
        best_idx = int(np.argmin(fit))
        if fit[best_idx] < self.best_fitness:
            self.best_fitness = fit[best_idx]
            self.best_solution = self.grasshoppers[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.grasshoppers:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class MFO:
    """Moth-Flame Optimization."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=30)
        self.moths: list[np.ndarray] = []
        self.flames: list[np.ndarray] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.moths = [np.random.uniform(low, high, dim) for _ in range(n)]
        fit = [(i, self.evaluate(m)) for i, m in enumerate(self.moths)]
        fit.sort(key=lambda x: x[1])
        self.flames = [self.moths[i].copy() for i, _ in fit]
        self.best_solution = self.flames[0].copy()
        self.best_fitness = fit[0][1]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        flame_no = round(n - self.generation * (n - 1) / self.params.generations)
        a = -1.0 + self.generation * (-1.0) / self.params.generations
        for i in range(n):
            t = random.uniform(-1, 1) * (a - 1) * random.random() + 1
            distance_to_flame = abs(self.flames[min(i, flame_no - 1)] - self.moths[i])
            self.moths[i] = distance_to_flame * math.exp(t) * math.cos(2 * math.pi * t) + self.flames[min(i, flame_no - 1)]
            self.moths[i] = np.clip(self.moths[i], low, high)
        fit = [(i, self.evaluate(m)) for i, m in enumerate(self.moths)]
        fit.sort(key=lambda x: x[1])
        all_sols = [(self.moths[i].copy(), fit[i][1]) for i in range(n)] + [(self.flames[i].copy(), self.evaluate(self.flames[i])) for i in range(n)]
        all_sols.sort(key=lambda x: x[1])
        self.flames = [s.copy() for s, _ in all_sols[:n]]
        self.best_solution = self.flames[0].copy()
        self.best_fitness = all_sols[0][1]
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.moths:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class SCA:
    """Sine Cosine Algorithm."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=30)
        self.positions: list[np.ndarray] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.positions = [np.random.uniform(low, high, dim) for _ in range(n)]
        fit = [self.evaluate(p) for p in self.positions]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.positions[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        a = 2.0 - 2.0 * self.generation / self.params.generations
        r1 = a
        for i in range(n):
            r2, r3, r4 = random.random() * 2 * math.pi, random.random() * 2, random.random()
            if r4 < 0.5:
                self.positions[i] = self.positions[i] + r1 * math.sin(r2) * abs(r3 * self.best_solution - self.positions[i])
            else:
                self.positions[i] = self.positions[i] + r1 * math.cos(r2) * abs(r3 * self.best_solution - self.positions[i])
            self.positions[i] = np.clip(self.positions[i], low, high)
        fit = [self.evaluate(p) for p in self.positions]
        best_idx = int(np.argmin(fit))
        if fit[best_idx] < self.best_fitness:
            self.best_fitness = fit[best_idx]
            self.best_solution = self.positions[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.positions:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class SSA:
    """Salp Swarm Algorithm."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=30)
        self.salps: list[np.ndarray] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.salps = [np.random.uniform(low, high, dim) for _ in range(n)]
        fit = [self.evaluate(s) for s in self.salps]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.salps[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        c1 = 2 * math.exp(-(4 * self.generation / self.params.generations) ** 2)
        for i in range(n):
            if i == 0:
                for j in range(dim):
                    c2, c3 = random.random(), random.random()
                    if c3 < 0.5:
                        self.salps[i][j] = self.best_solution[j] + c1 * ((high - low) * c2 + low)
                    else:
                        self.salps[i][j] = self.best_solution[j] - c1 * ((high - low) * c2 + low)
            else:
                self.salps[i] = (self.salps[i] + self.salps[i - 1]) / 2.0
            self.salps[i] = np.clip(self.salps[i], low, high)
        fit = [self.evaluate(s) for s in self.salps]
        best_idx = int(np.argmin(fit))
        if fit[best_idx] < self.best_fitness:
            self.best_fitness = fit[best_idx]
            self.best_solution = self.salps[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.salps:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class FFA:
    """Firefly Algorithm."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=25)
        self.beta0: float = 1.0
        self.gamma: float = 1.0
        self.alpha_firefly: float = 0.2
        self.fireflies: list[np.ndarray] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.fireflies = [np.random.uniform(low, high, dim) for _ in range(n)]
        fit = [self.evaluate(f) for f in self.fireflies]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.fireflies[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        intensities = [self.evaluate(f) for f in self.fireflies]
        for i in range(n):
            for j in range(n):
                if intensities[j] < intensities[i]:
                    r2 = np.sum((self.fireflies[i] - self.fireflies[j]) ** 2)
                    beta = self.beta0 * math.exp(-self.gamma * r2)
                    self.fireflies[i] += beta * (self.fireflies[j] - self.fireflies[i]) + self.alpha_firefly * (np.random.rand(dim) - 0.5)
                    self.fireflies[i] = np.clip(self.fireflies[i], low, high)
                    intensities[i] = self.evaluate(self.fireflies[i])
        best_idx = int(np.argmin(intensities))
        if intensities[best_idx] < self.best_fitness:
            self.best_fitness = intensities[best_idx]
            self.best_solution = self.fireflies[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.fireflies:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class BA:
    """Bat Algorithm."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=25)
        self.Qmin, self.Qmax = 0.0, 2.0
        self.r0, self.A = 0.5, 0.5
        self.alpha_bat, self.gamma_bat = 0.9, 0.9
        self.bats: list[np.ndarray] = []
        self.velocities: list[np.ndarray] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.bats = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.velocities = [np.zeros(dim) for _ in range(n)]
        fit = [self.evaluate(b) for b in self.bats]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.bats[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        for i in range(n):
            Q = self.Qmin + (self.Qmax - self.Qmin) * random.random()
            self.velocities[i] += (self.bats[i] - self.best_solution) * Q
            self.bats[i] += self.velocities[i]
            if random.random() > self.r0:
                self.bats[i] = self.best_solution + 0.001 * np.random.randn(dim)
            self.bats[i] = np.clip(self.bats[i], low, high)
            new_fit = self.evaluate(self.bats[i])
            if new_fit < self.best_fitness and random.random() < self.A:
                self.best_fitness = new_fit
                self.best_solution = self.bats[i].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.bats:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class FSS:
    """Fish School Search."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=30)
        self.step_ind: float = 0.1
        self.step_vol: float = 0.01
        self.W_total: float = 0.0
        self.fish: list[np.ndarray] = []
        self.weights: list[float] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.fish = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.weights = [1.0] * n
        self.W_total = float(n)
        fit = [self.evaluate(f) for f in self.fish]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.fish[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        fit = [self.evaluate(f) for f in self.fish]
        # Individual movement
        for i in range(n):
            delta = np.random.uniform(-1, 1, dim) * self.step_ind
            new_pos = np.clip(self.fish[i] + delta, low, high)
            new_fit = self.evaluate(new_pos)
            if new_fit < fit[i]:
                self.fish[i] = new_pos
                fit[i] = new_fit
        # Feeding
        max_delta = max(fit) - min(fit) if max(fit) != min(fit) else 1.0
        for i in range(n):
            self.weights[i] += (max_delta - (fit[i] - min(fit))) / max_delta
            self.weights[i] = max(min(self.weights[i], 10.0), 0.1)
        self.W_total = sum(self.weights)
        best_idx = int(np.argmin(fit))
        if fit[best_idx] < self.best_fitness:
            self.best_fitness = fit[best_idx]
            self.best_solution = self.fish[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.fish:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class SSO:
    """Social Spider Optimization."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=50)
        self.pf: float = 0.7
        self.spiders: list[np.ndarray] = []
        self.genders: list[bool] = []  # True = male, False = female
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.spiders = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.genders = [random.random() < self.pf for _ in range(n)]
        fit = [self.evaluate(s) for s in self.spiders]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.spiders[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        fit = np.array([self.evaluate(s) for s in self.spiders])
        best_idx = int(np.argmin(fit))
        worst_idx = int(np.argmax(fit))
        best, worst = fit[best_idx], fit[worst_idx]
        norm_fit = (fit - worst) / (best - worst + 1e-10)
        weights = norm_fit / (np.sum(norm_fit) + 1e-10)
        new_spiders: list[np.ndarray] = []
        for i in range(n):
            if not self.genders[i]:  # Female
                vib_sum = np.zeros(dim)
                for j in range(n):
                    if i == j:
                        continue
                    d2 = np.sum((self.spiders[i] - self.spiders[j]) ** 2)
                    vib = weights[j] * math.exp(-d2) if d2 > 0 else 0
                    vib_sum += vib * (self.spiders[j] - self.spiders[i])
                new_pos = self.spiders[i] + vib_sum
            else:  # Male
                if weights[i] < np.median(weights):
                    female_idx = random.choice([j for j in range(n) if not self.genders[j]])
                    d2 = np.sum((self.spiders[i] - self.spiders[female_idx]) ** 2)
                    vib = weights[female_idx] * math.exp(-d2)
                    new_pos = self.spiders[i] + vib * (self.spiders[female_idx] - self.spiders[i]) + random.random() * (np.random.rand(dim) - 0.5)
                else:
                    new_pos = self.spiders[i] - random.random() * (np.random.rand(dim) - 0.5) * (self.spiders[i] - self.best_solution)
            new_spiders.append(np.clip(new_pos, low, high))
        self.spiders = new_spiders
        fit = [self.evaluate(s) for s in self.spiders]
        best_idx = int(np.argmin(fit))
        if fit[best_idx] < self.best_fitness:
            self.best_fitness = fit[best_idx]
            self.best_solution = self.spiders[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.spiders:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class HBA:
    """Honey Badger Algorithm."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=30)
        self.beta_hba: float = 6.0
        self.C_hba: float = 2.0
        self.badgers: list[np.ndarray] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.badgers = [np.random.uniform(low, high, dim) for _ in range(n)]
        fit = [self.evaluate(b) for b in self.badgers]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.badgers[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        alpha = 1.0 - self.generation / self.params.generations
        r = random.random()
        I = 1 if r < 0.5 else -1
        for i in range(n):
            r1, r2, r3, r4 = [random.random() for _ in range(4)]
            if r2 < 0.5:
                S = I * (r3 * (self.best_solution - self.badgers[i]) / (self.best_solution - self.badgers[i] + 1e-10))
                di = self.best_solution - self.badgers[i]
                F = self.beta_hba * S / (2 * math.pi * np.sum(di**2))
                new_pos = self.best_solution + F * alpha * I * r1 * di
            else:
                F = 1.0 / (1.0 + math.exp(-(self.generation - self.params.generations / 2) / self.params.generations))
                new_pos = self.best_solution + F * r1 * alpha * I * (np.random.uniform(low, high, dim))
            self.badgers[i] = np.clip(new_pos, low, high)
        fit = [self.evaluate(b) for b in self.badgers]
        best_idx = int(np.argmin(fit))
        if fit[best_idx] < self.best_fitness:
            self.best_fitness = fit[best_idx]
            self.best_solution = self.badgers[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.badgers:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class EHO:
    """Elephant Herding Optimization."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=100)
        self.n_clans: int = 5
        self.alpha_eho: float = 0.6
        self.beta_eho: float = 0.5
        self.elephants: list[np.ndarray] = []
        self.clans: list[int] = []
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.elephants = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.clans = [i % self.n_clans for i in range(n)]
        fit = [self.evaluate(e) for e in self.elephants]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.elephants[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        fit = [self.evaluate(e) for e in self.elephants]
        for clan in range(self.n_clans):
            clan_idxs = [i for i in range(n) if self.clans[i] == clan]
            if not clan_idxs:
                continue
            clan_fits = [fit[i] for i in clan_idxs]
            matriarch_idx = clan_idxs[int(np.argmin(clan_fits))]
            matriarch = self.elephants[matriarch_idx].copy()
            clan_center = np.mean([self.elephants[i] for i in clan_idxs], axis=0)
            for i in clan_idxs:
                if i == matriarch_idx:
                    self.elephants[i] = self.beta_eho * clan_center
                else:
                    self.elephants[i] += self.alpha_eho * (matriarch - self.elephants[i]) * np.random.rand(dim)
                self.elephants[i] = np.clip(self.elephants[i], low, high)
        fit = [self.evaluate(e) for e in self.elephants]
        best_idx = int(np.argmin(fit))
        if fit[best_idx] < self.best_fitness:
            self.best_fitness = fit[best_idx]
            self.best_solution = self.elephants[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not self.elephants:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness


class AHA:
    """Artificial Hummingbird Algorithm."""

    def __init__(self, evaluate: Callable[[np.ndarray], float], params: SwarmParams | None = None) -> None:
        self.evaluate = evaluate
        self.params = params or SwarmParams(population_size=30)
        self.best_solution: np.ndarray = np.array([])
        self.best_fitness: float = float("inf")
        self.history: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        self.hummingbirds = [np.random.uniform(low, high, dim) for _ in range(n)]
        self.visit_table = np.zeros((n, n))
        fit = [self.evaluate(h) for h in self.hummingbirds]
        best_idx = int(np.argmin(fit))
        self.best_solution = self.hummingbirds[best_idx].copy()
        self.best_fitness = fit[best_idx]
        self.history.append(self.best_fitness)

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        n = self.params.population_size
        fit = [self.evaluate(h) for h in self.hummingbirds]
        for i in range(n):
            # Guided foraging (simplified)
            target = random.choice([j for j in range(n) if j != i])
            D = self.hummingbirds[target] - self.hummingbirds[i]
            new_pos = self.hummingbirds[i] + random.random() * D
            new_pos = np.clip(new_pos, low, high)
            new_fit = self.evaluate(new_pos)
            if new_fit < fit[i]:
                self.hummingbirds[i] = new_pos
                fit[i] = new_fit
        best_idx = int(np.argmin(fit))
        if fit[best_idx] < self.best_fitness:
            self.best_fitness = fit[best_idx]
            self.best_solution = self.hummingbirds[best_idx].copy()
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[np.ndarray, float]:
        if not hasattr(self, "hummingbirds") or not self.hummingbirds:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_solution, self.best_fitness
