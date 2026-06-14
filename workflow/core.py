from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from ciel.workflow.builder import BUILTIN_WORKFLOWS
from ciel.workflow.models import (
    ExecutionStatus,
    Situation,
    Step,
    StepResult,
    StepStatus,
    StepType,
    Workflow,
    WorkflowExecution,
)

log = logging.getLogger("ciel.workflow")


class WorkflowEngine:
    """Moteur de workflows : DAG de steps, agents/sub-agents, situations.

    Chaque workflow est un graphe orienté de steps. L'exécution traverse
    le graphe séquentiellement ou en parallèle, peut spawn des agents
    et sub-agents pour décomposer les tâches complexes.
    """

    def __init__(self, brain=None):
        self._brain = brain
        self._workflows: dict[str, Workflow] = {}
        self._executions: dict[str, WorkflowExecution] = {}
        self._running = False
        self._event_loop: asyncio.AbstractEventLoop | None = None
        self._tick_task: asyncio.Task | None = None
        self._client: httpx.AsyncClient | None = None
        self._client_lock = asyncio.Lock()
        self._cfg_path = Path.home() / ".ciel" / "workflows.json"
        self._last_fire: dict[str, float] = {}
        self._exec_sem = asyncio.Semaphore(2)

    # ── Gestion des workflows ──────────────────────────────────

    def register(self, wf: Workflow) -> None:
        self._workflows[wf.id] = wf

    def get(self, wf_id: str) -> Workflow | None:
        return self._workflows.get(wf_id)

    def list(self, group: str | None = None) -> list[Workflow]:
        wfs = list(self._workflows.values())
        if group:
            wfs = [w for w in wfs if w.group == group]
        return sorted(wfs, key=lambda w: w.id)

    def delete(self, wf_id: str) -> bool:
        return self._workflows.pop(wf_id, None) is not None

    def get_stats(self) -> dict:
        total = len(self._workflows)
        enabled = sum(1 for w in self._workflows.values() if w.enabled)
        running_execs = sum(
            1 for e in self._executions.values() if e.status == ExecutionStatus.RUNNING
        )
        return {
            "workflows": total,
            "enabled": enabled,
            "running_executions": running_execs,
            "total_executions": len(self._executions),
            "is_running": self._running,
        }

    def load_defaults(self) -> None:
        for wf in BUILTIN_WORKFLOWS:
            if wf.id not in self._workflows:
                self.register(wf)
        log.info("Loaded %d built-in workflows", len(BUILTIN_WORKFLOWS))

    def load_from_file(self) -> None:
        if self._cfg_path.exists():
            try:
                data = json.loads(self._cfg_path.read_text())
                for item in data.get("workflows", []):
                    wf = Workflow.from_dict(item)
                    self.register(wf)
                for item in data.get("executions", []):
                    ex = WorkflowExecution.from_dict(item)
                    self._executions[ex.id] = ex
            except Exception as e:
                log.warning("Failed to load workflows: %s", e)

    def save(self) -> None:
        try:
            self._cfg_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "workflows": [w.to_dict() for w in self._workflows.values()],
                "executions": [e.to_dict() for e in self._executions.values()],
            }
            self._cfg_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.warning("Failed to save workflows: %s", e)

    # ── Moteur d'exécution ─────────────────────────────────────

    async def execute(
        self,
        wf_id: str,
        triggered_by: str = "manual",
        initial_data: dict | None = None,
    ) -> WorkflowExecution:
        wf = self._workflows.get(wf_id)
        if not wf:
            raise ValueError(f"workflow '{wf_id}' not found")

        exec_id = f"exec-{uuid.uuid4().hex[:12]}"
        ex = WorkflowExecution(
            id=exec_id,
            workflow_id=wf_id,
            status=ExecutionStatus.RUNNING,
            started_at=time.time(),
            triggered_by=triggered_by,
        )
        self._executions[exec_id] = ex
        log.info("Executing workflow %s%s", wf_id, f" ({triggered_by})" if triggered_by else "")

        async with self._exec_sem:
            try:
                entry = wf.get_entry_step()
                if entry:
                    await self._run_step(wf, ex, entry, initial_data or {})
                    all_done = all(
                        r.status in (StepStatus.SUCCESS, StepStatus.FAILED, StepStatus.SKIPPED)
                        for r in ex.results.values()
                    )
                    ex.status = ExecutionStatus.SUCCESS if all_done else ExecutionStatus.FAILED
                else:
                    ex.status = ExecutionStatus.SUCCESS
            except asyncio.CancelledError:
                ex.status = ExecutionStatus.CANCELLED
            except Exception as e:
                ex.status = ExecutionStatus.FAILED
                log.error("Workflow %s failed: %s", wf_id, e)
            finally:
                ex.ended_at = time.time()
                self.save()

        return ex

    async def _run_step(
        self,
        wf: Workflow,
        ex: WorkflowExecution,
        step: Step,
        data: dict,
    ) -> None:
        if step.id in ex.results and ex.results[step.id].status in (
            StepStatus.SUCCESS, StepStatus.FAILED
        ):
            return  # déjà exécuté

        log.info("  Step %s [%s]: %s", step.id, step.type.value, step.description or "")
        sr = StepResult(step_id=step.id, started_at=time.time(), status=StepStatus.RUNNING)
        ex.results[step.id] = sr
        ex.current_step = step.id

        try:
            if step.type == StepType.API_CALL:
                output = await self._exec_api_call(step, data)
                sr.status = StepStatus.SUCCESS
                sr.output = output

            elif step.type == StepType.AGENT:
                output = await self._exec_agent_step(wf, ex, step, data)
                sr.status = StepStatus.SUCCESS
                sr.output = output

            elif step.type == StepType.PARALLEL:
                output = await self._exec_parallel(wf, ex, step, data)
                sr.status = StepStatus.SUCCESS
                sr.output = output

            elif step.type == StepType.CONDITION:
                output = await self._exec_condition(wf, ex, step, data)
                sr.status = StepStatus.SUCCESS
                sr.output = output

            elif step.type == StepType.TRANSFORM:
                output = self._exec_transform(step, data)
                sr.status = StepStatus.SUCCESS
                sr.output = output

            else:
                sr.status = StepStatus.FAILED
                sr.error = f"Unknown step type: {step.type}"

        except Exception as e:
            sr.status = StepStatus.FAILED
            sr.error = str(e)
            log.warning("  Step %s failed: %s", step.id, e)

            if step.max_retries > 0 and step.retry_delay > 0:
                for attempt in range(step.max_retries):
                    log.info("  Retry %d/%d for step %s", attempt + 1, step.max_retries, step.id)
                    await asyncio.sleep(step.retry_delay)
                    try:
                        sr.status = StepStatus.RUNNING
                        sr.error = ""
                        if step.type == StepType.API_CALL:
                            sr.output = await self._exec_api_call(step, data)
                        elif step.type == StepType.AGENT:
                            sr.output = await self._exec_agent_step(wf, ex, step, data)
                        sr.status = StepStatus.SUCCESS
                        break
                    except Exception as e2:
                        sr.error = str(e2)
                        sr.status = StepStatus.FAILED

        finally:
            sr.ended_at = time.time()

        # Rendre le résultat disponible par l'ID du step
        data[step.id] = sr.output

        # Propager aux steps suivants
        if sr.status == StepStatus.SUCCESS:
            next_steps = wf.get_next_steps(step.id, "success")
        else:
            next_steps = wf.get_next_steps(step.id, "failed")

        for ns in next_steps:
            await self._run_step(wf, ex, ns, data)

    async def _exec_api_call(self, step: Step, data: dict) -> Any:
        client = await self._ensure_client()
        kwargs: dict[str, Any] = {}
        if step.method in ("POST", "PUT", "PATCH"):
            body = dict(step.body or {})
            kwargs["json"] = body
        if step.params:
            kwargs["params"] = step.params
        resp = await client.request(step.method, step.endpoint, **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            return resp.json()
        except Exception:
            return resp.text

    async def _exec_agent_step(
        self, wf: Workflow, ex: WorkflowExecution, step: Step, data: dict
    ) -> Any:
        """Spawn un agent CIEL. Si la tâche est complexe, l'agent spawn
        des sub-agents en parallèle, chacun recevant une sous-tâche."""
        if self._brain is None:
            return {"success": False, "error": "brain not available"}

        agent_mod = self._brain.get_module("clones")
        if not agent_mod:
            return {"success": False, "error": "clones module not available"}

        task = step.agent_task
        task_config = step.agent_config or {}

        is_complex = task_config.get("complex", False)
        parallel_count = task_config.get("parallel", 1)

        if is_complex and parallel_count > 1:
            # Tâche complexe → décomposition en sub-agents parallèles
            sub_tasks = self._decompose_task(task, parallel_count)
            sub_results = await asyncio.gather(*[
                self._spawn_agent(agent_mod, sub_task, ex.id)
                for sub_task in sub_tasks
            ], return_exceptions=True)
            return {
                "success": True,
                "agent": task,
                "sub_agents": parallel_count,
                "sub_results": [
                    r if not isinstance(r, Exception) else {"error": str(r)}
                    for r in sub_results
                ],
            }
        else:
            # Tâche simple → un seul agent
            result = await self._spawn_agent(agent_mod, task, ex.id)
            return result

    def _decompose_task(self, task: str, n: int) -> list[str]:
        """Décompose une tâche complexe en n sous-tâches."""
        lines = task.strip().split("\n")
        if len(lines) >= n:
            chunk_size = max(1, len(lines) // n)
            return ["\n".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]
        return [task] * n

    async def _spawn_agent(self, agent_mod, task: str, parent_exec_id: str) -> dict:
        """Spawn un agent et attend son résultat."""
        name = f"wf-agent-{uuid.uuid4().hex[:8]}"
        try:
            result = agent_mod.process({
                "action": "spawn",
                "name": name,
                "role": "worker",
                "task": task,
            })
            return {"agent": name, "result": result}
        except Exception as e:
            return {"agent": name, "error": str(e)}

    async def _exec_parallel(
        self, wf: Workflow, ex: WorkflowExecution, step: Step, data: dict
    ) -> list:
        """Exécute des sous-steps en parallèle."""
        if not step.parallel_steps:
            return []
        tasks = []
        for ps_id in step.parallel_steps:
            ps = wf.steps.get(ps_id)
            if ps:
                tasks.append(self._run_step(wf, ex, ps, data))
        await asyncio.gather(*tasks, return_exceptions=True)
        return [ex.results.get(ps_id).to_dict() if ex.results.get(ps_id) else {} for ps_id in (step.parallel_steps or [])]

    async def _exec_condition(
        self, wf: Workflow, ex: WorkflowExecution, step: Step, data: dict
    ) -> dict:
        """Évalue une condition et oriente le flux."""
        try:
            result = eval(step.condition_expr, {"__builtins__": {}}, data)
            return {"condition": step.condition_expr, "result": bool(result)}
        except Exception as e:
            raise RuntimeError(f"Condition eval error: {e}")

    def _exec_transform(self, step: Step, data: dict) -> Any:
        """Transform step — pour l'instant, merge simple."""
        if step.body:
            return {**data, **step.body}
        return data

    # ── Client HTTP interne ────────────────────────────────────

    async def _ensure_client(self) -> httpx.AsyncClient:
        async with self._client_lock:
            if self._client is not None:
                return self._client
            self._client = httpx.AsyncClient(
                base_url="http://127.0.0.1:8765", timeout=30,
                limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
            )
            self._client.headers["X-CIEL-Internal"] = "workflow-engine"
        return self._client

    # ── Cycle de vie ───────────────────────────────────────────

    async def _situation_check(self) -> None:
        """Vérifie les situations et déclenche les workflows."""
        now = time.time()
        client = await self._ensure_client()
        triggered = 0
        for wf in self._workflows.values():
            if not wf.enabled:
                continue
            for sit in wf.situations:
                if sit.type == "time" and sit.interval_seconds > 0:
                    last = self._last_fire.get(wf.id, 0.0)
                    if now - last >= sit.interval_seconds:
                        self._last_fire[wf.id] = now
                        log.info("Time-trigger: workflow %s (every %.0fs)", wf.id, sit.interval_seconds)
                        asyncio.create_task(self.execute(wf.id, triggered_by=f"time:{sit.interval_seconds}s"))
                        triggered += 1
                        if triggered >= 10:
                            await asyncio.sleep(0.2)
                            triggered = 0
                    break
                elif sit.type == "state" and sit.state_module:
                    if await self._eval_state_situation(sit, client):
                        log.info("State-trigger: workflow %s", wf.id)
                        asyncio.create_task(self.execute(wf.id, triggered_by=f"state:{sit.state_module}"))
                        break
                elif sit.type == "event":
                    pass  # géré par les hooks du brain

    async def _eval_state_situation(self, sit: Situation, client: httpx.AsyncClient) -> bool:
        try:
            resp = await client.get(f"/v1/{sit.state_module}/status")
            if resp.status_code == 200:
                state = resp.json()
                return bool(eval(sit.state_condition, {"__builtins__": {}}, state))
        except Exception as e:
            log.debug("State situation eval error: %s", e)
        return False

    async def _tick_loop(self) -> None:
        log.info("Workflow engine loop started")
        await asyncio.sleep(3.0)  # laisser le serveur démarrer
        while self._running:
            try:
                await self._situation_check()
            except Exception as e:
                log.error("Situation check error: %s", e)
            await asyncio.sleep(5.0)

    def start(self) -> None:
        if self._running:
            return
        self._event_loop = asyncio.get_event_loop()
        self.load_defaults()
        self.load_from_file()
        self._running = True
        self._tick_task = self._event_loop.create_task(self._tick_loop())
        log.info("Workflow engine started with %d workflows", len(self._workflows))

    async def stop(self) -> None:
        self._running = False
        if self._tick_task:
            self._tick_task.cancel()
            try:
                await self._tick_task
            except asyncio.CancelledError:
                pass
            self._tick_task = None
        if self._client:
            await self._client.aclose()
            self._client = None
        self.save()
        log.info("Workflow engine stopped")

    # ── Interface brain module ──────────────────────────────────

    def process(self, input_data: Any) -> dict[str, Any]:
        action = input_data.get("action", "stats") if isinstance(input_data, dict) else "stats"

        if action == "stats":
            return {"success": True, **self.get_stats()}

        if action == "list":
            group = input_data.get("group")
            return {"success": True, "workflows": [w.to_dict() for w in self.list(group)]}

        if action == "get":
            wf = self.get(input_data.get("id", ""))
            if not wf:
                return {"success": False, "error": "not found"}
            return {"success": True, "workflow": wf.to_dict()}

        if action == "register":
            wf = Workflow.from_dict(input_data.get("workflow", {}))
            self.register(wf)
            self.save()
            return {"success": True, "workflow": wf.to_dict()}

        if action == "delete":
            ok = self.delete(input_data.get("id", ""))
            if ok:
                self.save()
            return {"success": ok}

        if action == "execute":
            wf_id = input_data.get("id", "")
            data = input_data.get("data", {})
            try:
                ex = asyncio.run_coroutine_threadsafe(
                    self.execute(wf_id, triggered_by="api", initial_data=data),
                    self._event_loop,
                ).result(timeout=30)
                return {"success": True, "execution": ex.to_dict()}
            except Exception as e:
                return {"success": False, "error": str(e)}

        if action == "executions":
            return {
                "success": True,
                "executions": [e.to_dict() for e in self._executions.values()],
            }

        return {"success": False, "error": f"unknown action '{action}'"}
