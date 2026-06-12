from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepType(Enum):
    API_CALL = "api_call"
    AGENT = "agent"
    PARALLEL = "parallel"
    CONDITION = "condition"
    TRANSFORM = "transform"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class Step:
    id: str
    type: StepType
    description: str = ""

    endpoint: str = ""
    method: str = "GET"
    body: dict[str, Any] | None = None
    params: dict[str, str] | None = None

    agent_task: str = ""
    agent_config: dict[str, Any] | None = None

    condition_expr: str = ""

    next_steps: list[str] | None = None
    parallel_steps: list[str] | None = None
    on_success: str = ""
    on_failure: str = ""

    timeout: float = 300.0
    max_retries: int = 0
    retry_delay: float = 5.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "description": self.description,
            "endpoint": self.endpoint,
            "method": self.method,
            "body": self.body,
            "params": self.params,
            "agent_task": self.agent_task,
            "agent_config": self.agent_config,
            "condition_expr": self.condition_expr,
            "next_steps": self.next_steps,
            "parallel_steps": self.parallel_steps,
            "on_success": self.on_success,
            "on_failure": self.on_failure,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Step:
        raw = d["type"]
        st = StepType(raw) if isinstance(raw, str) else raw
        return cls(
            id=d["id"],
            type=st,
            description=d.get("description", ""),
            endpoint=d.get("endpoint", ""),
            method=d.get("method", "GET"),
            body=d.get("body"),
            params=d.get("params"),
            agent_task=d.get("agent_task", ""),
            agent_config=d.get("agent_config"),
            condition_expr=d.get("condition_expr", ""),
            next_steps=d.get("next_steps"),
            parallel_steps=d.get("parallel_steps"),
            on_success=d.get("on_success", ""),
            on_failure=d.get("on_failure", ""),
            timeout=d.get("timeout", 300.0),
            max_retries=d.get("max_retries", 0),
            retry_delay=d.get("retry_delay", 5.0),
        )


@dataclass
class Situation:
    type: str  # time, event, state, or-combination
    interval_seconds: float = 0.0
    event_name: str = ""
    state_module: str = ""
    state_condition: str = ""
    cron_expr: str = ""
    cooldown: float = 60.0

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "interval_seconds": self.interval_seconds,
            "event_name": self.event_name,
            "state_module": self.state_module,
            "state_condition": self.state_condition,
            "cron_expr": self.cron_expr,
            "cooldown": self.cooldown,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Situation:
        return cls(
            type=d.get("type", "time"),
            interval_seconds=d.get("interval_seconds", 0.0),
            event_name=d.get("event_name", ""),
            state_module=d.get("state_module", ""),
            state_condition=d.get("state_condition", ""),
            cron_expr=d.get("cron_expr", ""),
            cooldown=d.get("cooldown", 60.0),
        )


@dataclass
class Workflow:
    id: str
    description: str = ""
    group: str = ""
    steps: dict[str, Step] = field(default_factory=dict)
    entry_point: str = ""
    situations: list[Situation] = field(default_factory=list)
    enabled: bool = True
    timeout: float = 3600.0
    max_concurrency: int = 5

    def add_step(self, step: Step) -> None:
        self.steps[step.id] = step
        if not self.entry_point:
            self.entry_point = step.id

    def get_entry_step(self) -> Step | None:
        return self.steps.get(self.entry_point)

    def get_next_steps(self, step_id: str, result_status: str = "success") -> list[Step]:
        step = self.steps.get(step_id)
        if not step:
            return []
        if result_status == "success" and step.on_success:
            nxt = self.steps.get(step.on_success)
            return [nxt] if nxt else []
        if result_status == "failed" and step.on_failure:
            nxt = self.steps.get(step.on_failure)
            return [nxt] if nxt else []
        next_ids = step.next_steps or []
        return [s for sid in next_ids if (s := self.steps.get(sid))]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "group": self.group,
            "steps": {k: v.to_dict() if isinstance(v, Step) else v for k, v in self.steps.items()},
            "entry_point": self.entry_point,
            "situations": [s.to_dict() if isinstance(s, Situation) else s for s in self.situations],
            "enabled": self.enabled,
            "timeout": self.timeout,
            "max_concurrency": self.max_concurrency,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Workflow:
        wf = cls(
            id=d["id"],
            description=d.get("description", ""),
            group=d.get("group", ""),
            steps={k: Step.from_dict(v) for k, v in d.get("steps", {}).items()},
            entry_point=d.get("entry_point", ""),
            situations=[Situation.from_dict(s) for s in d.get("situations", [])],
            enabled=d.get("enabled", True),
            timeout=d.get("timeout", 3600.0),
            max_concurrency=d.get("max_concurrency", 5),
        )
        return wf


@dataclass
class StepResult:
    step_id: str
    status: StepStatus = StepStatus.PENDING
    output: Any = None
    error: str = ""
    started_at: float = 0.0
    ended_at: float = 0.0
    agent_id: str = ""

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "status": self.status.value if isinstance(self.status, StepStatus) else self.status,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "agent_id": self.agent_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> StepResult:
        return cls(
            step_id=d["step_id"],
            status=StepStatus(d["status"]) if isinstance(d.get("status"), str) else StepStatus.PENDING,
            output=d.get("output"),
            error=d.get("error", ""),
            started_at=d.get("started_at", 0.0),
            ended_at=d.get("ended_at", 0.0),
            agent_id=d.get("agent_id", ""),
        )


@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    current_step: str = ""
    results: dict[str, StepResult] = field(default_factory=dict)
    started_at: float = 0.0
    ended_at: float = 0.0
    triggered_by: str = ""
    agent_id: str = ""
    sub_executions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status.value if isinstance(self.status, ExecutionStatus) else self.status,
            "current_step": self.current_step,
            "results": {k: v.to_dict() if isinstance(v, StepResult) else v for k, v in self.results.items()},
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "triggered_by": self.triggered_by,
            "agent_id": self.agent_id,
            "sub_executions": self.sub_executions,
        }

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowExecution:
        results = {}
        for k, v in d.get("results", {}).items():
            results[k] = StepResult.from_dict(v) if isinstance(v, dict) else v
        return cls(
            id=d["id"],
            workflow_id=d["workflow_id"],
            status=ExecutionStatus(d["status"]) if isinstance(d.get("status"), str) else ExecutionStatus.PENDING,
            current_step=d.get("current_step", ""),
            results=results,
            started_at=d.get("started_at", 0.0),
            ended_at=d.get("ended_at", 0.0),
            triggered_by=d.get("triggered_by", ""),
            agent_id=d.get("agent_id", ""),
            sub_executions=d.get("sub_executions", []),
        )
