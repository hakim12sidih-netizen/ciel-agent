from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class DetectorSet:
    detectors: list[np.ndarray]
    threshold: float = 0.1
    coverage: float = 0.0


class NegativeSelector:
    """Negative Selection Algorithm — détection d'anomalies par élimination des
    détecteurs qui reconnaissent le self."""

    def __init__(
        self,
        dimension: int = 10,
        threshold: float = 0.1,
        max_detectors: int = 1000,
    ) -> None:
        self.dimension = dimension
        self.threshold = threshold
        self.max_detectors = max_detectors
        self.detectors: list[np.ndarray] = []
        self._bounds: tuple[float, float] = (-1.0, 1.0)

    def generate(self, self_samples: np.ndarray, n_detectors: int = 100) -> DetectorSet:
        self.detectors = []
        low, high = self._bounds
        attempts = 0
        while len(self.detectors) < min(n_detectors, self.max_detectors) and attempts < n_detectors * 10:
            candidate = np.random.uniform(low, high, self.dimension)
            matches_self = any(
                np.linalg.norm(candidate - s) < self.threshold for s in self_samples
            )
            if not matches_self:
                self.detectors.append(candidate)
            attempts += 1
        coverage = len(self.detectors) / max(1, n_detectors)
        return DetectorSet(detectors=self.detectors, threshold=self.threshold, coverage=coverage)

    def detect(self, sample: np.ndarray) -> bool:
        if not self.detectors:
            return False
        return any(np.linalg.norm(sample - d) < self.threshold for d in self.detectors)

    def vdetector(self, self_samples: np.ndarray, target_coverage: float = 0.95, max_iterations: int = 10000) -> None:
        """Variable-sized detector generation for better coverage."""
        low, high = self._bounds
        self.detectors = []
        for _ in range(max_iterations):
            if len(self.detectors) >= self.max_detectors:
                break
            candidate = np.random.uniform(low, high, self.dimension)
            min_self_dist = min(np.linalg.norm(candidate - s) for s in self_samples)
            radius = min(min_self_dist, self.threshold * 2)
            if radius > self.threshold * 0.5:
                self.detectors.append(candidate)
