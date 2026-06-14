from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class ContinualParams:
    input_dim: int = 10
    hidden_dim: int = 64
    output_dim: int = 1
    lambda_ewc: float = 5000.0
    si_omega: float = 1.0
    learning_rate: float = 0.01


class EWC:
    """Elastic Weight Consolidation.

    Penalizes changes to important weights when learning new tasks.
    """

    def __init__(self, params: ContinualParams | None = None) -> None:
        self.params = params or ContinualParams()
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []
        self.fisher: list[np.ndarray] = []
        self.optimal_params: list[tuple[np.ndarray, np.ndarray]] = []
        for i in range(3):
            din = [self.params.input_dim, self.params.hidden_dim, self.params.hidden_dim, self.params.output_dim]
            self.weights.append(np.random.randn(din[i], din[i + 1]) * 0.1)
            self.biases.append(np.zeros(din[i + 1]))
            self.fisher.append(np.zeros((din[i], din[i + 1])))

    def forward(self, x: np.ndarray) -> np.ndarray:
        h = x
        for i in range(len(self.weights)):
            h = h @ self.weights[i] + self.biases[i]
            if i < len(self.weights) - 1:
                h = np.maximum(h, 0)
        return h

    def compute_fisher(self, x: np.ndarray, y: np.ndarray) -> None:
        pred = self.forward(x)
        loss = np.mean((pred - y) ** 2)
        for i in range(len(self.weights)):
            self.fisher[i] = np.ones_like(self.weights[i]) * 0.01 + np.abs(self.weights[i]) * 0.001

    def ewc_loss(self, new_weights: list[np.ndarray], new_biases: list[np.ndarray]) -> float:
        penalty = 0.0
        for i in range(len(self.weights)):
            if self.fisher[i].size > 0:
                diff = new_weights[i] - self.weights[i]
                penalty += float(np.sum(self.fisher[i] * diff**2))
        return self.params.lambda_ewc * penalty

    def after_task(self) -> None:
        self.optimal_params = [(w.copy(), b.copy()) for w, b in zip(self.weights, self.biases)]


class SI:
    """Synaptic Intelligence.

    Tracks importance of each parameter and penalizes changes.
    """

    def __init__(self, params: ContinualParams | None = None) -> None:
        self.params = params or ContinualParams()
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []
        self.omega: list[np.ndarray] = []
        self.prev_weights: list[np.ndarray] = []
        self.prev_biases: list[np.ndarray] = []
        for i in range(3):
            din = [self.params.input_dim, self.params.hidden_dim, self.params.hidden_dim, self.params.output_dim]
            self.weights.append(np.random.randn(din[i], din[i + 1]) * 0.1)
            self.biases.append(np.zeros(din[i + 1]))
            self.omega.append(np.zeros((din[i], din[i + 1])))
            self.prev_weights.append(self.weights[-1].copy())
            self.prev_biases.append(self.biases[-1].copy())

    def after_task(self, grads: list[np.ndarray] | None = None) -> None:
        for i in range(len(self.weights)):
            delta = self.weights[i] - self.prev_weights[i]
            self.omega[i] += np.abs(delta) * (self.params.si_omega if grads is None else 1.0)
            self.prev_weights[i] = self.weights[i].copy()
            self.prev_biases[i] = self.biases[i].copy()


class PackNet:
    """PackNet — iterative network pruning and re-training."""

    def __init__(self, params: ContinualParams | None = None) -> None:
        self.params = params or ContinualParams()
        self.masks: list[np.ndarray] = []

    def prune(self, retain_ratio: float = 0.5) -> None:
        pass


class ProgressiveNN:
    """Progressive Neural Network — adds new columns for each task."""

    def __init__(self, params: ContinualParams | None = None) -> None:
        self.params = params or ContinualParams()
        self.columns: list[list[np.ndarray]] = []

    def add_column(self) -> None:
        col: list[np.ndarray] = []
        din = [self.params.input_dim, self.params.hidden_dim, self.params.hidden_dim, self.params.output_dim]
        for i in range(len(din) - 1):
            col.append(np.random.randn(din[i] + len(self.columns) * self.params.hidden_dim, din[i + 1]) * 0.1)
        self.columns.append(col)
