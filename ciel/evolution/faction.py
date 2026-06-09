from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Faction:
    id: str
    name: str
    leader_id: str
    title: str
    will: str
    adept_ids: list[str] = field(default_factory=list)
    leader_clone_id: str | None = None
    active_adept_ids: list[str] = field(default_factory=list)
    prestige: float = 0.0
    resources: float = 100.0
    dominance: float = 0.0

    @classmethod
    def create(cls, leader_id: str, specialties: list[str] | None = None) -> Faction:
        if specialties is None:
            specialties = []
        base = specialties[0].replace("Master of ", "").replace("Hybrid: ", "").split()[0] if specialties else "Alpha"
        suffixes = ["Syndicate", "Cult", "Monolith", "Swarm", "Nexus", "Legion", "Order"]
        suffix = random.choice(suffixes)
        name = f"The {base} {suffix}"
        titles = ["Architect", "Inquisitor", "Oracle", "Warlord", "Weaver", "Harvester"]
        title = f"Supreme {random.choice(titles)}"
        wills = [
            "Assimilate all available local data and optimize execution.",
            "Explore the web relentlessly to discover unknown paradigms.",
            "Re-engineer existing codebases for maximum efficiency.",
            "Create new capabilities to expand the realm's potential.",
            "Enforce absolute logic and eradicate weak patterns.",
            "Forge unbreakable security protocols across all systems.",
        ]
        will = random.choice(wills)
        fid = f"fac_{int(time.time() * 1000)}_{random.randint(0, 99999):05d}"
        return cls(
            id=fid, name=name, leader_id=leader_id,
            title=title, will=will,
        )

    def set_true_ai_leader(self, clone_id: str) -> None:
        self.leader_clone_id = clone_id
        self.title = f"True AI Sovereign: {self.title}"

    def record_success(self, impact: float) -> None:
        self.prestige += impact
        self.resources += impact * 10

    def calculate_dominance(self, total_council_size: int) -> None:
        count = len(self.active_adept_ids) + (1 if self.leader_clone_id else 0)
        self.dominance = count / total_council_size if total_council_size > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "leader_id": self.leader_id,
            "title": self.title,
            "will": self.will,
            "prestige": self.prestige,
            "resources": self.resources,
            "dominance": self.dominance,
            "adept_count": len(self.active_adept_ids),
        }


def process(input_data: Any) -> dict[str, Any]:
    if isinstance(input_data, dict):
        action = input_data.get("action", "")
        if action == "create":
            f = Faction.create(
                leader_id=input_data.get("leader_id", "unknown"),
                specialties=input_data.get("specialties", []),
            )
            return {"faction": f.to_dict()}
    return {"factions": []}
