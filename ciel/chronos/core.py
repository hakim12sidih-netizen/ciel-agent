from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TemporalGranularity(Enum):
    MILLISECOND = 0.001
    INSTANT = 0.01
    SECOND = 1.0
    MINUTE = 60.0
    HOUR = 3600.0
    DAY = 86400.0
    WEEK = 604800.0
    CYCLE = 0.0  # event-based


@dataclass(slots=True)
class TemporalEvent:
    id: str
    timestamp: float
    duration: float = 0.0
    content: str = ""
    salience: float = 0.5
    event_type: str = "generic"


@dataclass(slots=True)
class TemporalInterval:
    start: float
    end: float
    label: str = ""
    events: list[TemporalEvent] = field(default_factory=list)

    def duration(self) -> float:
        return self.end - self.start

    def contains(self, t: float) -> bool:
        return self.start <= t <= self.end

    def overlaps(self, other: TemporalInterval) -> bool:
        return self.start < other.end and other.start < self.end


class InternalClock:
    """Horloge interne — perception subjective du temps."""

    def __init__(self, base_rate: float = 1.0):
        self.base_rate = base_rate
        self.subjective_time: float = 0.0
        self.objective_time: float = 0.0
        self.drift: float = 0.0
        self._rate_modulator: Callable[[float], float] | None = None

    def set_rate_modulator(self, modulator: Callable[[float], float]) -> None:
        self._rate_modulator = modulator

    def tick(self, dt: float = 1.0) -> float:
        rate = self.base_rate
        if self._rate_modulator:
            rate = self._rate_modulator(self.objective_time)
        self.objective_time += dt
        self.subjective_time += dt * rate
        self.drift = self.subjective_time - self.objective_time
        return self.subjective_time

    def reset(self) -> None:
        self.subjective_time = 0.0
        self.objective_time = 0.0
        self.drift = 0.0


class TemporalMemory:
    """Mémoire temporelle — séquencement, anticipation, rythmes."""

    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.events: list[TemporalEvent] = []
        self.intervals: list[TemporalInterval] = []

    def record(self, event: TemporalEvent) -> None:
        self.events.append(event)
        if len(self.events) > self.capacity:
            self.events.pop(0)

    def add_interval(self, interval: TemporalInterval) -> None:
        self.intervals.append(interval)

    def recall(self, start: float, end: float) -> list[TemporalEvent]:
        return [e for e in self.events if start <= e.timestamp <= end]

    def sequence(self) -> list[tuple[float, str]]:
        return sorted([(e.timestamp, e.content) for e in self.events])

    def predict_next(self) -> TemporalEvent | None:
        if len(self.events) < 2:
            return None
        intervals = [self.events[i + 1].timestamp - self.events[i].timestamp for i in range(len(self.events) - 1)]
        mean_interval = sum(intervals) / len(intervals)
        last = self.events[-1]
        return TemporalEvent(
            id="predicted",
            timestamp=last.timestamp + mean_interval,
            content=f"Prédiction après {last.content}",
            salience=0.3,
        )


class RhythmDetector:
    """Détection de rythmes et patterns temporels."""

    def __init__(self):
        self.periods: list[float] = []

    def detect(self, timestamps: list[float]) -> list[float]:
        if len(timestamps) < 3:
            return []
        intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        if not intervals:
            return []
        mean_iv = sum(intervals) / len(intervals)
        self.periods = [mean_iv]
        # detect sub-harmonics
        for k in range(2, 5):
            candidate = mean_iv / k
            matches = sum(1 for iv in intervals if abs(iv - candidate) < candidate * 0.2)
            if matches > len(intervals) * 0.3:
                self.periods.append(candidate)
        return sorted(self.periods)

    def is_rhythmic(self, timestamps: list[float], tolerance: float = 0.15) -> bool:
        if len(timestamps) < 3:
            return False
        intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        if not intervals:
            return False
        mean_iv = sum(intervals) / len(intervals)
        return all(abs(iv - mean_iv) < mean_iv * tolerance for iv in intervals)


class TemporalReasoning:
    """Raisonnement temporel — Allen intervals, causalité temporelle."""

    ALLEN_RELATIONS = [
        "before", "after", "meets", "met_by",
        "overlaps", "overlapped_by", "during", "contains",
        "starts", "started_by", "finishes", "finished_by",
        "equal",
    ]

    @staticmethod
    def relation(a: TemporalInterval, b: TemporalInterval) -> str:
        if a.end < b.start:
            return "before"
        if a.start > b.end:
            return "after"
        if a.end == b.start:
            return "meets"
        if a.start == b.end:
            return "met_by"
        if a.start < b.start and a.end > b.start and a.end < b.end:
            return "overlaps"
        if b.start < a.start and b.end > a.start and b.end < a.end:
            return "overlapped_by"
        if a.start >= b.start and a.end <= b.end:
            return "during"
        if a.start <= b.start and a.end >= b.end:
            return "contains"
        if a.start == b.start and a.end < b.end:
            return "starts"
        if a.start == b.start and a.end > b.end:
            return "started_by"
        if a.end == b.end and a.start > b.start:
            return "finishes"
        if a.end == b.end and a.start < b.start:
            return "finished_by"
        return "equal"

    @staticmethod
    def transitive_closure(relations: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
        """Compute transitive closure of Allen relations (simplified)."""
        graph: dict[str, set[str]] = {}
        for a, r, b in relations:
            if r == "before":
                graph.setdefault(a, set()).add(b)
        changed = True
        while changed:
            changed = False
            for a in list(graph.keys()):
                for b in list(graph[a]):
                    for c in graph.get(b, set()):
                        if c not in graph[a]:
                            graph[a].add(c)
                            changed = True
        result = []
        for a, bs in graph.items():
            for b in bs:
                result.append((a, "before", b))
        return result


class ChronosEngine:
    """Moteur temporel intégré — perception, mémoire, rythme, raisonnement."""

    def __init__(self):
        self.clock = InternalClock()
        self.memory = TemporalMemory()
        self.rhythm = RhythmDetector()
        self.reasoning = TemporalReasoning()
        self._listeners: list[Callable[[TemporalEvent], None]] = []

    def register_listener(self, listener: Callable[[TemporalEvent], None]) -> None:
        self._listeners.append(listener)

    def tick(self, dt: float = 1.0) -> float:
        return self.clock.tick(dt)

    def observe(self, content: str, event_type: str = "generic", salience: float = 0.5) -> TemporalEvent:
        event = TemporalEvent(
            id=f"evt_{len(self.memory.events)}",
            timestamp=self.clock.subjective_time,
            content=content,
            salience=salience,
            event_type=event_type,
        )
        self.memory.record(event)
        for l in self._listeners:
            l(event)
        return event

    def detect_rhythms(self) -> list[float]:
        timestamps = [e.timestamp for e in self.memory.events]
        return self.rhythm.detect(timestamps)

    def predict(self) -> TemporalEvent | None:
        return self.memory.predict_next()

    def interval_between(self, event_a: str, event_b: str) -> TemporalInterval | None:
        matching = [e for e in self.memory.events if e.id == event_a or e.content == event_a]
        if len(matching) < 2:
            return None
        a = matching[0]
        b = matching[-1]
        return TemporalInterval(start=a.timestamp, end=b.timestamp, label=f"{a.content} → {b.content}")

    def synchronize(self, external_time: float) -> None:
        self.clock.objective_time = external_time
