from __future__ import annotations

import math
import random
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SkillLevel(Enum):
    REFLEXE = 0
    REACTIF = 1
    ADAPTATIF = 2
    PREDICTIF = 3
    GENERATIF = 4
    META_META = 5
    SYMBIOTIQUE = 6
    TRANSCENDANT = 7

    @property
    def description(self) -> str:
        return _LEVEL_DESCRIPTIONS[self]

    @property
    def response_time_ms(self) -> float:
        return _LEVEL_RESPONSE_MS[self]


_LEVEL_DESCRIPTIONS: dict[SkillLevel, str] = {
    SkillLevel.REFLEXE: "précompilé, < 1ms",
    SkillLevel.REACTIF: "déclenché par pattern précis",
    SkillLevel.ADAPTATIF: "ajuste selon contexte + historique",
    SkillLevel.PREDICTIF: "anticipe avant demande",
    SkillLevel.GENERATIF: "crée d'autres skills (méta)",
    SkillLevel.META_META: "optimise création de N4",
    SkillLevel.SYMBIOTIQUE: "fusionné avec psycho utilisateur",
    SkillLevel.TRANSCENDANT: "capacité native du Noyau",
}

_LEVEL_RESPONSE_MS: dict[SkillLevel, float] = {
    SkillLevel.REFLEXE: 0.5,
    SkillLevel.REACTIF: 5.0,
    SkillLevel.ADAPTATIF: 20.0,
    SkillLevel.PREDICTIF: 50.0,
    SkillLevel.GENERATIF: 200.0,
    SkillLevel.META_META: 500.0,
    SkillLevel.SYMBIOTIQUE: 100.0,
    SkillLevel.TRANSCENDANT: 1.0,
}


class SkillPhase(Enum):
    GERMINATION = "germination"
    INCUBATION = "incubation"
    CONCEPTION = "conception"
    EMBRYON = "embryon"
    TEST_VIRTUEL = "test_virtuel"
    NAISSANCE = "naissance"
    ENFANCE = "enfance"
    MATURITE = "maturité"
    SPECIALISATION = "spécialisation"
    ENSEIGNEMENT = "enseignement"
    FUSION = "fusion"
    TRANSCENDANCE = "transcendance"

    @property
    def ordinal(self) -> int:
        return list(SkillPhase).index(self)


@dataclass(slots=True)
class Skill:
    id: str
    name: str
    level: SkillLevel
    phase: SkillPhase = SkillPhase.GERMINATION
    description: str = ""
    version: int = 1
    accuracy: float = 0.0
    latency_ms: float = 0.0
    usage_count: int = 0
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(name: str, level: SkillLevel, description: str = "") -> Skill:
        return Skill(
            id=str(uuid.uuid4()),
            name=name,
            level=level,
            phase=SkillPhase.GERMINATION,
            description=description or f"skill {name} N{level.value}",
            latency_ms=level.response_time_ms,
        )

    def advance_phase(self) -> SkillPhase | None:
        phases = list(SkillPhase)
        idx = phases.index(self.phase)
        if idx < len(phases) - 1:
            self.phase = phases[idx + 1]
            return self.phase
        return None

    def execute(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        self.usage_count += 1
        base_latency = self.latency_ms * random.uniform(0.8, 1.2)
        base_accuracy = min(1.0, self.accuracy + random.gauss(0, 0.05))
        return {
            "skill_id": self.id,
            "skill_name": self.name,
            "latency_ms": base_latency,
            "accuracy": max(0.0, base_accuracy),
            "level": self.level.value,
            "phase": self.phase.value,
            "usage_count": self.usage_count,
            "context_keys": list((context or {}).keys()),
        }

    def train(self, success: bool) -> None:
        delta = 0.05 if success else -0.02
        self.accuracy = min(1.0, max(0.0, self.accuracy + delta))
        if success and self.accuracy > 0.8 and self.phase != SkillPhase.TRANSCENDANCE:
            self.advance_phase()

    def similar_to(self, other: Skill) -> float:
        if self.level != other.level:
            return 0.0
        same_deps = len(set(self.dependencies) & set(other.dependencies))
        total_deps = len(set(self.dependencies) | set(other.dependencies)) or 1
        return same_deps / total_deps


class SkillRegistry:
    """Registre central de tous les skills."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, skill: Skill, category: str = "general") -> None:
        self._skills[skill.id] = skill
        self._categories.setdefault(category, []).append(skill.id)

    def get(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def get_by_name(self, name: str) -> Skill | None:
        for s in self._skills.values():
            if s.name == name:
                return s
        return None

    def unregister(self, skill_id: str) -> bool:
        skill = self._skills.pop(skill_id, None)
        if skill is not None:
            for cat in self._categories.values():
                if skill_id in cat:
                    cat.remove(skill_id)
            return True
        return False

    def list_by_level(self, level: SkillLevel) -> list[Skill]:
        return [s for s in self._skills.values() if s.level == level]

    def list_by_phase(self, phase: SkillPhase) -> list[Skill]:
        return [s for s in self._skills.values() if s.phase == phase]

    def list_by_category(self, category: str) -> list[Skill]:
        ids = self._categories.get(category, [])
        return [self._skills[sid] for sid in ids if sid in self._skills]

    def all(self) -> list[Skill]:
        return list(self._skills.values())

    def count(self) -> int:
        return len(self._skills)

    def categories(self) -> list[str]:
        return list(self._categories.keys())

    def clear(self) -> None:
        self._skills.clear()
        self._categories.clear()


class SkillExecutor:
    """Exécute un skill dans un contexte donné."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._history: list[dict[str, Any]] = []
        self._pre_hooks: list[Callable[[Skill, dict[str, Any]], dict[str, Any]]] = []
        self._post_hooks: list[Callable[[Skill, dict[str, Any]], None]] = []

    def add_pre_hook(self, hook: Callable[[Skill, dict[str, Any]], dict[str, Any]]) -> None:
        self._pre_hooks.append(hook)

    def add_post_hook(self, hook: Callable[[Skill, dict[str, Any]], None]) -> None:
        self._post_hooks.append(hook)

    def execute(self, skill_id: str, context: dict[str, Any] | None = None) -> dict[str, Any] | None:
        skill = self._registry.get(skill_id)
        if skill is None:
            return None

        ctx = context or {}
        for hook in self._pre_hooks:
            ctx = hook(skill, ctx)

        result = skill.execute(ctx)

        for hook in self._post_hooks:
            hook(skill, result)

        self._history.append({
            "skill_id": skill_id,
            "skill_name": skill.name,
            "level": skill.level.value,
            "result": result,
        })
        return result

    def execute_by_name(self, name: str, context: dict[str, Any] | None = None) -> dict[str, Any] | None:
        skill = self._registry.get_by_name(name)
        if skill is None:
            return None
        return self.execute(skill.id, context)

    def execute_all(self, level: SkillLevel | None = None, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        skills = self._registry.list_by_level(level) if level else self._registry.all()
        results = []
        for s in skills:
            r = self.execute(s.id, context)
            if r is not None:
                results.append(r)
        return results

    def history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()


class SkillGenerator:
    """Génère de nouveaux skills (niveau GENERATIF et au-dessus)."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._generation_count = 0

    def generate(self, name: str, description: str = "",
                 level: SkillLevel = SkillLevel.GENERATIF,
                 parent_ids: list[str] | None = None) -> Skill:
        skill = Skill.create(name=name, level=level, description=description)
        if parent_ids:
            for pid in parent_ids:
                parent = self._registry.get(pid)
                if parent is not None:
                    skill.dependencies.append(pid)

        if level == SkillLevel.META_META:
            parents = parent_ids or []
            for pid in parents:
                parent = self._registry.get(pid)
                if parent is not None and parent.level == SkillLevel.GENERATIF:
                    skill.accuracy = parent.accuracy * 0.9

        skill.accuracy = skill.level.value * 0.1 + random.uniform(0, 0.3)
        skill.latency_ms = skill.level.response_time_ms * random.uniform(0.8, 1.5)

        self._generation_count += 1
        return skill

    def generate_from_existing(self, template_id: str, new_name: str,
                                mutation: float = 0.1) -> Skill | None:
        template = self._registry.get(template_id)
        if template is None:
            return None
        child = Skill.create(name=new_name, level=template.level)
        child.accuracy = max(0.0, min(1.0, template.accuracy + random.gauss(0, mutation)))
        child.latency_ms = template.latency_ms * random.uniform(0.9, 1.1)
        child.dependencies = list(template.dependencies) + [template_id]
        child.description = f"muté de {template.name}"
        self._generation_count += 1
        return child

    def mutate_batch(self, template_id: str, n: int = 3, mutation: float = 0.2) -> list[Skill]:
        return [self.generate_from_existing(template_id, f"{template_id}_mutant_{i}", mutation)
                for i in range(n) if self.generate_from_existing(template_id, f"{template_id}_mutant_{i}", mutation)
                is not None]

    def total_generated(self) -> int:
        return self._generation_count


class SkillOptimizer:
    """Optimise les skills existants."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def optimize(self, skill_id: str) -> bool:
        skill = self._registry.get(skill_id)
        if skill is None:
            return False
        if skill.level.value < SkillLevel.META_META.value:
            return False
        skill.latency_ms *= 0.9
        skill.accuracy = min(1.0, skill.accuracy + 0.05)
        skill.metadata["optimized"] = True
        return True

    def prune(self, threshold_usage: int = 5) -> int:
        removed = 0
        for skill in self._registry.all():
            if skill.usage_count < threshold_usage and skill.phase == SkillPhase.GERMINATION:
                if self._registry.unregister(skill.id):
                    removed += 1
        return removed

    def rebalance(self) -> dict[str, float]:
        stats: dict[str, float] = {}
        for skill in self._registry.all():
            stats[skill.id] = skill.accuracy
        mean_acc = sum(stats.values()) / len(stats) if stats else 0.0
        return {"mean_accuracy": mean_acc, "n_skills": float(len(stats))}


class ForgeronEngine:
    """Point d'entrée principal de la Strate 7 — FORGERON.

    Gère le cycle de vie complet des skills :
    - 8 niveaux (Réflexe → Transcendant)
    - 12 phases (Germination → Transcendance)
    - Génération, exécution, optimisation
    """

    def __init__(self) -> None:
        self.registry = SkillRegistry()
        self.executor = SkillExecutor(self.registry)
        self.generator = SkillGenerator(self.registry)
        self.optimizer = SkillOptimizer(self.registry)
        self._build_innate()

    def _build_innate(self) -> None:
        reflexes = [
            ("respawn", SkillLevel.REFLEXE, "redémarrage immédiat après crash"),
            ("signal_detection", SkillLevel.REFLEXE, "détection de signal entrant"),
            ("memory_access", SkillLevel.REFLEXE, "accès mémoire basique"),
        ]
        for name, level, desc in reflexes:
            skill = Skill.create(name=name, level=level, description=desc)
            skill.phase = SkillPhase.TRANSCENDANCE
            skill.accuracy = 1.0
            self.registry.register(skill, category="innate")

    def create_skill(self, name: str, level: SkillLevel, description: str = "",
                     category: str = "general") -> Skill:
        skill = Skill.create(name=name, level=level, description=description)
        self.registry.register(skill, category=category)
        return skill

    def generate_skill(self, name: str, description: str = "",
                       level: SkillLevel = SkillLevel.GENERATIF,
                       parent_ids: list[str] | None = None) -> Skill:
        skill = self.generator.generate(name, description, level, parent_ids)
        self.registry.register(skill, category="generated")
        return skill

    def train_skill(self, skill_id: str, success: bool) -> bool:
        skill = self.registry.get(skill_id)
        if skill is None:
            return False
        skill.train(success)
        return True

    def execute_skill(self, skill_id: str, context: dict[str, Any] | None = None) -> dict[str, Any] | None:
        return self.executor.execute(skill_id, context)

    def get_stats(self) -> dict[str, Any]:
        all_skills = self.registry.all()
        level_counts: dict[str, int] = {}
        phase_counts: dict[str, int] = {}
        for s in all_skills:
            level_counts[s.level.name] = level_counts.get(s.level.name, 0) + 1
            phase_counts[s.phase.name] = phase_counts.get(s.phase.name, 0) + 1
        return {
            "total_skills": len(all_skills),
            "categories": self.registry.categories(),
            "by_level": level_counts,
            "by_phase": phase_counts,
            "total_generated": self.generator.total_generated(),
            "execution_count": len(self.executor.history()),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict):
            skill_name = input_data.get("skill", "")
            context = {k: v for k, v in input_data.items() if k != "skill"}
            if skill_name:
                result = self.executor.execute_by_name(skill_name, context)
                return {"success": result is not None, "result": result}
            return {"success": False, "error": "no skill specified"}
        return {"success": False, "error": "input must be dict"}
