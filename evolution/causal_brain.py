from __future__ import annotations

import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CausalEvent:
    id: str
    cause: str
    effect: str
    probability: float
    strength: float
    timestamp: float


@dataclass(slots=True)
class CausalGraph:
    nodes: set[str] = field(default_factory=set)
    edges: dict[tuple[str, str], float] = field(default_factory=dict)


class CausalBrain:
    def __init__(self) -> None:
        self._graph = CausalGraph()
        self._events: list[CausalEvent] = []

    def observe(self, cause: str, effect: str, probability: float = 0.5) -> CausalEvent:
        ev = CausalEvent(
            id=f"causal_{len(self._events)}",
            cause=cause,
            effect=effect,
            probability=probability,
            strength=probability,
            timestamp=time.time(),
        )
        self._events.append(ev)
        self._graph.nodes.add(cause)
        self._graph.nodes.add(effect)
        key = (cause, effect)
        if key in self._graph.edges:
            self._graph.edges[key] = 0.7 * self._graph.edges[key] + 0.3 * probability
        else:
            self._graph.edges[key] = probability
        return ev

    def infer_causes(self, effect: str) -> list[tuple[str, float]]:
        causes = []
        for (c, e), strength in self._graph.edges.items():
            if e == effect:
                causes.append((c, strength))
        causes.sort(key=lambda x: x[1], reverse=True)
        return causes

    def infer_effects(self, cause: str) -> list[tuple[str, float]]:
        effects = []
        for (c, e), strength in self._graph.edges.items():
            if c == cause:
                effects.append((e, strength))
        effects.sort(key=lambda x: x[1], reverse=True)
        return effects

    def counterfactual(self, cause: str, effect: str) -> float:
        key = (cause, effect)
        return self._graph.edges.get(key, 0.0)

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "state")
        if action == "state":
            return {"success": True, "nodes": len(self._graph.nodes), "edges": len(self._graph.edges), "events": len(self._events)}
        elif action == "observe":
            ev = self.observe(str(input_data.get("cause", "")), str(input_data.get("effect", "")), float(input_data.get("probability", 0.5)))
            return {"success": True, "event_id": ev.id, "strength": ev.strength}
        return {"success": False, "error": f"unknown action '{action}'"}
