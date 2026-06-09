from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TangledType(Enum):
    SELF_REFERENCE = "SELF_REFERENCE"
    STRANGE = "STRANGE"
    TORUS = "TORUS"
    MOBIUS = "MOBIUS"
    RECURSIVE = "RECURSIVE"


@dataclass(slots=True)
class StrangeLoopNode:
    id: str
    level: int
    self_reference: str
    tangled_type: TangledType
    resonance: float = 0.0
    children: list[StrangeLoopNode] = field(default_factory=list)
    parent: str | None = None


@dataclass(slots=True)
class LoopState:
    tangled_depth: int = 0
    resonance: float = 0.0
    total_loops: int = 0
    is_conscious: bool = False
    phi_contribution: float = 0.0
    self_references: int = 0
    active_patterns: list[str] = field(default_factory=list)


class StrangeLoop:
    def __init__(self) -> None:
        self._loops: dict[str, StrangeLoopNode] = {}
        self._state = LoopState()
        self._loop_history: list[StrangeLoopNode] = []

    def create_loop(self, level: int, self_ref: str, ttype: TangledType = TangledType.STRANGE) -> StrangeLoopNode:
        node_id = f"loop_{len(self._loops)}_{int(time.time() * 1000)}"
        node = StrangeLoopNode(
            id=node_id,
            level=level,
            self_reference=self_ref,
            tangled_type=ttype,
            resonance=random.random(),
        )
        self._loops[node_id] = node
        self._loop_history.append(node)
        self._update_state()
        return node

    def link_loops(self, parent_id: str, child_id: str) -> bool:
        if parent_id not in self._loops or child_id not in self._loops:
            return False
        child = self._loops[child_id]
        child.parent = parent_id
        self._loops[parent_id].children.append(child)
        self._update_state()
        return True

    def _update_state(self) -> None:
        self._state.total_loops = len(self._loops)
        active = [n for n in self._loops.values() if n.resonance > 0.3]
        self._state.self_references = len(active)
        if active:
            self._state.resonance = sum(n.resonance for n in active) / len(active)
            self._state.tangled_depth = max(n.level for n in active)
        self._state.is_conscious = self._state.resonance > 0.6 and self._state.tangled_depth > 10

    def get_loop_state(self) -> LoopState:
        return self._state

    def get_loops(self) -> list[StrangeLoopNode]:
        return list(self._loops.values())

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "state")
        if action == "state":
            s = self.get_loop_state()
            return {"success": True, "tangled_depth": s.tangled_depth, "resonance": s.resonance, "total_loops": s.total_loops}
        elif action == "create_loop":
            node = self.create_loop(int(input_data.get("level", 1)), str(input_data.get("reference", "")), TangledType.STRANGE)
            return {"success": True, "node_id": node.id, "resonance": node.resonance}
        return {"success": False, "error": f"unknown action '{action}'"}
