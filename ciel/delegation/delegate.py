from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from ciel.delegation.kanban import Kanban, TaskStatus

logger = logging.getLogger(__name__)


class Delegator:
    """Délégation de tâches à des sous-agents.

    Permet à un agent CIEL de déléguer une tâche complexe à un
    sous-agent isolé (leaf/orchestrator) et de récupérer le résultat.

    Inspiré du pattern OpenClaw leaf-agent.
    """

    def __init__(self, kanban: Kanban | None = None):
        self.kanban = kanban or Kanban()

    def delegate_task(self, description: str, agent_id: str = "",
                      workspace_id: str = "", priority: int = 0,
                      context: dict | None = None) -> str:
        """Délègue une tâche à un sous-agent.

        Retourne l'ID de la tâche pour suivi.
        """
        tid = self.kanban.enqueue(
            description=description,
            agent_id=agent_id,
            workspace_id=workspace_id,
            priority=priority,
            metadata={"context": context or {}},
        )
        logger.info(f"Delegated task {tid}: {description[:80]}")
        return tid

    def get_result(self, task_id: str, timeout: float = 60.0,
                   poll_interval: float = 0.5) -> dict[str, Any]:
        """Attend le résultat d'une tâche déléguée.

        Polling jusqu'à timeout.
        """
        start = time.time()
        while time.time() - start < timeout:
            task = self.kanban.get(task_id)
            if not task:
                return {"error": "task not found"}
            if task.status == TaskStatus.DONE:
                return {"success": True, "result": task.result, "duration": task._duration()}
            if task.status == TaskStatus.FAILED:
                return {"success": False, "error": task.error}
            if task.status == TaskStatus.CANCELLED:
                return {"success": False, "error": "cancelled"}
            time.sleep(poll_interval)
        return {"error": f"timeout after {timeout}s"}

    def batch(self, tasks: list[dict[str, Any]]) -> list[str]:
        """Délègue un lot de tâches en une fois."""
        ids = []
        for t in tasks:
            tid = self.delegate_task(
                description=t.get("description", ""),
                agent_id=t.get("agent_id", ""),
                workspace_id=t.get("workspace_id", ""),
                priority=t.get("priority", 0),
                context=t.get("context"),
            )
            ids.append(tid)
        return ids

    def summary(self) -> dict:
        return self.kanban.stats()
