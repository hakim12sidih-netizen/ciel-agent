"""
CIEL v∞.9 — Formal Plugin State Machine.
Guarded transitions with history, persistence, and forced recovery.
"""
from __future__ import annotations

import time
import uuid
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


__all__ = [
    "PluginState", "StateTransition", "StateMachine",
    "StateError", "TransitionDenied",
    "PLUGIN_STATE_MACHINE",
]


class PluginState(Enum):
    UNKNOWN = "unknown"
    INSTALLED = "installed"
    DISABLED = "disabled"
    ENABLED = "enabled"
    LOADING = "loading"
    ACTIVE = "active"
    UNLOADING = "unloading"
    ERROR = "error"
    UNINSTALLED = "uninstalled"
    FROZEN = "frozen"


VALID_TRANSITIONS: dict[PluginState, list[PluginState]] = {
    PluginState.UNKNOWN: [PluginState.INSTALLED, PluginState.ERROR],
    PluginState.INSTALLED: [PluginState.DISABLED, PluginState.ENABLED, PluginState.UNINSTALLED, PluginState.ERROR],
    PluginState.DISABLED: [PluginState.ENABLED, PluginState.UNINSTALLED, PluginState.LOADING, PluginState.ERROR],
    PluginState.ENABLED: [PluginState.LOADING, PluginState.DISABLED, PluginState.UNINSTALLED, PluginState.ERROR],
    PluginState.LOADING: [PluginState.ACTIVE, PluginState.ERROR, PluginState.DISABLED],
    PluginState.ACTIVE: [PluginState.UNLOADING, PluginState.DISABLED, PluginState.FROZEN, PluginState.ERROR],
    PluginState.UNLOADING: [PluginState.DISABLED, PluginState.ENABLED, PluginState.ERROR],
    PluginState.ERROR: [PluginState.DISABLED, PluginState.INSTALLED, PluginState.UNINSTALLED],
    PluginState.UNINSTALLED: [PluginState.INSTALLED],
    PluginState.FROZEN: [PluginState.ACTIVE, PluginState.ERROR],
}


class StateError(Exception):
    pass


class TransitionDenied(StateError):
    def __init__(self, plugin: str, from_state: PluginState, to_state: PluginState, reason: str = ""):
        self.plugin = plugin
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        super().__init__(f"Transition denied: {plugin} {from_state.value} → {to_state.value}: {reason}")


@dataclass
class StateTransition:
    from_state: PluginState
    to_state: PluginState
    timestamp: float
    reason: str = ""
    forced: bool = False

    def to_dict(self) -> dict:
        return {
            "from": self.from_state.value,
            "to": self.to_state.value,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "forced": self.forced,
        }


GuardFn = Callable[[str, PluginState, PluginState, dict], bool]


@dataclass
class Guard:
    name: str
    fn: GuardFn
    message: str = ""

    def check(self, plugin: str, from_state: PluginState, to_state: PluginState,
              context: dict) -> bool:
        try:
            return self.fn(plugin, from_state, to_state, context)
        except Exception:
            return False


@dataclass
class PluginStateData:
    current: PluginState = PluginState.UNKNOWN
    history: list[StateTransition] = field(default_factory=list)
    error_count: int = 0
    last_error: str = ""
    last_active: float = 0.0


class StateMachine:
    def __init__(self):
        self._states: dict[str, PluginStateData] = {}
        self._guards: dict[tuple[PluginState, PluginState], list[Guard]] = {}
        self._on_transition: list[Callable] = []
        self._global_guards: list[Guard] = []

    def get_state(self, plugin: str) -> PluginState:
        return self._states.get(plugin, PluginStateData()).current

    def add_guard(self, from_state: PluginState, to_state: PluginState,
                  guard: Guard):
        key = (from_state, to_state)
        if key not in self._guards:
            self._guards[key] = []
        self._guards[key].append(guard)

    def add_global_guard(self, guard: Guard):
        self._global_guards.append(guard)

    def on_transition(self, callback: Callable):
        self._on_transition.append(callback)

    def can_transition(self, plugin: str, from_state: PluginState,
                       to_state: PluginState, context: dict | None = None) -> tuple[bool, str]:
        context = context or {}

        allowed = VALID_TRANSITIONS.get(from_state, [])
        if to_state not in allowed:
            return False, f"Invalid transition: {from_state.value} → {to_state.value}"

        for guard in self._global_guards:
            if not guard.check(plugin, from_state, to_state, context):
                return False, guard.message or f"Global guard '{guard.name}' denied"

        for guard in self._guards.get((from_state, to_state), []):
            if not guard.check(plugin, from_state, to_state, context):
                return False, guard.message or f"Guard '{guard.name}' denied"

        return True, ""

    def transition(self, plugin: str, to_state: PluginState,
                   reason: str = "", forced: bool = False,
                   context: dict | None = None) -> StateTransition:
        data = self._states.setdefault(plugin, PluginStateData())
        from_state = data.current

        if not forced:
            ok, msg = self.can_transition(plugin, from_state, to_state, context)
            if not ok:
                raise TransitionDenied(plugin, from_state, to_state, msg)

        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=time.time(),
            reason=reason,
            forced=forced,
        )

        data.current = to_state
        data.history.append(transition)

        if to_state == PluginState.ERROR:
            data.error_count += 1
        if to_state == PluginState.ACTIVE:
            data.last_active = time.time()
        if to_state == PluginState.UNINSTALLED:
            data.history.clear()

        for cb in self._on_transition:
            try:
                cb(plugin, transition)
            except Exception:
                pass

        return transition

    def force_transition(self, plugin: str, to_state: PluginState,
                         reason: str = "") -> StateTransition:
        return self.transition(plugin, to_state, reason=reason, forced=True)

    def reset(self, plugin: str):
        self._states[plugin] = PluginStateData()

    def get_history(self, plugin: str, limit: int = 20) -> list[StateTransition]:
        data = self._states.get(plugin)
        if not data:
            return []
        return data.history[-limit:]

    def get_all_states(self) -> dict[str, str]:
        return {
            name: data.current.value
            for name, data in self._states.items()
        }

    def get_stats(self, plugin: str) -> dict:
        data = self._states.get(plugin)
        if not data:
            return {"error": "unknown plugin"}
        return {
            "current": data.current.value,
            "error_count": data.error_count,
            "last_error": data.last_error,
            "last_active": data.last_active,
            "history_size": len(data.history),
            "transitions": len(data.history),
        }


PLUGIN_STATE_MACHINE = StateMachine()

PLUGIN_STATE_MACHINE.add_global_guard(
    Guard("not_error",
          lambda p, f, t, c: PLUGIN_STATE_MACHINE.get_state(p) != PluginState.ERROR or t == PluginState.DISABLED,
          "Cannot transition from ERROR except to DISABLED")
)
PLUGIN_STATE_MACHINE.add_global_guard(
    Guard("not_uninstalled",
          lambda p, f, t, c: PLUGIN_STATE_MACHINE.get_state(p) != PluginState.UNINSTALLED or t == PluginState.INSTALLED,
          "Cannot transition from UNINSTALLED except to INSTALLED")
)
