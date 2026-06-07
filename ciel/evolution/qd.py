from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class QDParams:
    population_size: int = 100
    dimensions: int = 10
    generations: int = 500
    bounds: tuple[float, float] = (-10.0, 10.0)
    n_bins_per_dim: int = 10
    behaviour_dim: int = 2
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    iso_sigma: float = 0.01
    line_sigma: float = 0.1


class MAPElites:
    """Multi-dimensional Archive of Phenotypic Elites.

    Maintains a grid of high-performing solutions across behavior space.
    """

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        describe: Callable[[np.ndarray], np.ndarray],
        params: QDParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.describe = describe  # Maps solution -> behaviour descriptor
        self.params = params or QDParams()
        self.grid: dict[tuple[int, ...], tuple[np.ndarray, float]] = {}
        self.behaviour_bounds: list[tuple[float, float]] = [(-1.0, 1.0) for _ in range(self.params.behaviour_dim)]
        self.history: list[int] = []
        self.generation = 0

    def _discretize(self, bd: np.ndarray) -> tuple[int, ...]:
        return tuple(
            min(self.params.n_bins_per_dim - 1, max(0, int((bd[d] - self.behaviour_bounds[d][0]) / (self.behaviour_bounds[d][1] - self.behaviour_bounds[d][0]) * self.params.n_bins_per_dim)))
            for d in range(self.params.behaviour_dim)
        )

    def initialize(self) -> None:
        low, high = self.params.bounds
        dim = self.params.dimensions
        for _ in range(self.params.population_size):
            sol = np.random.uniform(low, high, dim)
            fit = self.evaluate(sol)
            bd = self.describe(sol)
            cell = self._discretize(bd)
            if cell not in self.grid or fit < self.grid[cell][1]:
                self.grid[cell] = (sol.copy(), fit)
        self.history.append(len(self.grid))

    def _variation(self, sol: np.ndarray) -> np.ndarray:
        low, high = self.params.bounds
        dim = self.params.dimensions
        if random.random() < self.params.crossover_rate and len(self.grid) > 1:
            other = random.choice(list(self.grid.values()))[0]
            alpha = random.random()
            child = alpha * sol + (1 - alpha) * other
        else:
            child = sol.copy()
        if random.random() < self.params.mutation_rate:
            iso = np.random.normal(0, self.params.iso_sigma, dim)
            line = np.random.normal(0, self.params.line_sigma) * np.random.randn(dim)
            child += iso + line
        return np.clip(child, low, high)

    def step(self) -> None:
        if random.random() < 0.5:
            # Exploration: random selection
            parent = random.choice(list(self.grid.values()))[0]
        else:
            # Exploitation: random elite
            parent = random.choice(list(self.grid.values()))[0]
        child = self._variation(parent)
        fit = self.evaluate(child)
        bd = self.describe(child)
        cell = self._discretize(bd)
        if cell not in self.grid or fit < self.grid[cell][1]:
            self.grid[cell] = (child.copy(), fit)
        self.history.append(len(self.grid))
        self.generation += 1

    def run(self, generations: int | None = None) -> dict[tuple[int, ...], tuple[np.ndarray, float]]:
        if not self.grid:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.grid

    def get_best(self) -> tuple[np.ndarray, float]:
        return min(self.grid.values(), key=lambda x: x[1])

    def get_coverage(self) -> float:
        return len(self.grid) / (self.params.n_bins_per_dim ** self.params.behaviour_dim)


class CVT_MAPElites(MAPElites):
    """MAP-Elites with Centroidal Voronoi Tesselation.

    Uses k-means centroids instead of a fixed grid.
    """

    def __init__(
        self,
        evaluate: Callable[[np.ndarray], float],
        describe: Callable[[np.ndarray], np.ndarray],
        n_centroids: int = 100,
        params: QDParams | None = None,
    ) -> None:
        super().__init__(evaluate, describe, params)
        self.n_centroids = n_centroids
        self.centroids: list[np.ndarray] = []

    def initialize(self) -> None:
        super().initialize()
        # Generate centroids via random sampling in behaviour space
        self.centroids = [np.random.uniform(-1, 1, self.params.behaviour_dim) for _ in range(self.n_centroids)]

    def _discretize(self, bd: np.ndarray) -> tuple[int, ...]:
        dists = [np.linalg.norm(bd - c) for c in self.centroids]
        return (int(np.argmin(dists)),)

    def get_coverage(self) -> float:
        return len(self.grid) / self.n_centroids


class AURORA:
    """AUtomated Representation Of Reliable Attributes.

    Placeholder — unsupervised discovery of behavior descriptors.
    """

    def __init__(self, params: QDParams | None = None) -> None:
        self.params = params or QDParams()

    def discover_bd(self, solutions: np.ndarray) -> np.ndarray:
        return solutions[:, :2]


class SAIL:
    """Surrogate-Assisted Illumination.

    Placeholder — uses surrogate model to guide search.
    """

    def __init__(self, params: QDParams | None = None) -> None:
        self.params = params or QDParams()
