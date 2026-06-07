from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

import numpy as np


@dataclass(slots=True)
class FEPState:
    free_energy: float = 0.0
    entropy: float = 0.0
    complexity: float = 0.0
    accuracy: float = 0.0


@dataclass(slots=True)
class MarkovBlanket:
    internal_states: np.ndarray = field(default_factory=lambda: np.zeros(0))
    external_states: np.ndarray = field(default_factory=lambda: np.zeros(0))
    sensory_states: np.ndarray = field(default_factory=lambda: np.zeros(0))
    active_states: np.ndarray = field(default_factory=lambda: np.zeros(0))

    def partition(self) -> dict[str, np.ndarray]:
        return {
            "internal": self.internal_states,
            "external": self.external_states,
            "sensory": self.sensory_states,
            "active": self.active_states,
        }


@dataclass(slots=True)
class GenerativeModel:
    priors: np.ndarray = field(default_factory=lambda: np.zeros(0))
    preferences: np.ndarray = field(default_factory=lambda: np.zeros(0))
    likelihood: np.ndarray = field(default_factory=lambda: np.eye(1))
    transition: np.ndarray = field(default_factory=lambda: np.eye(1))


@dataclass(slots=True)
class BeliefState:
    mean: np.ndarray = field(default_factory=lambda: np.zeros(0))
    variance: np.ndarray = field(default_factory=lambda: np.ones(1))

    def entropy(self) -> float:
        return 0.5 * np.sum(np.log(2 * np.pi * np.e * self.variance))


@dataclass(slots=True)
class FreeEnergyAgent:
    dim_observations: int = 1
    dim_states: int = 1
    dim_policies: int = 1
    dim_params: int = 1

    model: GenerativeModel = field(default_factory=GenerativeModel)
    blanket: MarkovBlanket = field(default_factory=MarkovBlanket)
    belief: BeliefState = field(default_factory=BeliefState)
    state: FEPState = field(default_factory=FEPState)
    precision: float = 1.0
    learning_rate: float = 0.01
    history: list[FEPState] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.blanket.internal_states = np.zeros(self.dim_states)
        self.blanket.external_states = np.zeros(self.dim_states)
        self.blanket.sensory_states = np.zeros(self.dim_observations)
        self.blanket.active_states = np.zeros(self.dim_policies)
        self.belief.mean = np.zeros(self.dim_states)
        self.belief.variance = np.ones(self.dim_states)
        self.model.priors = np.zeros(self.dim_states)
        self.model.preferences = np.zeros(self.dim_observations)
        self.model.likelihood = np.eye(self.dim_observations, self.dim_states)
        self.model.transition = np.eye(self.dim_states)

    def variational_free_energy(
        self, obs: np.ndarray, posterior: BeliefState | None = None
    ) -> float:
        q = posterior or self.belief
        likelihood = self.model.likelihood @ q.mean
        log_likelihood = -0.5 * np.sum((obs - likelihood) ** 2) * self.precision
        kl_div = 0.5 * np.sum(
            np.log(self.model.priors / q.variance)
            + (q.variance + (q.mean - self.model.priors) ** 2) / self.model.priors
            - 1
        )
        F = -log_likelihood + kl_div
        self.state.free_energy = float(F)
        self.state.complexity = float(kl_div)
        self.state.accuracy = float(log_likelihood)
        return F

    def expected_free_energy(self, policy: np.ndarray, horizon: int = 1) -> float:
        expected_obs = self.model.likelihood @ (self.model.transition @ policy)
        epistemic_value = 0.5 * np.sum(np.log(self.belief.variance))
        pragmatic_value = -0.5 * np.sum((expected_obs - self.model.preferences) ** 2)
        G = -epistemic_value - pragmatic_value
        return float(G)

    def perceive(self, obs: np.ndarray, steps: int = 10) -> float:
        for _ in range(steps):
            pred_error = obs - self.model.likelihood @ self.belief.mean
            weighted_error = self.precision * pred_error
            gradient = self.model.likelihood.T @ weighted_error - (self.belief.mean - self.model.priors)
            self.belief.mean += self.learning_rate * gradient
            self.variational_free_energy(obs)
        self.blanket.sensory_states = obs
        return self.state.free_energy

    def select_policy(self, policies: np.ndarray | None = None) -> np.ndarray:
        if policies is None:
            policies = np.eye(self.dim_policies)
        G_values = np.array([self.expected_free_energy(p) for p in policies])
        beta = self.precision
        policy_probs = np.exp(-beta * G_values)
        policy_probs /= policy_probs.sum()
        best_idx = np.argmax(policy_probs)
        self.blanket.active_states = policies[best_idx]
        return policies[best_idx]

    def act(self, policy: np.ndarray) -> np.ndarray:
        action = self.model.transition @ policy
        self.blanket.active_states = action
        return action

    def active_inference_step(self, obs: np.ndarray) -> np.ndarray:
        self.perceive(obs)
        policy = self.select_policy()
        action = self.act(policy)
        self.state.entropy = float(self.belief.entropy())
        self.history.append(FEPState(**{k: v for k, v in self.state.__dict__.items()}))
        return action
