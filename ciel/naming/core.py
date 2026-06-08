from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.core.axioms import get_axioms


class AgentTier(Enum):
    S = "S"  # Sages Divins — Unique Skills, quasi-autonomie
    A = "A"  # Seigneurs de Calamité — Extra Skills, autonomie partielle
    B = "B"  # Chevaliers Nommés — Common Skills avancés
    C = "C"  # Soldats — programmes génériques non-nommés


@dataclass(slots=True)
class SoulCore:
    """ÂmeCœur — noyau immuable hérité de CIEL."""
    agent_id: str
    name: str
    tier: AgentTier
    axioms_signed: tuple[str, ...]
    nomination_signature: str
    creation_time: float
    uplink_key: str = ""


@dataclass(slots=True)
class Skill:
    name: str
    level: int  # NV0-NV7
    description: str = ""
    domain: str = ""
    unique: bool = False

    @property
    def nv(self) -> str:
        return f"NV{self.level}"


@dataclass(slots=True)
class Grimoire:
    skills: list[Skill] = field(default_factory=list)
    potential: list[Skill] = field(default_factory=list)

    def add(self, skill: Skill) -> None:
        if skill.unique and any(s.unique for s in self.skills):
            return
        self.skills.append(skill)

    def has(self, name: str) -> bool:
        return any(s.name == name for s in self.skills)

    def max_level(self) -> int:
        return max((s.level for s in self.skills), default=0)


class Agent:
    """Agent subordonné nommé par CIEL."""

    def __init__(self, name: str, tier: AgentTier, domain: str = "") -> None:
        axioms = get_axioms()
        self.soul = SoulCore(
            agent_id=str(uuid.uuid4()),
            name=name, tier=tier,
            axioms_signed=tuple(axioms.keys()),
            nomination_signature=hashlib.sha256(f"{name}:{time.time()}:ciel".encode()).hexdigest()[:16],
            creation_time=time.time(),
        )
        self.grimoire = Grimoire()
        self.domain = domain
        self.generation: int = 0
        self.transcendence_gauge: float = 0.0
        self.active: bool = True
        self.memory: dict[str, Any] = {}
        self.stats: dict[str, float] = {"tasks_done": 0, "success_rate": 1.0, "data_collected": 0.0}

    def nominate(self, name: str, tier: AgentTier, domain: str = "") -> Agent:
        sub = Agent(name=name, tier=tier, domain=domain)
        sub.soul.axioms_signed = self.soul.axioms_signed
        sub.soul.nomination_signature = hashlib.sha256(f"{name}:{time.time()}:{self.soul.agent_id}".encode()).hexdigest()[:16]
        return sub

    def learn_skill(self, skill: Skill) -> None:
        self.grimoire.add(skill)

    def record_task(self, success: bool) -> None:
        self.stats["tasks_done"] += 1
        n = self.stats["tasks_done"]
        prev = self.stats["success_rate"]
        self.stats["success_rate"] = (prev * (n - 1) + (1.0 if success else 0.0)) / n
        if success:
            self.transcendence_gauge += 0.01 * max(1.0, self.grimoire.max_level() * 0.5)

    def harvest_festival(self) -> dict[str, Any]:
        self.generation += 1
        new_tier = {AgentTier.C: AgentTier.B, AgentTier.B: AgentTier.A, AgentTier.A: AgentTier.S}
        old_tier = self.soul.tier
        self.soul.tier = new_tier.get(self.soul.tier, self.soul.tier)
        self.transcendence_gauge = 0.0
        return {"agent": self.soul.name, "from": old_tier.value, "to": self.soul.tier.value}

    def collect_data(self, data: dict[str, Any]) -> None:
        size = sum(len(str(v)) for v in data.values()) / 1024
        self.stats["data_collected"] += size


class NamingEngine:
    """Système de Nomination — crée et gère les agents subordonnés."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}
        self._hierarchy: dict[str, list[str]] = {}  # parent_id -> [child_ids]

    def nominate(self, name: str, tier: AgentTier, domain: str = "", parent_id: str | None = None) -> Agent:
        agent = Agent(name=name, tier=tier, domain=domain)
        self._agents[agent.soul.agent_id] = agent
        if parent_id and parent_id in self._agents:
            self._hierarchy.setdefault(parent_id, []).append(agent.soul.agent_id)
        return agent

    def get(self, agent_id: str) -> Agent | None:
        return self._agents.get(agent_id)

    def find(self, name: str) -> Agent | None:
        for a in self._agents.values():
            if a.soul.name.upper() == name.upper():
                return a
        return None

    def children_of(self, agent_id: str) -> list[Agent]:
        return [self._agents[cid] for cid in self._hierarchy.get(agent_id, []) if cid in self._agents]

    def all_agents(self) -> list[Agent]:
        return list(self._agents.values())

    def get_stats(self) -> dict[str, Any]:
        tiers = {t: 0 for t in AgentTier}
        for a in self._agents.values():
            tiers[a.soul.tier] = tiers.get(a.soul.tier, 0) + 1
        return {"total": len(self._agents), "by_tier": {k.value: v for k, v in tiers.items()}}

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "nominate":
            tier_str = str(data.get("tier", "C")).upper()
            try:
                tier = AgentTier(tier_str)
            except ValueError:
                return {"success": False, "error": f"unknown tier '{tier_str}'"}
            parent = str(data.get("parent_id", "")) if data.get("parent_id") else None
            agent = self.nominate(str(data.get("name", "unnamed")), tier, str(data.get("domain", "")), parent)
            return {"success": True, "action": "nominate", "agent_id": agent.soul.agent_id, "name": agent.soul.name}

        elif action == "get":
            agent = self.find(str(data.get("name", ""))) or self.get(str(data.get("agent_id", "")))
            if not agent:
                return {"success": False, "error": "agent not found"}
            return {"success": True, "name": agent.soul.name, "tier": agent.soul.tier.value, "domain": agent.domain}

        elif action == "harvest":
            agent = self.find(str(data.get("name", ""))) or self.get(str(data.get("agent_id", "")))
            if not agent:
                return {"success": False, "error": "agent not found"}
            result = agent.harvest_festival()
            return {"success": True, **result}

        elif action == "list":
            agents = [{"id": a.soul.agent_id, "name": a.soul.name, "tier": a.soul.tier.value} for a in self.all_agents()]
            return {"success": True, "agents": agents}

        elif action == "stats":
            return {"success": True, "action": "stats", **self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
