from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    agent_id: str = ""
    workspace_id: str = ""
    priority: int = 0
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "description": self.description[:100],
            "status": self.status.value, "agent_id": self.agent_id,
            "workspace_id": self.workspace_id, "priority": self.priority,
            "result": self.result[:200] if self.result else "",
            "error": self.error[:200] if self.error else "",
            "created_at": self.created_at, "duration": self._duration(),
        }

    def _duration(self) -> float:
        if self.completed_at and self.started_at:
            return round(self.completed_at - self.started_at, 2)
        return 0.0


class Kanban:
    """File d'attente multi-agents.

    Gère les tâches asynchrones avec priorités, dispatch entre agents,
    et persistance SQLite.
    """

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = Path(db_path or Path.home() / ".ciel" / "kanban.json")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        if not self._db_path.exists():
            return
        try:
            data = json.loads(self._db_path.read_text())
            for t in data.get("tasks", []):
                task = Task(
                    id=t["id"], description=t["description"],
                    status=TaskStatus(t.get("status", "pending")),
                    agent_id=t.get("agent_id", ""),
                    workspace_id=t.get("workspace_id", ""),
                    priority=t.get("priority", 0),
                    result=t.get("result", ""),
                    error=t.get("error", ""),
                    created_at=t.get("created_at", time.time()),
                    started_at=t.get("started_at", 0),
                    completed_at=t.get("completed_at", 0),
                    metadata=t.get("metadata", {}),
                )
                self._tasks[task.id] = task
        except Exception:
            pass

    def _save(self) -> None:
        data = {
            "tasks": [t.to_dict() for t in self._tasks.values()],
        }
        self._db_path.write_text(json.dumps(data, indent=2, default=str))

    def enqueue(self, description: str, agent_id: str = "",
                workspace_id: str = "", priority: int = 0,
                metadata: dict | None = None) -> str:
        tid = f"task-{uuid.uuid4().hex[:12]}"
        self._tasks[tid] = Task(
            id=tid, description=description, agent_id=agent_id,
            workspace_id=workspace_id, priority=priority,
            metadata=metadata or {},
        )
        self._save()
        return tid

    def dequeue(self, agent_id: str = "") -> Task | None:
        candidates = sorted(
            [t for t in self._tasks.values()
             if t.status == TaskStatus.PENDING
             and (not agent_id or not t.agent_id or t.agent_id == agent_id)],
            key=lambda t: (-t.priority, t.created_at),
        )
        if not candidates:
            return None
        task = candidates[0]
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        if agent_id:
            task.agent_id = agent_id
        self._save()
        return task

    def complete(self, task_id: str, result: str = "") -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.status = TaskStatus.DONE
        task.result = result
        task.completed_at = time.time()
        self._save()
        return True

    def fail(self, task_id: str, error: str = "") -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.status = TaskStatus.FAILED
        task.error = error
        task.completed_at = time.time()
        self._save()
        return True

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if not task or task.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return False
        task.status = TaskStatus.CANCELLED
        self._save()
        return True

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list(self, status: TaskStatus | None = None,
             agent_id: str = "") -> list[Task]:
        results = list(self._tasks.values())
        if status:
            results = [t for t in results if t.status == status]
        if agent_id:
            results = [t for t in results if t.agent_id == agent_id]
        return sorted(results, key=lambda t: (-t.priority, t.created_at))

    def stats(self) -> dict:
        total = len(self._tasks)
        by_status = {}
        for t in self._tasks.values():
            by_status[t.status.value] = by_status.get(t.status.value, 0) + 1
        return {
            "total": total,
            "by_status": by_status,
            "pending": len([t for t in self._tasks.values() if t.status == TaskStatus.PENDING]),
            "running": len([t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]),
        }
