from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class CoevParams:
    pop_a_size: int = 50
    pop_b_size: int = 50
    dimensions: int = 10
    generations: int = 200
    bounds: tuple[float, float] = (-10.0, 10.0)
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8


class Coevolution:
    """Generic competitive/cooperative coevolution."""

    def __init__(
        self,
        evaluate_a: Callable[[np.ndarray, np.ndarray], float],
        evaluate_b: Callable[[np.ndarray, np.ndarray], float] | None = None,
        params: CoevParams | None = None,
    ) -> None:
        self.evaluate_a = evaluate_a
        self.evaluate_b = evaluate_b or (lambda b, a: -evaluate_a(a, b))
        self.params = params or CoevParams()
        self.pop_a: list[np.ndarray] = []
        self.pop_b: list[np.ndarray] = []
        self.fitness_a: list[float] = []
        self.fitness_b: list[float] = []
        self.generation = 0

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        self.pop_a = [np.random.uniform(low, high, dim) for _ in range(self.params.pop_a_size)]
        self.pop_b = [np.random.uniform(low, high, dim) for _ in range(self.params.pop_b_size)]

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        na, nb = len(self.pop_a), len(self.pop_b)

        self.fitness_a = []
        self.fitness_b = []
        for a in self.pop_a:
            opponent = random.choice(self.pop_b)
            self.fitness_a.append(self.evaluate_a(a, opponent))
        for b in self.pop_b:
            opponent = random.choice(self.pop_a)
            self.fitness_b.append(self.evaluate_b(b, opponent))

        new_a: list[np.ndarray] = []
        idxs_a = np.argsort(self.fitness_a)[:na // 2]
        for i in idxs_a:
            new_a.append(self.pop_a[i].copy())
        while len(new_a) < na:
            p1 = random.choice(idxs_a)
            p2 = random.choice(idxs_a)
            if random.random() < self.params.crossover_rate:
                alpha = random.random()
                child = alpha * self.pop_a[p1] + (1 - alpha) * self.pop_a[p2]
            else:
                child = self.pop_a[p1].copy()
            if random.random() < self.params.mutation_rate:
                child += np.random.normal(0, 0.1, dim)
            new_a.append(np.clip(child, low, high))
        self.pop_a = new_a

        new_b: list[np.ndarray] = []
        idxs_b = np.argsort(self.fitness_b)[:nb // 2]
        for i in idxs_b:
            new_b.append(self.pop_b[i].copy())
        while len(new_b) < nb:
            p1 = random.choice(idxs_b)
            p2 = random.choice(idxs_b)
            if random.random() < self.params.crossover_rate:
                alpha = random.random()
                child = alpha * self.pop_b[p1] + (1 - alpha) * self.pop_b[p2]
            else:
                child = self.pop_b[p1].copy()
            if random.random() < self.params.mutation_rate:
                child += np.random.normal(0, 0.1, dim)
            new_b.append(np.clip(child, low, high))
        self.pop_b = new_b
        self.generation += 1

    def run(self, generations: int | None = None) -> tuple[list[np.ndarray], list[np.ndarray]]:
        if not self.pop_a:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.pop_a, self.pop_b


class PredatorPrey(Coevolution):
    """Predator-prey coevolution specialization."""

    def step(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        na, nb = len(self.pop_a), len(self.pop_b)
        self.fitness_a = []
        self.fitness_b = []
        for i, a in enumerate(self.pop_a):
            best_prey = min(self.pop_b, key=lambda p: np.linalg.norm(a - p))
            self.fitness_a.append(-np.linalg.norm(a - best_prey))
        for i, b in enumerate(self.pop_b):
            best_pred = min(self.pop_a, key=lambda p: np.linalg.norm(p - b))
            self.fitness_b.append(np.linalg.norm(b - best_pred))
        idxs_a = np.argsort(self.fitness_a)[:na // 2]
        idxs_b = np.argsort(self.fitness_b)[:nb // 2]
        new_a = [self.pop_a[i].copy() for i in idxs_a]
        new_b = [self.pop_b[i].copy() for i in idxs_b]
        while len(new_a) < na:
            child = random.choice(new_a).copy() + np.random.normal(0, 0.1, dim)
            new_a.append(np.clip(child, low, high))
        while len(new_b) < nb:
            child = random.choice(new_b).copy() + np.random.normal(0, 0.1, dim)
            new_b.append(np.clip(child, low, high))
        self.pop_a = new_a
        self.pop_b = new_b
        self.generation += 1


class HallOfFame:
    """Maintains a set of diverse high-performing solutions."""

    def __init__(self, max_size: int = 20, novelty_weight: float = 0.5) -> None:
        self.members: list[tuple[np.ndarray, float]] = []
        self.max_size = max_size
        self.novelty_weight = novelty_weight

    def add(self, solution: np.ndarray, fitness: float) -> None:
        score = fitness
        if len(self.members) > 0:
            min_dist = min(np.linalg.norm(solution - m[0]) for m in self.members)
            score -= self.novelty_weight * min_dist
        self.members.append((solution.copy(), score))
        self.members.sort(key=lambda x: x[1])
        if len(self.members) > self.max_size:
            self.members = self.members[:self.max_size]

    def get_diverse_set(self, n: int) -> list[np.ndarray]:
        return [m[0] for m in self.members[:n]]
