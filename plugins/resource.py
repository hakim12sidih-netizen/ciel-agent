"""
CIEL v∞.9 — Plugin Resource Controller.
CPU tracking, memory estimation, rate limiting, quotas.
"""
from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable


__all__ = [
    "ResourceController", "ResourceQuota", "ResourceUsage",
    "RateLimiter", "get_resource_controller",
]


@dataclass
class ResourceQuota:
    max_cpu_ms_per_minute: float = 60_000.0
    max_memory_bytes: int = 256 * 1024 * 1024
    max_hooks_per_second: float = 100.0
    max_concurrent_hooks: int = 10
    cooldown_seconds: float = 1.0

    def to_dict(self) -> dict:
        return {
            "max_cpu_ms_per_minute": self.max_cpu_ms_per_minute,
            "max_memory_bytes": self.max_memory_bytes,
            "max_memory_mb": round(self.max_memory_bytes / (1024 * 1024), 1),
            "max_hooks_per_second": self.max_hooks_per_second,
            "max_concurrent_hooks": self.max_concurrent_hooks,
            "cooldown_seconds": self.cooldown_seconds,
        }


@dataclass
class ResourceUsage:
    plugin: str
    cpu_ms: float = 0.0
    memory_bytes: int = 0
    hook_calls: int = 0
    errors: int = 0
    last_active: float = 0.0
    rate_limited: bool = False

    def to_dict(self) -> dict:
        return {
            "plugin": self.plugin,
            "cpu_ms": round(self.cpu_ms, 1),
            "memory_bytes": self.memory_bytes,
            "memory_mb": round(self.memory_bytes / (1024 * 1024), 1),
            "hook_calls": self.hook_calls,
            "errors": self.errors,
            "last_active": self.last_active,
            "rate_limited": self.rate_limited,
        }


class _SlidingWindow:
    def __init__(self, window_seconds: float = 60.0):
        self._window = window_seconds
        self._events: list[float] = []
        self._lock = threading.Lock()

    def add(self, value: float = 0.0):
        now = time.time()
        with self._lock:
            self._events.append(now)
            self._trim(now)

    def count(self) -> int:
        now = time.time()
        with self._lock:
            self._trim(now)
            return len(self._events)

    def _trim(self, now: float):
        cutoff = now - self._window
        while self._events and self._events[0] < cutoff:
            self._events.pop(0)

    def reset(self):
        with self._lock:
            self._events.clear()


class RateLimiter:
    def __init__(self, max_per_second: float = 100.0):
        self._max_per_second = max_per_second
        self._window = _SlidingWindow(1.0)
        self._lock = threading.Lock()

    def allow(self) -> bool:
        current = self._window.count()
        if current >= self._max_per_second:
            return False
        self._window.add()
        return True

    @property
    def utilization(self) -> float:
        return min(1.0, self._window.count() / max(1, self._max_per_second))


class ResourceController:
    def __init__(self):
        self._usages: dict[str, ResourceUsage] = {}
        self._quotas: dict[str, ResourceQuota] = {}
        self._rate_limiters: dict[str, RateLimiter] = {}
        self._cpu_windows: dict[str, _SlidingWindow] = {}
        self._concurrent: dict[str, int] = {}
        self._cooldowns: dict[str, float] = {}
        self._lock = threading.RLock()
        self._default_quota = ResourceQuota()

    def set_quota(self, plugin: str, quota: ResourceQuota):
        with self._lock:
            self._quotas[plugin] = quota

    def get_quota(self, plugin: str) -> ResourceQuota:
        return self._quotas.get(plugin, self._default_quota)

    def get_usage(self, plugin: str) -> ResourceUsage:
        with self._lock:
            if plugin not in self._usages:
                self._usages[plugin] = ResourceUsage(plugin=plugin)
            return self._usages[plugin]

    def track_hook(self, plugin: str, duration_ms: float) -> bool:
        now = time.time()
        quota = self.get_quota(plugin)

        with self._lock:
            usage = self._usages.setdefault(plugin, ResourceUsage(plugin=plugin))
            usage.hook_calls += 1
            usage.cpu_ms += duration_ms
            usage.last_active = now
            usage.rate_limited = False

            if plugin not in self._cpu_windows:
                self._cpu_windows[plugin] = _SlidingWindow(60.0)
            self._cpu_windows[plugin].add(duration_ms)

            cpu_used = self._cpu_windows[plugin].count() * (duration_ms or 1)
            if cpu_used > quota.max_cpu_ms_per_minute:
                usage.rate_limited = True
                return False

            if plugin not in self._rate_limiters:
                self._rate_limiters[plugin] = RateLimiter(quota.max_hooks_per_second)
            limiter = self._rate_limiters[plugin]
            if not limiter.allow():
                usage.rate_limited = True
                return False

            concurrent = self._concurrent.get(plugin, 0)
            if concurrent >= quota.max_concurrent_hooks:
                usage.rate_limited = True
                return False
            self._concurrent[plugin] = concurrent + 1

            if plugin in self._cooldowns and now < self._cooldowns[plugin]:
                usage.rate_limited = True
                return False

        return True

    def release_hook(self, plugin: str):
        with self._lock:
            self._concurrent[plugin] = max(0, self._concurrent.get(plugin, 0) - 1)

    def cooldown(self, plugin: str, duration: float | None = None):
        quota = self.get_quota(plugin)
        with self._lock:
            self._cooldowns[plugin] = time.time() + (duration or quota.cooldown_seconds)

    def track_error(self, plugin: str):
        with self._lock:
            usage = self._usages.setdefault(plugin, ResourceUsage(plugin=plugin))
            usage.errors += 1

    def estimate_memory(self, plugin: str, obj: Any) -> int:
        try:
            size = _estimate_size(obj)
            with self._lock:
                usage = self._usages.setdefault(plugin, ResourceUsage(plugin=plugin))
                usage.memory_bytes = size
            return size
        except Exception:
            return 0

    def get_all_usages(self) -> list[dict]:
        with self._lock:
            return [u.to_dict() for u in self._usages.values()]

    def get_stats(self) -> dict:
        with self._lock:
            total_cpu = sum(u.cpu_ms for u in self._usages.values())
            total_memory = sum(u.memory_bytes for u in self._usages.values())
            total_hooks = sum(u.hook_calls for u in self._usages.values())
            rate_limited_plugins = sum(1 for u in self._usages.values() if u.rate_limited)
            return {
                "plugins_tracked": len(self._usages),
                "total_cpu_ms": round(total_cpu, 1),
                "total_memory_bytes": total_memory,
                "total_memory_mb": round(total_memory / (1024 * 1024), 1),
                "total_hook_calls": total_hooks,
                "rate_limited_plugins": rate_limited_plugins,
                "quotas_set": len(self._quotas),
            }


_CONTROLLER_SINGLETON: ResourceController | None = None


def get_resource_controller() -> ResourceController:
    global _CONTROLLER_SINGLETON
    if _CONTROLLER_SINGLETON is None:
        _CONTROLLER_SINGLETON = ResourceController()
    return _CONTROLLER_SINGLETON


def _estimate_size(obj: Any, seen: set | None = None) -> int:
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = 0
    try:
        size = _BASE_SIZE.get(type(obj), 0)
    except Exception:
        size = 0

    if isinstance(obj, (str, bytes, bytearray)):
        return size + len(obj)
    if isinstance(obj, (int, float, bool, type(None))):
        return size
    if isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(_estimate_size(item, seen) for item in obj)
        return size
    if isinstance(obj, dict):
        size += sum(_estimate_size(k, seen) + _estimate_size(v, seen) for k, v in obj.items())
        return size
    if hasattr(obj, "__dict__"):
        try:
            size += _estimate_size(obj.__dict__, seen)
        except Exception:
            pass
    if hasattr(obj, "__slots__"):
        try:
            for slot in obj.__slots__:
                size += _estimate_size(getattr(obj, slot, None), seen)
        except Exception:
            pass
    return size


_BASE_SIZE = {
    int: 28,
    float: 24,
    bool: 28,
    type(None): 16,
    str: 49,
    bytes: 37,
    list: 56,
    tuple: 48,
    dict: 64,
    set: 56,
    frozenset: 56,
}
