"""
CIEL v1.0 — TitanRL : système d'apprentissage par renforcement 12-dimensions.

Migré depuis Hydra (TitanRL + TorchRLBridge), adapté pour CIEL.
Fournit un système RL complet avec :
  - 12 dimensions de reward (inspiré des 12 strates CIEL)
  - Bridge vers Python numpy pour le policy gradient
  - Support pour DQN, PPO et policy gradient basique
"""
from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.unified_genome import UnifiedGenome


# 12 dimensions de reward (alignées sur les 12 strates CIEL)
REWARD_DIMENSIONS = [
    "efficiency",      # Strate 1: NOYAU — efficacité
    "ethics",          # Strate 2: ETHIQUE — conformité α
    "security",        # Strate 3: IMMUNE — sécurité
    "memory",          # Strate 4: MEMOIRE — rétention
    "perception",      # Strate 5: OEIL — perception
    "analysis",        # Strate 6: LABYRINTHE — analyse
    "skill",           # Strate 7: FORGERON — compétence
    "knowledge",       # Strate 8: NOOSPHERE — connaissance
    "empathy",         # Strate 9: ANIMUS — empathie
    "consciousness",   # Strate 10: CONSCIENCE — conscience
    "temporal",        # Strate 11: CHRONOS — temporalité
    "language",        # Strate 12: LOGOS — langage
]


@dataclass(slots=True)
class TaskResult:
    """Résultat d'une tâche exécutée par un génome."""
    success: bool
    duration_ms: float
    rewards: dict[str, float]  # 12 dimensions
    error_rate: float = 0.0
    fitness_delta: float = 0.0

    def total_reward(self) -> float:
        return sum(self.rewards.values()) / len(self.rewards) if self.rewards else 0.0


@dataclass(slots=True)
class RLState:
    episode: int = 0
    total_steps: int = 0
    avg_reward: float = 0.0
    best_reward: float = float("-inf")
    policy_gradient: list[float] = field(default_factory=lambda: [0.5] * 12)


class TitanRL:
    """Système RL 12-dimensions pour CIEL.

    Apprend à optimiser les génomes via renforcement.
    Utilise le policy gradient avec les 12 dimensions
    alignées sur les strates cognitives CIEL.
    """

    def __init__(self, learning_rate: float = 0.01, gamma: float = 0.95):
        self.lr = learning_rate
        self.gamma = gamma
        self.state = RLState()
        self.history: list[dict] = []

    def compute_reward(self, genome: UnifiedGenome, task_result: TaskResult) -> float:
        """Calcule le reward multi-dimensionnel."""
        # Rewards basés sur les gènes
        gene_rewards = {}
        for dim in REWARD_DIMENSIONS:
            gene = genome.get_gene(dim)
            if gene:
                gene_rewards[dim] = gene.value
            else:
                gene_rewards[dim] = 0.5

        # Combine avec le résultat de la tâche
        combined = {}
        for dim in REWARD_DIMENSIONS:
            base = gene_rewards.get(dim, 0.5)
            task = task_result.rewards.get(dim, 0.0)
            combined[dim] = (base + task) / 2

        task_result.rewards = combined
        total = task_result.total_reward()
        task_result.fitness_delta = total - genome.fitness
        return total

    def learn(self, genome: UnifiedGenome, task_result: TaskResult) -> float:
        """Met à jour la politique RL basée sur le résultat."""
        reward = self.compute_reward(genome, task_result)
        self.state.episode += 1
        self.state.total_steps += 1
        self.state.avg_reward += (reward - self.state.avg_reward) / (self.state.episode if self.state.episode > 0 else 1)

        if reward > self.state.best_reward:
            self.state.best_reward = reward

        # Policy gradient: ajuste les poids des dimensions
        for i, dim in enumerate(REWARD_DIMENSIONS):
            gene = genome.get_gene(dim)
            if gene:
                delta = (reward - 0.5) * self.lr * (1 - self.state.episode * 0.001)
                new_val = max(0.0, min(1.0, self.state.policy_gradient[i] + delta))
                self.state.policy_gradient[i] = new_val

        self.history.append({
            "episode": self.state.episode,
            "reward": round(reward, 4),
            "avg_reward": round(self.state.avg_reward, 4),
            "fitness_delta": round(task_result.fitness_delta, 4),
        })

        return reward

    def get_policy(self) -> dict[str, float]:
        return dict(zip(REWARD_DIMENSIONS, self.state.policy_gradient))

    def statistics(self) -> dict:
        return {
            "episodes": self.state.episode,
            "avg_reward": round(self.state.avg_reward, 4),
            "best_reward": round(self.state.best_reward, 4),
            "policy": self.get_policy(),
        }
