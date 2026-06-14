"""
CIEL v1.0 — Overseer : agent superviseur.

Migré depuis Hydra (Overseer), adapté pour CIEL.
Supervise l'exécution, planifie les tâches,
coordonne les strates et assure la cohérence.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork
from ciel.evolution.unified_genome import UnifiedGenome


@dataclass(slots=True)
class Task:
    id: str
    name: str
    priority: int  # 1-10
    status: str  # pending, running, completed, failed
    assigned_to: str | None = None
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    result: dict[str, Any] = field(default_factory=dict)


class Overseer:
    """Agent superviseur CIEL.

    Responsabilités :
      - Planification des tâches
      - Coordination des strates
      - Supervision de l'exécution
      - Détection des anomalies
    """

    def __init__(self):
        self.id = f"OVERSEER-{uuid.uuid4().hex[:8]}"
        self.network = LeaderNetwork()
        self.tasks: list[Task] = []
        self._running: list[Task] = []
        self._max_concurrent = 5

    def plan(self, objective: str, sub_tasks: list[dict]) -> list[Task]:
        """Planifie une séquence de tâches."""
        planned = []
        for i, st in enumerate(sub_tasks):
            task = Task(
                id=f"TASK-{uuid.uuid4().hex[:12]}",
                name=st.get("name", f"task_{i}"),
                priority=st.get("priority", 5),
                status="pending",
            )
            self.tasks.append(task)
            planned.append(task)

        self.network.emit("overseer.plan", {
            "objective": objective,
            "task_count": len(planned),
            "overseer_id": self.id,
        })
        return planned

    def assign(self, task_id: str, agent_id: str) -> bool:
        for task in self.tasks:
            if task.id == task_id and task.status == "pending":
                task.assigned_to = agent_id
                task.status = "running"
                self._running.append(task)
                self.network.emit("overseer.assign", {
                    "task": task_id,
                    "agent": agent_id,
                })
                return True
        return False

    def complete(self, task_id: str, result: dict[str, Any]) -> bool:
        for task in self.tasks:
            if task.id == task_id and task.status == "running":
                task.status = "completed"
                task.completed_at = time.time()
                task.result = result
                if task in self._running:
                    self._running.remove(task)
                self.network.emit("overseer.complete", {
                    "task": task_id,
                    "result": result,
                })
                return True
        return False

    def fail(self, task_id: str, error: str) -> bool:
        for task in self.tasks:
            if task.id == task_id and task.status == "running":
                task.status = "failed"
                task.result = {"error": error}
                if task in self._running:
                    self._running.remove(task)
                return True
        return False

    def status(self) -> dict:
        return {
            "id": self.id,
            "total_tasks": len(self.tasks),
            "running": len(self._running),
            "completed": sum(1 for t in self.tasks if t.status == "completed"),
            "failed": sum(1 for t in self.tasks if t.status == "failed"),
            "pending": sum(1 for t in self.tasks if t.status == "pending"),
        }
