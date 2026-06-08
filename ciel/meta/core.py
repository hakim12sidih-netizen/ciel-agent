from __future__ import annotations

import hashlib
import inspect
import math
import random
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── Self-Reflection ─────────────────────────────────────────────────────────

class MetricDimension(Enum):
    PERFORMANCE = "performance"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    ROBUSTNESS = "robustness"
    ADAPTABILITY = "adaptability"
    COHERENCE = "coherence"
    NOVELTY = "novelty"
    SAFETY = "safety"
    TRANSPARENCY = "transparency"
    EVOLUTION = "evolution"


METRIC_DESCRIPTIONS: dict[MetricDimension, str] = {
    MetricDimension.PERFORMANCE: "vitesse et debit de traitement",
    MetricDimension.QUALITY: "precision et qualite des resultats",
    MetricDimension.EFFICIENCY: "ratio ressources/resultats",
    MetricDimension.ROBUSTNESS: "resistance aux erreurs et pannes",
    MetricDimension.ADAPTABILITY: "capacite a s adapter a des contextes nouveaux",
    MetricDimension.COHERENCE: "consistance interne des decisions",
    MetricDimension.NOVELTY: "taux de creation de nouvelles solutions",
    MetricDimension.SAFETY: "respect des axiomes et garde-fous",
    MetricDimension.TRANSPARENCY: "traçabilite et explicabilite",
    MetricDimension.EVOLUTION: "taux d amelioration dans le temps",
}


@dataclass(slots=True)
class MetricSnapshot:
    dimension: MetricDimension
    value: float
    weight: float = 1.0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def weighted_value(self) -> float:
        return self.value * self.weight


@dataclass(slots=True)
class ReflectionReport:
    id: str
    metrics: dict[MetricDimension, float]
    overall_score: float
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class SelfReflection:
    """Auto-évaluation sur les 10 dimensions métriques."""

    def __init__(self) -> None:
        self._history: list[MetricSnapshot] = []
        self._reports: list[ReflectionReport] = []

    def record(self, dimension: MetricDimension, value: float,
               weight: float = 1.0, metadata: dict[str, Any] | None = None) -> MetricSnapshot:
        snapshot = MetricSnapshot(
            dimension=dimension, value=max(0.0, min(1.0, value)),
            weight=weight, metadata=metadata or {},
        )
        self._history.append(snapshot)
        return snapshot

    def evaluate(self) -> ReflectionReport:
        dims = list(MetricDimension)
        scores: dict[MetricDimension, float] = {}
        for d in dims:
            snapshots = [s for s in self._history if s.dimension == d]
            if snapshots:
                recent = snapshots[-10:]
                scores[d] = sum(s.weighted_value() for s in recent) / len(recent)
            else:
                scores[d] = 0.5

        overall = sum(scores.values()) / len(scores)
        strengths = [d.value for d, v in scores.items() if v >= 0.7]
        weaknesses = [d.value for d, v in scores.items() if v < 0.4]
        recommendations = self._generate_recommendations(scores)

        report = ReflectionReport(
            id=str(uuid.uuid4()),
            metrics=scores,
            overall_score=overall,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )
        self._reports.append(report)
        return report

    def _generate_recommendations(self, scores: dict[MetricDimension, float]) -> list[str]:
        recs: list[str] = []
        for dim, score in sorted(scores.items(), key=lambda x: x[1]):
            if score < 0.4:
                recs.append(f"ameliorer {dim.value}: {METRIC_DESCRIPTIONS[dim]} (score={score:.2f})")
        for dim, score in sorted(scores.items(), key=lambda x: -x[1])[:2]:
            if score >= 0.8:
                recs.append(f"maintenir {dim.value}: point fort (score={score:.2f})")
        if not recs:
            recs.append("toutes les dimensions sont dans la norme")
        return recs

    def trend(self, dimension: MetricDimension, window: int = 10) -> float:
        snapshots = [s for s in self._history if s.dimension == dimension][-window:]
        if len(snapshots) < 2:
            return 0.0
        values = [s.value for s in snapshots]
        return (values[-1] - values[0]) / len(values)

    def history(self) -> list[MetricSnapshot]:
        return list(self._history)

    def reports(self) -> list[ReflectionReport]:
        return list(self._reports)


# ── Quine — Auto-Reproduction ──────────────────────────────────────────────

@dataclass(slots=True)
class QuineManifest:
    id: str
    version: str
    modules: list[dict[str, Any]]
    checksum: str
    dependencies: dict[str, str]
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class Quine:
    """Auto-reproduction — serialisation, verification, recompilation."""

    def __init__(self) -> None:
        self._manifests: list[QuineManifest] = []
        self._reproduction_count = 0

    def snapshot(self, modules: list[dict[str, Any]],
                 dependencies: dict[str, str] | None = None,
                 version: str = "1.0") -> QuineManifest:
        manifest_data = str(modules) + str(dependencies or {}) + version
        checksum = hashlib.sha256(manifest_data.encode()).hexdigest()
        manifest = QuineManifest(
            id=str(uuid.uuid4()),
            version=version,
            modules=modules,
            checksum=checksum,
            dependencies=dependencies or {},
        )
        self._manifests.append(manifest)
        self._reproduction_count += 1
        return manifest

    def verify(self, manifest: QuineManifest) -> bool:
        data = str(manifest.modules) + str(manifest.dependencies) + manifest.version
        expected = hashlib.sha256(data.encode()).hexdigest()
        return manifest.checksum == expected

    def compare(self, a: QuineManifest, b: QuineManifest) -> dict[str, Any]:
        a_modules = {m.get("name", ""): m for m in a.modules if "name" in m}
        b_modules = {m.get("name", ""): m for m in b.modules if "name" in m}
        a_names = set(a_modules)
        b_names = set(b_modules)
        return {
            "added": list(b_names - a_names),
            "removed": list(a_names - b_names),
            "common": list(a_names & b_names),
            "version_change": f"{a.version} -> {b.version}",
        }

    def latest(self) -> QuineManifest | None:
        return self._manifests[-1] if self._manifests else None

    def count(self) -> int:
        return self._reproduction_count

    def history(self) -> list[QuineManifest]:
        return list(self._manifests)


# ── Evolution Planner ──────────────────────────────────────────────────────

class EvolutionStrategy(Enum):
    LAMARCK = "lamarck"
    DARWIN = "darwin"
    BALDWIN = "baldwin"
    HYBRID = "hybrid"


@dataclass(slots=True)
class EvolutionPlan:
    id: str
    strategy: EvolutionStrategy
    target: str
    changes: list[dict[str, Any]]
    expected_impact: float
    risk_score: float
    status: str = "draft"
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class EvolutionPlanner:
    """Planification évolutionnaire — Lamarck + Darwin + Baldwin."""

    def __init__(self) -> None:
        self._plans: list[EvolutionPlan] = []
        self._adaptations: list[dict[str, Any]] = []

    def plan(self, target: str, strategy: EvolutionStrategy = EvolutionStrategy.HYBRID,
             changes: list[dict[str, Any]] | None = None,
             expected_impact: float = 0.5) -> EvolutionPlan:
        risk = self._assess_risk(strategy, changes or [])
        plan = EvolutionPlan(
            id=str(uuid.uuid4()),
            strategy=strategy,
            target=target,
            changes=changes or [],
            expected_impact=max(0.0, min(1.0, expected_impact)),
            risk_score=risk,
        )
        self._plans.append(plan)
        return plan

    def _assess_risk(self, strategy: EvolutionStrategy, changes: list[dict[str, Any]]) -> float:
        base_risk = {
            EvolutionStrategy.LAMARCK: 0.6,
            EvolutionStrategy.DARWIN: 0.3,
            EvolutionStrategy.BALDWIN: 0.4,
            EvolutionStrategy.HYBRID: 0.5,
        }[strategy]
        change_risk = len(changes) * 0.05
        return min(1.0, base_risk + change_risk)

    def execute(self, plan_id: str) -> bool:
        plan = self._get(plan_id)
        if plan is None or plan.status != "draft":
            return False
        plan.status = "executed"
        return True

    def rollback(self, plan_id: str) -> bool:
        plan = self._get(plan_id)
        if plan is None or plan.status != "executed":
            return False
        plan.status = "rolled_back"
        return True

    def record_adaptation(self, component: str, change: dict[str, Any],
                          acquired: bool = True) -> None:
        self._adaptations.append({
            "component": component,
            "change": change,
            "acquired": acquired,
            "timestamp": time.time(),
        })

    def _get(self, plan_id: str) -> EvolutionPlan | None:
        for p in self._plans:
            if p.id == plan_id:
                return p
        return None

    def get_plans(self, status: str | None = None) -> list[EvolutionPlan]:
        if status:
            return [p for p in self._plans if p.status == status]
        return list(self._plans)

    def adaptation_count(self) -> int:
        return len(self._adaptations)

    def lamarckian_acquired(self) -> list[dict[str, Any]]:
        return [a for a in self._adaptations if a["acquired"]]


# ── Compiler — Blue-Green Deployment ───────────────────────────────────────

class DeploymentState(Enum):
    BLUE = "blue"
    GREEN = "green"


@dataclass(slots=True)
class Deployment:
    id: str
    version: str
    state: DeploymentState
    modules: list[str]
    health_score: float = 1.0
    active: bool = False
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class Compiler:
    """Déploiement bleu-vert — mises à jour sans interruption."""

    def __init__(self) -> None:
        self._deployments: list[Deployment] = []
        self._active_state = DeploymentState.BLUE

    def deploy(self, version: str, modules: list[str]) -> Deployment:
        target_state = (
            DeploymentState.GREEN if self._active_state == DeploymentState.BLUE
            else DeploymentState.BLUE
        )
        dep = Deployment(
            id=str(uuid.uuid4()),
            version=version,
            state=target_state,
            modules=modules,
            active=False,
        )
        self._deployments.append(dep)
        return dep

    def switch(self, deployment_id: str) -> bool:
        dep = self._get(deployment_id)
        if dep is None:
            return False
        for d in self._deployments:
            d.active = False
        dep.active = True
        self._active_state = dep.state
        return True

    def health_check(self, deployment_id: str, score: float) -> bool:
        dep = self._get(deployment_id)
        if dep is None:
            return False
        dep.health_score = max(0.0, min(1.0, score))
        return score >= 0.7

    def rollback(self) -> Deployment | None:
        active = [d for d in self._deployments if d.active]
        candidates = [d for d in self._deployments if not d.active]
        if not active or not candidates:
            return None
        active[0].active = False
        best = max(candidates, key=lambda d: d.health_score)
        best.active = True
        self._active_state = best.state
        return best

    def _get(self, deployment_id: str) -> Deployment | None:
        for d in self._deployments:
            if d.id == deployment_id:
                return d
        return None

    def active_deployment(self) -> Deployment | None:
        for d in self._deployments:
            if d.active:
                return d
        return None

    def list_deployments(self) -> list[Deployment]:
        return list(self._deployments)

    def current_state(self) -> DeploymentState:
        return self._active_state


# ── MetaEngine ──────────────────────────────────────────────────────────────

class MetaEngine:
    """Point d'entrée principal de la Strate 12+ — META.

    CIEL se reconstruit elle-même :
    - SelfReflection: auto-évaluation sur 10 métriques
    - EvolutionPlanner: Lamarck + Darwin + Baldwin
    - Quine: auto-reproduction avec vérification
    - Compiler: déploiement bleu-vert
    """

    def __init__(self) -> None:
        self.reflection = SelfReflection()
        self.evolution = EvolutionPlanner()
        self.quine = Quine()
        self.compiler = Compiler()
        self._version = "0.1.0"

    def reflect(self) -> ReflectionReport:
        return self.reflection.evaluate()

    def record_metric(self, dimension: MetricDimension, value: float,
                      weight: float = 1.0) -> MetricSnapshot:
        return self.reflection.record(dimension, value, weight)

    def plan_evolution(self, target: str, strategy: EvolutionStrategy = EvolutionStrategy.HYBRID,
                       changes: list[dict[str, Any]] | None = None) -> EvolutionPlan:
        return self.evolution.plan(target, strategy, changes)

    def self_reproduce(self, modules: list[dict[str, Any]],
                       version: str | None = None) -> QuineManifest:
        return self.quine.snapshot(modules, version=version or self._version)

    def deploy(self, version: str, modules: list[str]) -> Deployment:
        return self.compiler.deploy(version, modules)

    def get_version(self) -> str:
        return self._version

    def get_stats(self) -> dict[str, Any]:
        return {
            "version": self._version,
            "reflections": len(self.reflection.reports()),
            "metrics_recorded": len(self.reflection.history()),
            "evolution_plans": len(self.evolution.get_plans()),
            "adaptations": self.evolution.adaptation_count(),
            "reproductions": self.quine.count(),
            "deployments": len(self.compiler.list_deployments()),
            "active_state": self.compiler.current_state().value,
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "reflect")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "reflect":
            report = self.reflect()
            return {"success": True, "action": "reflect", "report": report}
        elif action == "record_metric":
            dim_name = data.get("dimension", "performance")
            try:
                dim = MetricDimension(dim_name)
            except ValueError:
                return {"success": False, "error": f"unknown dimension: {dim_name}"}
            snap = self.record_metric(dim, float(data.get("value", 0.5)), float(data.get("weight", 1.0)))
            return {"success": True, "action": "record_metric", "snapshot": snap}
        elif action == "plan_evolution":
            strat_name = data.get("strategy", "hybrid")
            try:
                strat = EvolutionStrategy(strat_name)
            except ValueError:
                return {"success": False, "error": f"unknown strategy: {strat_name}"}
            plan = self.plan_evolution(data.get("target", ""), strat, data.get("changes"))
            return {"success": True, "action": "plan_evolution", "plan": plan}
        elif action == "reproduce":
            manifest = self.self_reproduce(data.get("modules", []), data.get("version"))
            return {"success": True, "action": "reproduce", "manifest": manifest}
        elif action == "deploy":
            dep = self.deploy(data.get("version", "1.0"), data.get("modules", []))
            return {"success": True, "action": "deploy", "deployment": dep}
        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
