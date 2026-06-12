"""
CIEL v∞.8 — CLONES ENGINE.
Système de clones Hydra — LegionEngine, SpiderWeb, essaim distribué.

Concept : CIEL peut créer des clones (instances légères) de
lui-même pour exécuter des tâches en parallèle. Chaque clone
est une copie indépendante avec un sous-ensemble de capacités.
Types : Worker (tâche unique), Scout (exploration), Phantom
(furtif), Aspect (spécialisé). Communication via essaim.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


class CloneType(Enum):
    WORKER = "worker"       # Tâche unique
    SCOUT = "scout"         # Exploration
    PHANTOM = "phantom"     # Furtif
    ASPECT = "aspect"       # Spécialisé


CLONE_PROFILES = {
    CloneType.WORKER: {"capabilities": ["tool_run", "compute"],
                       "ttl": 3600, "memory_mb": 128},
    CloneType.SCOUT: {"capabilities": ["web_search", "vision", "read"],
                      "ttl": 7200, "memory_mb": 64},
    CloneType.PHANTOM: {"capabilities": ["observe", "collect"],
                        "ttl": 1800, "memory_mb": 32},
    CloneType.ASPECT: {"capabilities": ["specialized"],
                       "ttl": 86400, "memory_mb": 256},
}


@dataclass(slots=True)
class Clone:
    id: str
    name: str
    clone_type: CloneType
    parent_id: str = ""
    status: str = "spawning"  # spawning | active | idle | terminated
    task: str = ""
    capabilities: list[str] = field(default_factory=list)
    ttl: int = 3600
    created_at: float = 0.0
    last_heartbeat: float = 0.0
    result: dict = field(default_factory=dict)

    def is_alive(self) -> bool:
        if self.status == "terminated":
            return False
        if self.ttl > 0 and time.time() - self.created_at > self.ttl:
            return False
        return True

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "type": self.clone_type.value,
                "status": self.status,
                "task": self.task[:40],
                "alive": self.is_alive(),
                "age_sec": round(time.time() - self.created_at, 1)}


@dataclass(slots=True)
class SpiderWeb:
    """Réseau de communication entre clones — toile d'araignée."""
    edges: dict[str, list[str]] = field(default_factory=dict)

    def connect(self, a_id: str, b_id: str):
        self.edges.setdefault(a_id, []).append(b_id)
        self.edges.setdefault(b_id, []).append(a_id)

    def broadcast(self, sender_id: str, message: dict) -> list[str]:
        recipients = self.edges.get(sender_id, [])
        return recipients


class ClonesEngine:
    """Moteur de clones — essaim distribué à la Hydra.

    Crée, gère, termine des clones. Maintient le SpiderWeb.
    Chaque clone peut être invoqué, monitoré, rappelé.
    """

    def __init__(self):
        self.clones: dict[str, Clone] = {}
        self.web = SpiderWeb()
        self.network = LeaderNetwork()
        self._next_id = 0

    def spawn(self, name: str, clone_type: str = "worker",
              task: str = "", parent_id: str = "ciel-master") -> Clone:
        ctype = next((ct for ct in CloneType if ct.value == clone_type),
                     CloneType.WORKER)
        profile = CLONE_PROFILES[ctype]
        clone = Clone(
            id=f"CLN-{uuid.uuid4().hex[:12]}",
            name=name, clone_type=ctype,
            parent_id=parent_id, task=task,
            capabilities=list(profile["capabilities"]),
            ttl=profile["ttl"],
            created_at=time.time(),
            last_heartbeat=time.time(),
            status="active",
        )
        self.clones[clone.id] = clone
        self.web.connect(parent_id, clone.id)
        self.network.emit("clone.spawned", {"name": name, "type": ctype.value})
        return clone

    def terminate(self, clone_id: str) -> bool:
        clone = self.clones.get(clone_id)
        if not clone:
            return False
        clone.status = "terminated"
        return True

    def heartbeat(self, clone_id: str) -> bool:
        clone = self.clones.get(clone_id)
        if not clone:
            return False
        clone.last_heartbeat = time.time()
        return True

    def assign_task(self, clone_id: str, task: str) -> bool:
        clone = self.clones.get(clone_id)
        if not clone:
            return False
        clone.task = task
        return True

    def list_alive(self) -> list[dict]:
        return [c.to_dict() for c in self.clones.values() if c.is_alive()]

    def broadcast(self, sender_id: str, message: dict) -> list[str]:
        return self.web.broadcast(sender_id, message)

    def recall_all(self):
        for c in self.clones.values():
            if c.is_alive():
                c.status = "terminated"

    def get_swarm_stats(self) -> dict:
        alive = [c for c in self.clones.values() if c.is_alive()]
        by_type = {}
        for c in alive:
            by_type[c.clone_type.value] = by_type.get(c.clone_type.value, 0) + 1
        return {
            "total": len(self.clones),
            "alive": len(alive),
            "by_type": by_type,
            "web_edges": sum(len(v) for v in self.web.edges.values()),
        }

    def get_stats(self) -> dict:
        return self.get_swarm_stats()

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "spawn":
            c = self.spawn(
                input_data.get("name", "clone"),
                input_data.get("type", "worker"),
                input_data.get("task", ""),
                input_data.get("parent_id", "ciel-master"),
            )
            return {"status": "ok", "clone": c.to_dict()}
        elif action == "terminate":
            ok = self.terminate(input_data.get("clone_id", ""))
            return {"status": "ok" if ok else "error"}
        elif action == "task":
            ok = self.assign_task(
                input_data.get("clone_id", ""),
                input_data.get("task", ""),
            )
            return {"status": "ok" if ok else "error"}
        elif action == "list":
            return {"status": "ok",
                    "clones": self.list_alive()}
        elif action == "broadcast":
            reached = self.broadcast(
                input_data.get("sender_id", ""),
                input_data.get("message", {}),
            )
            return {"status": "ok", "reached": len(reached)}
        elif action == "recall_all":
            self.recall_all()
            return {"status": "ok"}
        return {"status": "ok", "clones": len(self.clones)}
