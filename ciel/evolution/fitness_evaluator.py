from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class HydraContext:
    task_success: float = 0.0
    user_satisfaction: float = 0.0
    cost_ratio: float = 0.0
    latency_ratio: float = 0.0
    evolutionary_pressure: float = 0.0
    metadata: dict[str, Any] | None = None


FITNESS_WEIGHTS = {
    "task_success": 0.40,
    "user_satisfaction": 0.30,
    "cost_efficiency": 0.20,
    "evolutionary_pressure": 0.10,
}


class DefaultFitnessEvaluator:
    def __init__(self) -> None:
        self._weights = dict(FITNESS_WEIGHTS)

    def evaluate(self, genome: Any, context: HydraContext | None = None) -> float:
        if context is None:
            return self._from_history(genome)
        task_score = max(0.0, min(1.0, context.task_success))
        user_score = max(0.0, min(1.0, context.user_satisfaction))
        cost_score = max(0.0, min(1.0, 1.0 - context.cost_ratio))
        latency_score = max(0.0, min(1.0, 1.0 - context.latency_ratio))
        efficiency_score = (cost_score + latency_score) / 2.0
        pressure_score = max(0.0, min(1.0, context.evolutionary_pressure))
        fitness = (
            task_score * self._weights["task_success"]
            + user_score * self._weights["user_satisfaction"]
            + efficiency_score * self._weights["cost_efficiency"]
            + pressure_score * self._weights["evolutionary_pressure"]
        )
        return max(0.0, min(1.0, fitness))

    def _from_history(self, genome: Any) -> float:
        history = getattr(genome, "fitness_history", [])
        fitness = getattr(genome, "fitness", 0.5)
        if not history:
            return fitness
        recent = history[-10:]
        avg = sum(recent) / len(recent)
        bonus = self._compute_diversity_bonus(genome) * 0.05
        return max(0.0, min(1.0, avg + bonus))

    def _compute_diversity_bonus(self, genome: Any) -> float:
        behavior = getattr(genome, "g_behavior", [])
        sample = behavior[:50]
        if not sample:
            return 0.0
        buckets = [0] * 10
        for gene in sample:
            val = getattr(gene, "value", 0.5)
            idx = min(9, int(val * 10))
            buckets[idx] += 1
        total = len(sample)
        entropy = 0.0
        for count in buckets:
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        return entropy / math.log2(10)

    def get_weights(self) -> dict[str, float]:
        return dict(self._weights)

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict):
            ctx = HydraContext(
                task_success=input_data.get("task_success", 0.0),
                user_satisfaction=input_data.get("user_satisfaction", 0.0),
                cost_ratio=input_data.get("cost_ratio", 0.0),
                latency_ratio=input_data.get("latency_ratio", 0.0),
                evolutionary_pressure=input_data.get("evolutionary_pressure", 0.0),
            )
            return {
                "weights": self._weights,
                "evaluator_type": "DefaultFitnessEvaluator",
            }
        return {"error": "No context provided"}
