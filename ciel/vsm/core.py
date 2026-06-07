from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Self

import numpy as np


class VSMState(Enum):
    VIABLE = "viable"
    CRISIS = "crisis"
    FRAGMENTED = "fragmented"
    COLLAPSED = "collapsed"


@dataclass(slots=True)
class VarietyEngine:
    variety: int
    capacity: int

    @staticmethod
    def from_array(arr: np.ndarray) -> VarietyEngine:
        return VarietyEngine(variety=int(np.prod(arr.shape)), capacity=0)

    def attenuate(self, factor: float) -> None:
        self.variety = max(1, int(self.variety * (1 - factor)))

    def amplify(self, factor: float) -> None:
        self.capacity = int(self.capacity * (1 + factor)) or factor

    def absorbs(self, other: VarietyEngine) -> bool:
        return self.capacity >= other.variety


@dataclass(slots=True)
class AlgedonicSignal:
    source: str
    severity: float
    message: str


@dataclass(slots=True)
class AlgedonicAlertSystem:
    threshold: float = 0.7
    signals: list[AlgedonicSignal] = field(default_factory=list)

    def evaluate(self, s3_variety: int, s4_variety: int) -> AlgedonicSignal | None:
        mismatch = abs(s3_variety - s4_variety) / max(s3_variety, s4_variety, 1)
        if mismatch > self.threshold:
            signal = AlgedonicSignal(
                source="algedonic",
                severity=mismatch,
                message=f"S3/S4 mismatch {mismatch:.2f} exceeds threshold {self.threshold}",
            )
            self.signals.append(signal)
            return signal
        return None


@dataclass(slots=True)
class Subsystem:
    name: str
    variety: int = 0
    complexity: float = 0.0
    connectivity: float = 0.0
    homeostasis_level: float = 1.0

    def compute_variety(self) -> int:
        return self.variety

    def state(self) -> VSMState:
        if self.homeostasis_level <= 0.2:
            return VSMState.COLLAPSED
        if self.homeostasis_level <= 0.5:
            return VSMState.FRAGMENTED
        if self.homeostasis_level <= 0.8:
            return VSMState.CRISIS
        return VSMState.VIABLE


@dataclass(slots=True)
class S1Implementation(Subsystem):
    units: list[Subsystem] = field(default_factory=list)
    local_variety_engine: VarietyEngine | None = None

    def add_unit(self, unit: Subsystem) -> None:
        self.units.append(unit)
        self.variety += unit.variety
        self.complexity += unit.complexity

    def compute_variety(self) -> int:
        return sum(u.compute_variety() for u in self.units) + self.variety


@dataclass(slots=True)
class S2Coordination(Subsystem):
    conflict_log: list[dict] = field(default_factory=list)
    oscillation_damping: float = 0.0

    def resolve_conflict(self, unit_a: Subsystem, unit_b: Subsystem) -> bool:
        variety_gap = abs(unit_a.variety - unit_b.variety)
        resolved = variety_gap < self.complexity
        self.conflict_log.append(
            {"a": unit_a.name, "b": unit_b.name, "resolved": resolved, "gap": variety_gap}
        )
        if resolved:
            self.oscillation_damping = min(1.0, self.oscillation_damping + 0.1)
        return resolved


@dataclass(slots=True)
class S3Control(Subsystem):
    resource_pool: float = 100.0
    homeostasis_target: float = 1.0

    def allocate(self, unit: Subsystem, amount: float) -> float:
        actual = min(amount, self.resource_pool)
        self.resource_pool -= actual
        unit.homeostasis_level = min(1.0, unit.homeostasis_level + actual / 100)
        return actual

    def regulate(self, actual: float, target: float) -> float:
        error = target - actual
        correction = error * self.connectivity
        self.homeostasis_level = max(0.0, min(1.0, self.homeostasis_level + correction))
        return correction


@dataclass(slots=True)
class S3StarAudit(Subsystem):
    audit_log: list[dict] = field(default_factory=list)
    integrity_score: float = 1.0

    def inspect(self, target: Subsystem) -> dict:
        findings = {
            "target": target.name,
            "variety": target.variety,
            "homeostasis": target.homeostasis_level,
            "integrity": self.integrity_score,
        }
        self.audit_log.append(findings)
        if target.homeostasis_level < 0.5:
            self.integrity_score = max(0.0, self.integrity_score - 0.1)
        return findings


@dataclass(slots=True)
class S4Intelligence(Subsystem):
    scans: list[dict] = field(default_factory=list)
    future_models: list[np.ndarray] = field(default_factory=list)

    def scan_environment(self, external_variety: int) -> dict:
        scan = {"external_variety": external_variety, "complexity": self.complexity}
        self.scans.append(scan)
        self.variety = external_variety
        return scan

    def project_model(self, horizon: int = 10) -> np.ndarray:
        model = np.cumsum(np.random.randn(horizon) * self.complexity + self.homeostasis_level)
        self.future_models.append(model)
        return model


@dataclass(slots=True)
class S5Identity(Subsystem):
    policy: str = ""
    values: list[str] = field(default_factory=list)
    closure_threshold: float = 0.9

    def define_policy(self, policy: str) -> None:
        self.policy = policy

    def closure_check(self, system_variety: int, environment_variety: int) -> bool:
        ratio = system_variety / max(environment_variety, 1)
        return ratio >= self.closure_threshold


@dataclass(slots=True)
class ViableSystemModel:
    s1: S1Implementation
    s2: S2Coordination
    s3: S3Control
    s3_star: S3StarAudit
    s4: S4Intelligence
    s5: S5Identity
    algedonic: AlgedonicAlertSystem = field(default_factory=AlgedonicAlertSystem)
    sub_models: list[ViableSystemModel] = field(default_factory=list)
    _state: VSMState = VSMState.VIABLE

    @classmethod
    def create(cls) -> ViableSystemModel:
        return cls(
            s1=S1Implementation(name="S1-Implementation"),
            s2=S2Coordination(name="S2-Coordination"),
            s3=S3Control(name="S3-Control"),
            s3_star=S3StarAudit(name="S3*-Audit"),
            s4=S4Intelligence(name="S4-Intelligence"),
            s5=S5Identity(name="S5-Identity"),
        )

    def add_operational_unit(self, name: str, variety: int, complexity: float) -> Subsystem:
        unit = Subsystem(name=name, variety=variety, complexity=complexity)
        self.s1.add_unit(unit)
        return unit

    def add_sub_model(self, model: ViableSystemModel) -> None:
        self.sub_models.append(model)

    def homeostasis_loop(self) -> None:
        for unit in self.s1.units:
            self.s3.regulate(unit.homeostasis_level, self.s3.homeostasis_target)

    def intelligence_loop(self, external_variety: int) -> np.ndarray:
        self.s4.scan_environment(external_variety)
        return self.s4.project_model()

    def audit_loop(self) -> list[dict]:
        findings = []
        for unit in self.s1.units:
            findings.append(self.s3_star.inspect(unit))
        findings.append(self.s3_star.inspect(self.s2))
        findings.append(self.s3_star.inspect(self.s4))
        return findings

    def check_algedonic(self) -> AlgedonicSignal | None:
        return self.algedonic.evaluate(self.s3.variety, self.s4.variety)

    def evaluate_state(self) -> VSMState:
        if self.s3.homeostasis_level <= 0.2:
            self._state = VSMState.COLLAPSED
        elif self.s3.homeostasis_level <= 0.5:
            self._state = VSMState.FRAGMENTED
        elif self.s3_star.integrity_score < 0.5:
            self._state = VSMState.CRISIS
        else:
            self._state = VSMState.VIABLE
        return self._state

    def step(self, external_variety: int) -> VSMState:
        self.homeostasis_loop()
        self.intelligence_loop(external_variety)
        self.audit_loop()
        self.check_algedonic()
        return self.evaluate_state()
