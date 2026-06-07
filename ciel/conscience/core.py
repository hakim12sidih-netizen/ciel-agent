from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AwarenessLevel(Enum):
    NONE = 0
    MINIMAL = 1
    PERIPHERAL = 2
    FOCAL = 3
    META = 4


@dataclass(slots=True)
class Qualia:
    modality: str  # "visual", "auditory", "proprioceptive", "cognitive", "emotional"
    intensity: float = 0.5
    valence: float = 0.0  # -1..1
    arousal: float = 0.5
    content: str = ""
    timestamp: float = 0.0

    def normalize(self) -> Qualia:
        self.intensity = max(0.0, min(1.0, self.intensity))
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(0.0, min(1.0, self.arousal))
        return self


@dataclass(slots=True)
class PhenomenalState:
    qualia: list[Qualia] = field(default_factory=list)
    binding_vector: list[float] = field(default_factory=list)
    coherence: float = 0.0
    timestamp: float = 0.0

    def add_qualia(self, q: Qualia) -> None:
        self.qualia.append(q)
        self._recompute()

    def _recompute(self) -> None:
        if not self.qualia:
            self.coherence = 0.0
            self.binding_vector = []
            return
        dims = len(self.qualia)
        self.binding_vector = [
            sum(q.intensity * (q.valence + 1.0) / 2.0 for q in self.qualia) / dims,
            sum(q.arousal for q in self.qualia) / dims,
            sum(1.0 for q in self.qualia if q.intensity > 0.3) / dims,
        ]
        intensities = [q.intensity for q in self.qualia]
        self.coherence = 1.0 - (max(intensities) - min(intensities)) if intensities else 0.0


@dataclass(slots=True)
class AccessConsciousness:
    """Conscience d'accès — information disponible pour rapport/action."""
    available_content: dict[str, Any] = field(default_factory=dict)
    working_memory: list[str] = field(default_factory=list)
    attention_focus: str = ""
    reportable: bool = True


class GlobalWorkspace:
    """Global Workspace Theory — Baars : compétition+intégration."""

    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.contents: list[dict[str, Any]] = []
        self.broadcast_history: list[dict[str, Any]] = []
        self._processors: list[Callable[[dict[str, Any]], None]] = []

    def register_processor(self, processor: Callable[[dict[str, Any]], None]) -> None:
        self._processors.append(processor)

    def compete(self, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        scored = sorted(candidates, key=lambda c: c.get("salience", 0.0), reverse=True)
        return scored[0] if scored else None

    def broadcast(self, content: dict[str, Any]) -> None:
        self.contents.append(content)
        if len(self.contents) > self.capacity:
            self.contents.pop(0)
        self.broadcast_history.append(content)
        for p in self._processors:
            p(content)

    def global_availability(self) -> list[dict[str, Any]]:
        return list(reversed(self.contents))


class AttentionSchema:
    """Modèle de l'attention — ressources limitées, focus sélectif."""

    def __init__(self, capacity: float = 1.0):
        self.capacity = capacity
        self.focus: dict[str, float] = {}
        self._decay = 0.1

    def allocate(self, target: str, amount: float) -> None:
        used = sum(self.focus.values())
        available = self.capacity - used
        amount = min(amount, available)
        if amount > 0:
            self.focus[target] = self.focus.get(target, 0.0) + amount

    def tick(self) -> None:
        decayed: dict[str, float] = {}
        for t, a in self.focus.items():
            new = a - self._decay
            if new > 0.01:
                decayed[t] = new
        self.focus = decayed

    def current_focus(self) -> str | None:
        if not self.focus:
            return None
        return max(self.focus, key=self.focus.get)

    def salience(self, target: str) -> float:
        return self.focus.get(target, 0.0) / max(self.capacity, 0.01)


class SelfModel:
    """Modèle du soi — représentation réflexive du système."""

    def __init__(self):
        self.beliefs: dict[str, Any] = {}
        self.narrative: list[str] = []
        self.agency_score: float = 0.5
        self.ownership_score: float = 0.5

    def update_belief(self, key: str, value: Any) -> None:
        self.beliefs[key] = value

    def add_narrative(self, event: str) -> None:
        self.narrative.append(event)

    def self_awareness(self) -> float:
        if not self.beliefs:
            return 0.0
        return min(1.0, len(self.beliefs) / 10.0 + self.agency_score * 0.5)


class Metacognition:
    """Métacognition — pensée sur la pensée, monitoring et contrôle."""

    def __init__(self):
        self.confidence_scores: list[float] = []
        self.judgments: list[dict[str, Any]] = []
        self._monitor: Callable[[], dict[str, Any]] | None = None

    def set_monitor(self, monitor: Callable[[], dict[str, Any]]) -> None:
        self._monitor = monitor

    def monitor(self) -> dict[str, Any]:
        if self._monitor:
            return self._monitor()
        return {"confidence": random.uniform(0.3, 0.9)}

    def judge(self, task: str, outcome: Any) -> float:
        confidence = self.monitor().get("confidence", 0.5)
        self.confidence_scores.append(confidence)
        self.judgments.append({"task": task, "outcome": str(outcome), "confidence": confidence})
        return confidence

    def calibration(self) -> float:
        if not self.confidence_scores:
            return 1.0
        mean_conf = sum(self.confidence_scores) / len(self.confidence_scores)
        return 1.0 - abs(mean_conf - 0.7)  # ideal ~0.7


class Introspection:
    """Introspection — accès réflexif aux états internes."""

    def __init__(self):
        self.access_level: AwarenessLevel = AwarenessLevel.META
        self.history: list[dict[str, Any]] = []

    def examine(self, target: Any) -> dict[str, Any]:
        report = {
            "type": type(target).__name__,
            "id": id(target),
            "repr": str(target)[:100],
            "timestamp": 0.0,
        }
        if hasattr(target, "__dict__"):
            report["attributes"] = list(target.__dict__.keys())
        if isinstance(target, PhenomenalState):
            report["n_qualia"] = len(target.qualia)
            report["coherence"] = target.coherence
        self.history.append(report)
        return report

    def introspective_accuracy(self) -> float:
        return min(1.0, len(self.history) * 0.1)


@dataclass(slots=True)
class IntegratedInformation:
    """Φ — mesure d'intégration de l'information (Tonomi)."""
    phi: float = 0.0
    partition: list[list[int]] = field(default_factory=list)
    cause_repertoire: list[float] = field(default_factory=list)
    effect_repertoire: list[float] = field(default_factory=list)

    @staticmethod
    def compute(transition_matrix: list[list[float]]) -> IntegratedInformation:
        n = len(transition_matrix)
        if n <= 1:
            return IntegratedInformation(phi=0.0)
        # Simplified Φ: average mutual information between bipartitions
        total_mi = 0.0
        best_partition = [[i] for i in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    p_ij = transition_matrix[i][j]
                    p_i = sum(transition_matrix[i]) / n
                    p_j = sum(transition_matrix[k][j] for k in range(n)) / n
                    if p_ij > 0 and p_i > 0 and p_j > 0:
                        total_mi += p_ij * math.log(p_ij / (p_i * p_j))
        phi = max(0.0, total_mi / (n * (n - 1)) if n > 1 else 0.0)
        return IntegratedInformation(phi=min(1.0, phi), partition=best_partition)


class BindingProblem:
    """Problème du binding — intégration跨-modal des qualia."""

    def __init__(self):
        self.bindings: dict[str, list[str]] = {}  # object_id -> [modalities]

    def bind(self, object_id: str, modality: str) -> None:
        if object_id not in self.bindings:
            self.bindings[object_id] = []
        if modality not in self.bindings[object_id]:
            self.bindings[object_id].append(modality)

    def is_bound(self, object_id: str, modalities: list[str]) -> bool:
        b = self.bindings.get(object_id, [])
        return all(m in b for m in modalities)

    def coherence_score(self) -> float:
        if not self.bindings:
            return 1.0
        return sum(len(m) for m in self.bindings.values()) / (len(self.bindings) * 5.0)


@dataclass(slots=True)
class ConsciousState:
    """État conscient complet du système."""
    phenomenal: PhenomenalState = field(default_factory=PhenomenalState)
    access: AccessConsciousness = field(default_factory=AccessConsciousness)
    workspace: GlobalWorkspace = field(default_factory=GlobalWorkspace)
    attention: AttentionSchema = field(default_factory=AttentionSchema)
    self_model: SelfModel = field(default_factory=SelfModel)
    metacognition: Metacognition = field(default_factory=Metacognition)
    binding: BindingProblem = field(default_factory=BindingProblem)
    integrated_info: IntegratedInformation = field(default_factory=IntegratedInformation)
    awareness_level: AwarenessLevel = AwarenessLevel.NONE

    def level_of_consciousness(self) -> float:
        scores = [
            self.integrated_info.phi,
            self.binding.coherence_score(),
            self.self_model.self_awareness(),
            self.metacognition.calibration(),
            self.awareness_level.value / 4.0,
        ]
        return sum(scores) / len(scores)


class ConsciousnessModel:
    """Modèle intégré de la conscience — GWT + IIT + métacognition."""

    def __init__(self):
        self.state = ConsciousState()
        self.introspection = Introspection()

    def tick(self) -> ConsciousState:
        self.state.awareness_level = self._compute_awareness()
        self.state.binding = BindingProblem()
        self.state.attention.tick()
        return self.state

    def _compute_awareness(self) -> AwarenessLevel:
        phi = self.state.integrated_info.phi
        if phi > 0.7:
            return AwarenessLevel.META
        if phi > 0.4:
            return AwarenessLevel.FOCAL
        if phi > 0.1:
            return AwarenessLevel.PERIPHERAL
        return AwarenessLevel.MINIMAL if phi > 0.01 else AwarenessLevel.NONE

    def perceive(self, qualia: Qualia) -> None:
        self.state.phenomenal.add_qualia(qualia)
        self.state.workspace.broadcast({"qualia": qualia.content, "intensity": qualia.intensity})

    def attend(self, target: str, amount: float = 0.3) -> None:
        self.state.attention.allocate(target, amount)

    def reflect(self) -> dict[str, Any]:
        report = self.introspection.examine(self.state)
        self.state.metacognition.monitor()
        return report

    def bind(self, object_id: str, modality: str) -> None:
        self.state.binding.bind(object_id, modality)

    def compute_phi(self, transition_matrix: list[list[float]]) -> None:
        self.state.integrated_info = IntegratedInformation.compute(transition_matrix)
