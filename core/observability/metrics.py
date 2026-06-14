"""
CIEL v∞.2 — Observability : métriques (Counter/Gauge/Histogram) + health checks.

Inspiré de Prometheus mais en Python pur, sans dépendance externe.

Types :
  - Counter  : monotonement croissant (ex: ticks_total, errors_total)
  - Gauge    : valeur instantanée (ex: uptime_s, queue_depth)
  - Histogram: distribution (ex: latence_ms, drift_ms)

Persistance :
  - In-memory par défaut
  - Snapshot JSON sérialisable via snapshot()

Health :
  - HealthCheck dataclass pour checks systématiques
  - run_all() agrège en un rapport
"""
from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import RLock
from typing import Any


# ═══════════════════════════════════════════════════════════
# COUNTER
# ═══════════════════════════════════════════════════════════

def _validate_metric_name(name: str) -> None:
    """Valide qu'un nom de métrique suit [a-zA-Z_][a-zA-Z0-9_]*."""
    if not name:
        raise ValueError("nom de métrique vide")
    if not (name[0].isalpha() or name[0] == "_"):
        raise ValueError(f"nom de métrique doit commencer par lettre ou _ : {name!r}")
    for c in name[1:]:
        if not (c.isalnum() or c == "_"):
            raise ValueError(f"nom de métrique contient caractère invalide : {name!r}")


class Counter:
    """Compteur monotonement croissant (thread-safe)."""

    def __init__(self, name: str, help_text: str = "", labels: dict[str, str] | None = None) -> None:
        _validate_metric_name(name)
        self._name = name
        self._help = help_text
        self._labels = labels or {}
        self._value = 0.0
        self._lock = RLock()
        self._created_at = time.time()

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> float:
        with self._lock:
            return self._value

    def inc(self, amount: float = 1.0) -> None:
        if amount < 0:
            raise ValueError(f"Counter ne peut décroitre (amount={amount})")
        with self._lock:
            self._value += amount

    def reset(self) -> None:
        with self._lock:
            self._value = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "counter",
            "name": self._name,
            "help": self._help,
            "labels": self._labels,
            "value": self.value,
        }


# ═══════════════════════════════════════════════════════════
# GAUGE
# ═══════════════════════════════════════════════════════════

class Gauge:
    """Valeur instantanée (peut monter ou descendre)."""

    def __init__(self, name: str, help_text: str = "", labels: dict[str, str] | None = None) -> None:
        _validate_metric_name(name)
        self._name = name
        self._help = help_text
        self._labels = labels or {}
        self._value = 0.0
        self._lock = RLock()
        self._created_at = time.time()

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> float:
        with self._lock:
            return self._value

    def set(self, value: float) -> None:
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"gauge value ne peut être NaN/Inf : {value}")
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0) -> None:
        with self._lock:
            self._value -= amount

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "gauge",
            "name": self._name,
            "help": self._help,
            "labels": self._labels,
            "value": self.value,
        }


# ═══════════════════════════════════════════════════════════
# HISTOGRAM
# ═══════════════════════════════════════════════════════════

class Histogram:
    """Distribution de valeurs (buckets cumulatifs + sum/count)."""

    def __init__(
        self,
        name: str,
        help_text: str = "",
        buckets: tuple[float, ...] = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        labels: dict[str, str] | None = None,
    ) -> None:
        _validate_metric_name(name)
        if not buckets or any(b <= 0 for b in buckets):
            raise ValueError(f"buckets doivent être > 0 et triés")
        sorted_buckets = tuple(sorted(set(buckets)))
        self._name = name
        self._help = help_text
        self._labels = labels or {}
        self._buckets = sorted_buckets
        self._counts = [0] * len(sorted_buckets)
        self._sum = 0.0
        self._count = 0
        self._lock = RLock()

    @property
    def name(self) -> str:
        return self._name

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    @property
    def sum(self) -> float:
        with self._lock:
            return self._sum

    def observe(self, value: float) -> None:
        if math.isnan(value):
            return  # ignore NaN (convention Prometheus)
        with self._lock:
            self._sum += value
            self._count += 1
            for i, b in enumerate(self._buckets):
                if value <= b:
                    self._counts[i] += 1

    def quantile(self, q: float) -> float | None:
        """Estime le quantile q (0..1) par interpolation linéaire.

        Approximation simple, suffisante pour health checks.
        """
        if not 0 < q < 1:
            raise ValueError(f"q doit être entre 0 et 1, reçu {q}")
        with self._lock:
            if self._count == 0:
                return None
            target = q * self._count
            for b, c in zip(self._buckets, self._counts):
                if c >= target:
                    return b
            return self._buckets[-1]

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "type": "histogram",
                "name": self._name,
                "help": self._help,
                "labels": self._labels,
                "buckets": dict(zip(self._buckets, self._counts)),
                "count": self._count,
                "sum": self._sum,
                "p50": self.quantile(0.5),
                "p95": self.quantile(0.95),
                "p99": self.quantile(0.99),
            }


# ═══════════════════════════════════════════════════════════
# METRICS REGISTRY
# ═══════════════════════════════════════════════════════════

class Metrics:
    """Registre central de toutes les métriques d'une instance."""

    def __init__(self) -> None:
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = RLock()

    def get_counter(self, name: str, help_text: str = "") -> Counter:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, help_text)
            return self._counters[name]

    def get_gauge(self, name: str, help_text: str = "") -> Gauge:
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, help_text)
            return self._gauges[name]

    def get_histogram(
        self, name: str, help_text: str = "", buckets: tuple[float, ...] | None = None
    ) -> Histogram:
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(
                    name, help_text, buckets or Histogram.__init__.__defaults__[1]  # type: ignore
                )
            return self._histograms[name]

    def snapshot(self) -> dict[str, float]:
        """Snapshot plat (juste les valeurs) pour export rapide."""
        snap: dict[str, float] = {}
        for c in self._counters.values():
            snap[c.name] = c.value
        for g in self._gauges.values():
            snap[g.name] = g.value
        for h in self._histograms.values():
            snap[f"{h.name}_count"] = float(h.count)
            snap[f"{h.name}_sum"] = h.sum
        return snap

    def full_snapshot(self) -> dict[str, Any]:
        """Snapshot complet avec types et buckets."""
        return {
            "counters": {n: c.to_dict() for n, c in self._counters.items()},
            "gauges": {n: g.to_dict() for n, g in self._gauges.items()},
            "histograms": {n: h.to_dict() for n, h in self._histograms.items()},
        }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


# ═══════════════════════════════════════════════════════════
# HEALTH CHECKS
# ═══════════════════════════════════════════════════════════

@dataclass
class HealthCheckResult:
    """Résultat d'un health check."""

    name: str
    status: str  # "OK", "WARN", "FAIL"
    message: str = ""
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }


HealthCheckFn = Callable[[], HealthCheckResult]


@dataclass
class HealthCheck:
    """Définition d'un health check."""

    name: str
    fn: HealthCheckFn
    category: str = "general"
    description: str = ""


def _ok(name: str, message: str = "", **details: Any) -> HealthCheckResult:
    return HealthCheckResult(name=name, status="OK", message=message, details=details)


def _warn(name: str, message: str = "", **details: Any) -> HealthCheckResult:
    return HealthCheckResult(name=name, status="WARN", message=message, details=details)


def _fail(name: str, message: str = "", **details: Any) -> HealthCheckResult:
    return HealthCheckResult(name=name, status="FAIL", message=message, details=details)


# ═══════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "Metrics",
    "HealthCheck",
    "HealthCheckResult",
    "HealthCheckFn",
    "_ok",
    "_warn",
    "_fail",
]
