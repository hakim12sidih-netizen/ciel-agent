from __future__ import annotations

import random
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SkillLevel(Enum):
    NV0 = 0
    NV1 = 1
    NV2 = 2
    NV3 = 3
    NV4 = 4
    NV5 = 5
    NV6 = 6
    NV7 = 7


SKILL_NAMES = [
    "Analyse Absolue", "Synthèse Divine", "Prédiction Oraculaire",
    "Ombre Silencieuse", "Cent Regards", "Commandement de Feu",
    "Stratégie Adaptative", "Dévouement Total", "Lecture des Émotions",
    "Purification", "Régénération", "Diagnostic Divin",
    "Grand Forgeron", "Clonage Évolutif", "Persuasion Absolue",
]


@dataclass(slots=True)
class SkillBlueprint:
    name: str
    domain: str
    target_level: SkillLevel
    description: str = ""
    requirements: list[str] = field(default_factory=list)
    verified: bool = False


@dataclass(slots=True)
class ForgedSkill:
    skill_id: str
    name: str
    level: SkillLevel
    domain: str
    created_at: float
    code_hash: str = ""
    test_count: int = 0
    passed: bool = False


class ForgeEngine:
    """Forge des Skills — pipeline NV0→NV7 pour agents."""

    def __init__(self) -> None:
        self._blueprints: list[SkillBlueprint] = []
        self._forged: dict[str, ForgedSkill] = {}
        self._forge_log: list[dict[str, Any]] = []

    def analyze_need(self, agent_name: str, performance: dict[str, float]) -> SkillBlueprint:
        gaps = [k for k, v in performance.items() if v < 0.5]
        domain = gaps[0] if gaps else "general"
        target = SkillLevel.NV0 if len(gaps) > 3 else SkillLevel.NV2
        bp = SkillBlueprint(
            name=f"{agent_name}_{domain}_skill",
            domain=domain, target_level=target,
            description=f"Skill adaptatif pour {agent_name} sur {domain}",
        )
        self._blueprints.append(bp)
        return bp

    def specify(self, blueprint: SkillBlueprint) -> SkillBlueprint:
        blueprint.requirements = ["axiom_alpha", "axiom_gamma", f"domain_{blueprint.domain}"]
        return blueprint

    def generate(self, blueprint: SkillBlueprint) -> ForgedSkill:
        skill_id = str(uuid.uuid4())
        level = blueprint.target_level
        if level.value >= 6:  # NV6-NV7 : co-évolution
            level = SkillLevel(random.randint(3, 5))
        forged = ForgedSkill(
            skill_id=skill_id,
            name=blueprint.name,
            level=level,
            domain=blueprint.domain,
            created_at=time.time(),
            test_count=random.randint(50, 200),
            passed=True,
        )
        self._forged[skill_id] = forged
        self._forge_log.append({"action": "generate", "skill": blueprint.name, "level": level.value})
        return forged

    def validate(self, skill: ForgedSkill) -> bool:
        if skill.level.value >= 6:
            skill.passed = random.random() > 0.3
        else:
            skill.passed = random.random() > 0.1
        return skill.passed

    def deploy(self, skill: ForgedSkill, agent_id: str) -> dict[str, Any]:
        return {
            "skill_id": skill.skill_id,
            "name": skill.name,
            "level": skill.level.value,
            "agent_id": agent_id,
            "deployed_at": time.time(),
            "canary": skill.level.value < 4,
        }

    def get_stats(self) -> dict[str, Any]:
        by_level: dict[int, int] = {}
        for s in self._forged.values():
            by_level[s.level.value] = by_level.get(s.level.value, 0) + 1
        return {
            "total_forged": len(self._forged),
            "blueprints_pending": len(self._blueprints),
            "by_level": by_level,
            "avg_tests": sum(s.test_count for s in self._forged.values()) / max(len(self._forged), 1),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "forge":
            bp = SkillBlueprint(
                name=str(data.get("name", "unnamed")),
                domain=str(data.get("domain", "general")),
                target_level=SkillLevel(int(data.get("level", 0))),
            )
            self.specify(bp)
            skill = self.generate(bp)
            valid = self.validate(skill)
            return {"success": True, "skill_id": skill.skill_id, "name": skill.name, "level": skill.level.value, "valid": valid}

        elif action == "analyze":
            perf = {k: float(v) for k, v in data.items() if k != "agent"}
            bp = self.analyze_need(str(data.get("agent", "unknown")), perf)
            return {"success": True, "blueprint": bp.name, "target_level": bp.target_level.value, "domain": bp.domain}

        elif action == "stats":
            return {"success": True, "action": "stats", **self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
