from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.sandbox import SandboxEngine, SandboxPolicy, detect_best_backend


@dataclass
class Workspace:
    id: str
    name: str
    sandbox_backend: str = ""
    policy: str = "default"
    agent_id: str = ""
    skills: list[str] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "sandbox_backend": self.sandbox_backend, "policy": self.policy,
            "agent_id": self.agent_id, "skills": self.skills,
            "state_keys": list(self.state.keys()),
            "created_at": self.created_at, "last_active_at": self.last_active_at,
            "active": self.active,
        }


POLICIES: dict[str, SandboxPolicy] = {
    "restricted": SandboxPolicy.restricted(),
    "default": SandboxPolicy.default(),
    "permissive": SandboxPolicy.permissive(),
}


class WorkspaceManager:
    def __init__(self, data_dir: str | Path | None = None):
        self._data_dir = Path(data_dir or Path.home() / ".ciel" / "workspaces")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._workspaces: dict[str, Workspace] = {}
        self._sandboxes: dict[str, SandboxEngine] = {}
        self._load()

    def _load(self) -> None:
        for f in self._data_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                ws = Workspace(**data)
                self._workspaces[ws.id] = ws
            except Exception:
                pass

    def _save(self, ws: Workspace) -> None:
        path = self._data_dir / f"{ws.id}.json"
        path.write_text(json.dumps(vars(ws), indent=2, default=str))

    def create(self, name: str, sandbox_backend: str = "",
               policy: str = "default", agent_id: str = "",
               skills: list[str] | None = None) -> Workspace:
        wid = f"ws-{uuid.uuid4().hex[:12]}"
        ws = Workspace(
            id=wid, name=name,
            sandbox_backend=sandbox_backend or detect_best_backend(),
            policy=policy, agent_id=agent_id,
            skills=skills or [],
        )
        self._workspaces[wid] = ws
        self._save(ws)
        return ws

    def get(self, workspace_id: str) -> Workspace | None:
        return self._workspaces.get(workspace_id)

    def list(self, active_only: bool = True) -> list[Workspace]:
        results = list(self._workspaces.values())
        if active_only:
            results = [w for w in results if w.active]
        return results

    def delete(self, workspace_id: str) -> bool:
        ws = self._workspaces.pop(workspace_id, None)
        if ws:
            path = self._data_dir / f"{workspace_id}.json"
            if path.exists():
                path.unlink()
            if workspace_id in self._sandboxes:
                del self._sandboxes[workspace_id]
            return True
        return False

    def get_sandbox(self, workspace_id: str) -> SandboxEngine | None:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return None
        if workspace_id not in self._sandboxes:
            policy = POLICIES.get(ws.policy, POLICIES["default"])
            self._sandboxes[workspace_id] = SandboxEngine(
                backend=ws.sandbox_backend, policy=policy,
            )
        return self._sandboxes[workspace_id]

    def execute(self, workspace_id: str, code: str,
                language: str = "python", timeout: int = 30) -> Any:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return {"error": f"Workspace {workspace_id} not found"}
        ws.last_active_at = time.time()
        sbx = self.get_sandbox(workspace_id)
        if not sbx:
            return {"error": "Failed to create sandbox"}
        result = sbx.execute(code, language, timeout)
        self._save(ws)
        return result.to_dict()

    def update_state(self, workspace_id: str, key: str, value: Any) -> bool:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return False
        ws.state[key] = value
        ws.last_active_at = time.time()
        self._save(ws)
        return True

    def get_state(self, workspace_id: str, key: str) -> Any:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return None
        return ws.state.get(key)

    def deactivate(self, workspace_id: str) -> bool:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return False
        ws.active = False
        self._save(ws)
        return True

    def stats(self) -> dict:
        total = len(self._workspaces)
        active = len([w for w in self._workspaces.values() if w.active])
        return {"total": total, "active": active}
