"""
CIEL — Performance profiling & timing utilities.

Modules :
  - Timer / @timed decorator pour mesurer l'exécution
  - Profiler pour benchmarker modules, fonctions, classes
  - CLI : ciel perf profile

Usage :
    with Timer() as t:
        do_work()
    print(f"Pris {t.ms:.1f} ms")

    @timed
    def slow_func(): ...

    p = Profiler()
    p.run("ciel.skills.marketplace", iterations=100)
"""
from __future__ import annotations

import time
import functools
import logging
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

log = logging.getLogger("ciel.perf")
_timings: dict[str, list[float]] = {}


class Timer:
    """Context manager de chronométrage haute résolution.

    >>> with Timer() as t:
    ...     time.sleep(0.1)
    >>> assert 90 < t.ms < 500
    """

    __slots__ = ("_start", "_elapsed")

    def __init__(self) -> None:
        self._start: float = 0.0
        self._elapsed: float = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self._elapsed = time.perf_counter() - self._start

    @property
    def elapsed(self) -> float:
        return self._elapsed

    @property
    def ms(self) -> float:
        return self._elapsed * 1000

    @property
    def us(self) -> float:
        return self._elapsed * 1_000_000


def _record(key: str, elapsed: float) -> None:
    _timings.setdefault(key, []).append(elapsed)


def timed(func: F = None, *, key: str | None = None) -> F | Callable[[F], F]:
    """Decorator qui chronomètre et enregistre le temps d'exécution.

    Peut s'utiliser avec ou sans parenthèses :

        @timed
        def foo(): ...

        @timed(key="custom_key")
        def bar(): ...
    """
    def decorator(fn: F) -> F:
        label = key or f"{fn.__module__}.{fn.__qualname__}"

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                _record(label, elapsed)

        return wrapper  # type: ignore

    return decorator if func is None else decorator(func)


def get_timings() -> dict[str, dict[str, float]]:
    """Retourne les statistiques agrégées de tous les chronos."""
    stats: dict[str, dict[str, float]] = {}
    for key, values in _timings.items():
        n = len(values)
        total = sum(values)
        avg = total / n
        sorted_v = sorted(values)
        p50 = sorted_v[int(n * 0.50)]
        p95 = sorted_v[int(n * 0.95)]
        p99 = sorted_v[int(n * 0.99)]
        stats[key] = {
            "count": n,
            "total_ms": round(total * 1000, 2),
            "avg_ms": round(avg * 1000, 2),
            "min_ms": round(min(values) * 1000, 2),
            "max_ms": round(max(values) * 1000, 2),
            "p50_ms": round(p50 * 1000, 2),
            "p95_ms": round(p95 * 1000, 2),
            "p99_ms": round(p99 * 1000, 2),
        }
    return stats


def reset_timings() -> None:
    _timings.clear()


class Profiler:
    """Profileur simple pour benchmarker des modules et fonctions.

    Exécute une fonction N fois, collecte les statistiques.
    """

    def __init__(self, warmup: int = 3):
        self.warmup = warmup
        self.results: dict[str, dict[str, float]] = {}

    def run(self, fn: Callable, *args: Any,
            iterations: int = 100, label: str | None = None,
            **kwargs: Any) -> dict[str, float]:
        """Exécute fn() N fois et retourne les stats."""
        key = label or f"{fn.__module__}.{fn.__qualname__}"

        # warmup
        for _ in range(self.warmup):
            fn(*args, **kwargs)

        # measure
        times: list[float] = []
        for _ in range(iterations):
            start = time.perf_counter()
            fn(*args, **kwargs)
            times.append(time.perf_counter() - start)

        sorted_t = sorted(times)
        n = len(times)
        total = sum(times)
        avg = total / n

        stats = {
            "count": n,
            "total_ms": round(total * 1000, 2),
            "avg_ms": round(avg * 1000, 2),
            "min_ms": round(min(times) * 1000, 2),
            "max_ms": round(max(times) * 1000, 2),
            "p50_ms": round(sorted_t[int(n * 0.50)] * 1000, 2),
            "p95_ms": round(sorted_t[int(n * 0.95)] * 1000, 2),
            "p99_ms": round(sorted_t[int(n * 0.99)] * 1000, 2),
        }
        self.results[key] = stats
        return stats

    def run_module(self, module_name: str, iterations: int = 100) -> dict[str, dict[str, float]]:
        """Profile toutes les fonctions d'un module."""
        import importlib
        import inspect

        mod = importlib.import_module(module_name)
        results: dict[str, dict[str, float]] = {}
        for name, obj in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("_"):
                continue
            try:
                sig = inspect.signature(obj)
                args = []
                for p in sig.parameters.values():
                    if p.default is inspect.Parameter.empty and p.name != "self":
                        args.append(None)  # placeholder
                stats = self.run(obj, *args, iterations=max(iterations // 10, 5),
                                 label=f"{module_name}.{name}")
                results[f"{module_name}.{name}"] = stats
            except Exception:
                pass
        return results

    def summary(self) -> list[dict[str, Any]]:
        """Retourne les résultats triés par avg_ms décroissant."""
        return sorted(
            [{"key": k, **v} for k, v in self.results.items()],
            key=lambda r: -r["avg_ms"],
        )
