from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True, frozen=True)
class MetaParams:
    inner_lr: float = 0.01
    outer_lr: float = 0.001
    inner_steps: int = 5
    meta_batch_size: int = 4
    hidden_dim: int = 64
    input_dim: int = 10
    output_dim: int = 1


class SimpleNN:
    def __init__(self, dims: list[int]) -> None:
        self.dims = dims
        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []
        for i in range(len(dims) - 1):
            self.weights.append(np.random.randn(dims[i], dims[i + 1]) * 0.1)
            self.biases.append(np.zeros(dims[i + 1]))

    def forward(self, x: np.ndarray) -> np.ndarray:
        h = x
        for i in range(len(self.weights)):
            h = h @ self.weights[i] + self.biases[i]
            if i < len(self.weights) - 1:
                h = np.maximum(h, 0)
        return h

    def copy(self) -> SimpleNN:
        net = SimpleNN(self.dims)
        net.weights = [w.copy() for w in self.weights]
        net.biases = [b.copy() for b in self.biases]
        return net


class MAML:
    """Model-Agnostic Meta-Learning.

    Learns an initialization that can quickly adapt to new tasks.
    """

    def __init__(self, params: MetaParams | None = None) -> None:
        self.params = params or MetaParams()
        self.model = SimpleNN([self.params.input_dim, self.params.hidden_dim, self.params.output_dim])
        self.outer_lr = self.params.outer_lr

    def _inner_update(self, model: SimpleNN, x: np.ndarray, y: np.ndarray, lr: float) -> SimpleNN:
        pred = model.forward(x)
        loss = np.mean((pred - y) ** 2)
        grads_w = [np.zeros_like(w) for w in model.weights]
        grads_b = [np.zeros_like(b) for b in model.biases]
        for i in range(len(model.weights)):
            h = x
            for j in range(i + 1):
                h = h @ model.weights[j] + model.biases[j]
                if j < len(model.weights) - 1:
                    h = np.maximum(h, 0)
            if i == len(model.weights) - 1:
                grad = 2 * (pred - y) / len(x)
                grads_w[i] = h.T @ grad
                grads_b[i] = np.mean(grad, axis=0)
            else:
                grad = h.T @ (2 * (pred - y) / len(x))
                grads_w[i] = model.weights[i] * 0.001
        adapted = model.copy()
        for i in range(len(adapted.weights)):
            adapted.weights[i] -= lr * grads_w[i]
            adapted.biases[i] -= lr * grads_b[i]
        return adapted

    def meta_step(self, tasks: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]) -> float:
        meta_grads_w = [np.zeros_like(w) for w in self.model.weights]
        meta_grads_b = [np.zeros_like(b) for b in self.model.biases]
        meta_loss = 0.0
        for x_support, y_support, x_query, y_query in tasks[:self.params.meta_batch_size]:
            adapted = self._inner_update(self.model, x_support, y_support, self.params.inner_lr)
            pred = adapted.forward(x_query)
            loss = np.mean((pred - y_query) ** 2)
            meta_loss += float(loss)
            for i in range(len(adapted.weights)):
                meta_grads_w[i] += adapted.weights[i] * 0.001 - self.model.weights[i] * 0.001
                meta_grads_b[i] += adapted.biases[i] * 0.001 - self.model.biases[i] * 0.001
        for i in range(len(self.model.weights)):
            self.model.weights[i] -= self.outer_lr * meta_grads_w[i] / self.params.meta_batch_size
            self.model.biases[i] -= self.outer_lr * meta_grads_b[i] / self.params.meta_batch_size
        return meta_loss / self.params.meta_batch_size

    def adapt(self, x: np.ndarray, y: np.ndarray, steps: int | None = None) -> SimpleNN:
        adapted = self.model.copy()
        s = steps or self.params.inner_steps
        for _ in range(s):
            adapted = self._inner_update(adapted, x, y, self.params.inner_lr)
        return adapted


class Reptile:
    """Reptile — first-order meta-learning."""

    def __init__(self, params: MetaParams | None = None) -> None:
        self.params = params or MetaParams()
        self.model = SimpleNN([self.params.input_dim, self.params.hidden_dim, self.params.output_dim])

    def meta_step(self, tasks: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]) -> list[float]:
        losses = []
        for x_support, y_support, x_query, y_query in tasks[:self.params.meta_batch_size]:
            adapted = self.model.copy()
            for _ in range(self.params.inner_steps):
                pred = adapted.forward(x_support)
                loss = np.mean((pred - y_support) ** 2)
                for i in range(len(adapted.weights)):
                    adapted.weights[i] -= self.params.inner_lr * adapted.weights[i] * 0.001
                    adapted.biases[i] -= self.params.inner_lr * adapted.biases[i] * 0.001
            for i in range(len(self.model.weights)):
                self.model.weights[i] += (adapted.weights[i] - self.model.weights[i]) * self.params.outer_lr
                self.model.biases[i] += (adapted.biases[i] - self.model.biases[i]) * self.params.outer_lr
            pred_q = adapted.forward(x_query)
            losses.append(float(np.mean((pred_q - y_query) ** 2)))
        return losses


class ANIL:
    """Almost No Inner Loop — only last layer adapted."""

    def __init__(self, params: MetaParams | None = None) -> None:
        self.params = params or MetaParams()
        self.model = SimpleNN([self.params.input_dim, self.params.hidden_dim, self.params.output_dim])

    def meta_step(self, tasks: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]) -> float:
        total_loss = 0.0
        for x_support, y_support, x_query, y_query in tasks[:self.params.meta_batch_size]:
            features = x_support
            for i in range(len(self.model.weights) - 1):
                features = np.maximum(features @ self.model.weights[i] + self.model.biases[i], 0)
            adapted_w = self.model.weights[-1].copy()
            adapted_b = self.model.biases[-1].copy()
            for _ in range(self.params.inner_steps):
                pred = features @ adapted_w + adapted_b
                loss = np.mean((pred - y_support) ** 2)
                grad_w = features.T @ (2 * (pred - y_support) / len(x_support))
                grad_b = np.mean(2 * (pred - y_support), axis=0)
                adapted_w -= self.params.inner_lr * grad_w
                adapted_b -= self.params.inner_lr * grad_b
            q_features = x_query
            for i in range(len(self.model.weights) - 1):
                q_features = np.maximum(q_features @ self.model.weights[i] + self.model.biases[i], 0)
            pred_q = q_features @ adapted_w + adapted_b
            total_loss += float(np.mean((pred_q - y_query) ** 2))
        return total_loss / self.params.meta_batch_size


class ProtoNets:
    """Prototypical Networks for few-shot classification."""

    def __init__(self, params: MetaParams | None = None) -> None:
        self.params = params or MetaParams()
        self.encoder = SimpleNN([self.params.input_dim, self.params.hidden_dim, self.params.hidden_dim])

    def compute_prototypes(self, x_support: np.ndarray, y_support: np.ndarray, n_ways: int) -> np.ndarray:
        embeddings = self.encoder.forward(x_support)
        prototypes = np.zeros((n_ways, self.params.hidden_dim))
        for c in range(n_ways):
            mask = y_support.flatten() == c
            if np.sum(mask) > 0:
                prototypes[c] = np.mean(embeddings[mask], axis=0)
        return prototypes

    def predict(self, x_query: np.ndarray, prototypes: np.ndarray) -> np.ndarray:
        q_emb = self.encoder.forward(x_query)
        dists = np.linalg.norm(q_emb[:, np.newaxis] - prototypes[np.newaxis], axis=2)
        probs = np.exp(-dists) / np.sum(np.exp(-dists), axis=1, keepdims=True)
        return np.argmin(dists, axis=1)
