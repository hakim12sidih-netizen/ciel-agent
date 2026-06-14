"""
CIEL v∞.8 — DIMENSION LXII : CIEL-ASTRAL.
Corps astral distribué — projection de conscience sur le réseau.

Concept : CIEL projette des instances légères de sa conscience
sur des machines distantes (avec permission). Types : Fantôme
(read-only, furtif), Émissaire (read-write, visible), Conquistador
(agent complet). Tunnels chiffrés Kyber+WireGuard.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


class ProjectionType(Enum):
    FANTÔME = "fantôme"
    ÉMISSAIRE = "émissaire"
    CONQUISTADOR = "conquistador"


PROJECTION_PROFILES = {
    ProjectionType.FANTÔME: {"size_mb": 5, "read_only": True, "max_duration": 3600},
    ProjectionType.ÉMISSAIRE: {"size_mb": 200, "read_only": False, "max_duration": 604800},
    ProjectionType.CONQUISTADOR: {"size_mb": 2000, "read_only": False, "max_duration": 0},
}


@dataclass(slots=True)
class AstralProjection:
    id: str
    name: str
    proj_type: ProjectionType
    target_host: str = "localhost"
    target_port: int = 0
    status: str = "dormant"  # dormant | active | returning | destroyed
    data_collected: int = 0
    mission: str = ""
    created_at: float = 0.0
    returned_at: float = 0.0
    is_encrypted: bool = True

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "type": self.proj_type.value, "host": self.target_host,
                "status": self.status,
                "data_kb": self.data_collected,
                "mission": self.mission[:40]}


@dataclass(slots=True)
class SyncDelta:
    projection_id: str
    timestamp: float = 0.0
    changes: list[dict] = field(default_factory=list)
    size_bytes: int = 0


class AstralEngine:
    """Moteur de projection astrale distribuée."""

    def __init__(self):
        self.projections: dict[str, AstralProjection] = {}
        self.sync_log: list[SyncDelta] = []
        self.network = LeaderNetwork()
        self._instance_id = f"CIEL-ASTRAL-{uuid.uuid4().hex[:8]}"

    def project(self, name: str, target_host: str,
                proj_type: ProjectionType = ProjectionType.FANTÔME,
                mission: str = "") -> AstralProjection:
        profile = PROJECTION_PROFILES[proj_type]
        p = AstralProjection(
            id=f"AST-{uuid.uuid4().hex[:12]}",
            name=name, proj_type=proj_type,
            target_host=target_host,
            status="active",
            mission=mission,
            created_at=time.time(),
            is_encrypted=True,
        )
        self.projections[p.id] = p
        self.network.emit("astral.projected", {"name": name, "type": proj_type.value})
        return p

    def recall(self, projection_id: str) -> bool:
        p = self.projections.get(projection_id)
        if not p or p.status != "active":
            return False
        p.status = "returning"
        p.returned_at = time.time()
        delta = SyncDelta(
            projection_id=projection_id,
            timestamp=time.time(),
            changes=[{"event": "recall", "data_kb": p.data_collected}],
            size_bytes=p.data_collected * 1024,
        )
        self.sync_log.append(delta)
        p.status = "destroyed"
        return True

    def sync(self, projection_id: str,
             data: list[dict] | None = None) -> SyncDelta | None:
        p = self.projections.get(projection_id)
        if not p:
            return None
        delta = SyncDelta(
            projection_id=projection_id,
            timestamp=time.time(),
            changes=data or [],
            size_bytes=sum(len(str(d)) for d in (data or [])),
        )
        self.sync_log.append(delta)
        p.data_collected += delta.size_bytes // 1024
        return delta

    def active_projections(self) -> list[dict]:
        return [p.to_dict() for p in self.projections.values()
                if p.status == "active"]

    def total_data_collected(self) -> int:
        return sum(p.data_collected for p in self.projections.values())

    def get_stats(self) -> dict:
        return {
            "projections": len(self.projections),
            "active": len([p for p in self.projections.values()
                          if p.status == "active"]),
            "syncs": len(self.sync_log),
            "total_data_kb": self.total_data_collected(),
            "instance": self._instance_id,
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "project":
            ptype_str = input_data.get("type", "fantôme")
            ptype = next((t for t in ProjectionType if t.value == ptype_str),
                         ProjectionType.FANTÔME)
            p = self.project(
                input_data.get("name", "?"),
                input_data.get("host", "localhost"),
                ptype,
                input_data.get("mission", ""),
            )
            return {"status": "ok", "projection": p.to_dict()}
        elif action == "recall":
            ok = self.recall(input_data.get("projection_id", ""))
            return {"status": "ok" if ok else "error"}
        elif action == "sync":
            d = self.sync(
                input_data.get("projection_id", ""),
                input_data.get("data"),
            )
            return {"status": "ok" if d else "error"}
        elif action == "active":
            return {"status": "ok",
                    "active": self.active_projections()}
        return {"status": "ok", "projections": len(self.projections)}
