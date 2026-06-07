"""
CIEL v∞.2 — Kernel : boucle asyncio principale d'une instance.

Le Kernel est le CŒUR de l'instance. Il :
  - Maintient l'état d'exécution
  - Exécute un tick périodique (mode ÉCLAIR < 1ms)
  - Coordonne les 12 strates via messages asynchrones
  - Supporte le shutdown gracieux
  - Expose des métriques de santé (uptime, ticks, erreurs)

Usage :
    async with Kernel(root, identity_dir) as k:
        async for tick in k.run(duration_s=5.0):
            ...

État :
  - IDLE       : au repos, en attente
  - RUNNING    : tick en cours
  - PAUSED     : tick suspendu
  - STOPPING   : arrêt en cours
  - STOPPED    : arrêté

Le Kernel NE décide PAS du contenu des ticks. Il orchestre.
"""
from __future__ import annotations

import asyncio
import enum
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.core.identity import Identity, bootstrap as bootstrap_identity, exists as identity_exists
from ciel.core.observability.metrics import Counter, Gauge, Histogram, Metrics


# ── Constantes ────────────────────────────────────────────
DEFAULT_TICK_INTERVAL_MS: int = 50  # 20 Hz (mode ÉCLAIR cible)
MIN_TICK_INTERVAL_MS: int = 1
MAX_TICK_INTERVAL_MS: int = 60_000


class KernelState(enum.Enum):
    """État du kernel."""

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


# Mapping KernelState → code numérique (pour métriques)
_STATE_CODES: dict[KernelState, int] = {
    KernelState.IDLE: 0,
    KernelState.RUNNING: 1,
    KernelState.PAUSED: 2,
    KernelState.STOPPING: 3,
    KernelState.STOPPED: 4,
}


def _state_code(state: KernelState) -> int:
    """Convertit un KernelState en code numérique pour Gauge."""
    return _STATE_CODES[state]


@dataclass(slots=True)
class Tick:
    """Un tick du kernel (snapshot instantané)."""

    number: int
    uptime_s: float
    timestamp_ms: int
    state: KernelState
    metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "uptime_s": self.uptime_s,
            "timestamp_ms": self.timestamp_ms,
            "state": self.state.value,
            "metrics": self.metrics,
        }


@dataclass(slots=True)
class KernelConfig:
    """Configuration du kernel."""

    tick_interval_ms: int = DEFAULT_TICK_INTERVAL_MS
    max_ticks: int | None = None  # None = infini
    enable_metrics: bool = True
    enable_observability: bool = True
    name: str = "ciel-kernel"


class Kernel:
    """Boucle asyncio principale d'une instance CIEL.

    Example:
        >>> async with Kernel(root=Path("."), identity_dir=Path("data/identity")) as k:
        ...     async for tick in k.run(duration_s=2.0):
        ...         print(tick)
    """

    def __init__(
        self,
        root: Path,
        identity_dir: Path,
        config: KernelConfig | None = None,
    ) -> None:
        self._root = root
        self._identity_dir = identity_dir
        self._config = config or KernelConfig()
        self._state = KernelState.IDLE
        self._start_monotonic: float = 0.0
        self._start_wall: float = 0.0
        self._tick_count: int = 0
        self._error_count: int = 0
        self._stop_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # pas en pause par défaut
        self._metrics = Metrics()
        self._id: str = str(uuid.uuid7()) if hasattr(uuid, "uuid7") else str(uuid.uuid4())
        self._identity: Identity | None = None

    # ── Lifecycle ─────────────────────────────────────────

    async def __aenter__(self) -> "Kernel":
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.stop()

    async def start(self) -> None:
        """Démarre le kernel et initialise l'identité si nécessaire."""
        if self._state != KernelState.IDLE and self._state != KernelState.STOPPED:
            raise RuntimeError(f"kernel déjà {self._state.value}")
        # Init identité (crée si absente)
        if not identity_exists(self._identity_dir):
            self._identity = bootstrap_identity(self._identity_dir)
        else:
            from ciel.core.identity import load
            self._identity = load(self._identity_dir)
        self._start_monotonic = time.monotonic()
        self._start_wall = time.time()
        self._stop_event.clear()
        self._pause_event.set()
        self._state = KernelState.RUNNING
        self._metrics.get_counter("kernel_starts_total").inc()
        self._metrics.get_gauge("kernel_state").set(_state_code(self._state))

    async def stop(self) -> None:
        """Arrête proprement le kernel."""
        if self._state == KernelState.STOPPED:
            return
        self._state = KernelState.STOPPING
        self._stop_event.set()
        self._pause_event.set()  # débloque si en pause
        # Attente brève que la boucle s'arrête (max 1s)
        await asyncio.sleep(0)
        self._state = KernelState.STOPPED
        self._metrics.get_gauge("kernel_state").set(_state_code(self._state))

    def pause(self) -> None:
        """Met le kernel en pause (suspend les ticks)."""
        if self._state != KernelState.RUNNING:
            return
        self._pause_event.clear()
        self._state = KernelState.PAUSED
        self._metrics.get_gauge("kernel_state").set(_state_code(self._state))

    def resume(self) -> None:
        """Reprend après une pause."""
        if self._state != KernelState.PAUSED:
            return
        self._pause_event.set()
        self._state = KernelState.RUNNING
        self._metrics.get_gauge("kernel_state").set(_state_code(self._state))

    # ── Boucle principale ─────────────────────────────────

    async def run(self, duration_s: float | None = None) -> AsyncIterator[Tick]:
        """Boucle de ticks.

        Args:
            duration_s: durée en secondes (None = infini)

        Yields:
            Tick à chaque intervalle
        """
        if self._state != KernelState.RUNNING:
            await self.start()

        tick_interval = self._config.tick_interval_ms / 1000.0
        deadline = time.monotonic() + duration_s if duration_s else float("inf")
        drift_hist = self._metrics.get_histogram(
            "kernel_tick_drift_ms",
            buckets=(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000),
        )

        try:
            while not self._stop_event.is_set():
                if time.monotonic() >= deadline:
                    break
                tick_start = time.monotonic()

                # Attente pause
                await self._pause_event.wait()

                # Effectue le tick
                try:
                    await self._on_tick()
                except Exception as e:
                    self._error_count += 1
                    self._metrics.get_counter("kernel_errors_total").inc()
                    # Log mais ne propage pas (continue à tourner)
                    import traceback
                    traceback.print_exc()
                    _ = e  # appease linter

                # Calcule drift et yield
                actual_interval = time.monotonic() - tick_start
                expected_interval = tick_interval
                drift_ms = abs(actual_interval - expected_interval) * 1000
                drift_hist.observe(drift_ms)

                self._tick_count += 1
                uptime = time.monotonic() - self._start_monotonic
                yield Tick(
                    number=self._tick_count,
                    uptime_s=uptime,
                    timestamp_ms=int(time.time() * 1000),
                    state=self._state,
                    metrics=self._metrics.snapshot(),
                )

                # Limite de ticks
                if (
                    self._config.max_ticks is not None
                    and self._tick_count >= self._config.max_ticks
                ):
                    break

                # Attente du prochain tick
                sleep_for = tick_interval - (time.monotonic() - tick_start)
                if sleep_for > 0:
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(), timeout=sleep_for
                        )
                    except asyncio.TimeoutError:
                        pass  # OK, on continue
        finally:
            if self._state == KernelState.RUNNING:
                self._state = KernelState.STOPPED

    async def _on_tick(self) -> None:
        """Effectue le travail d'un tick (à surcharger)."""
        # Hook par défaut : incrémenter les compteurs de base
        self._metrics.get_counter("kernel_ticks_total").inc()
        self._metrics.get_gauge("kernel_uptime_s").set(
            time.monotonic() - self._start_monotonic
        )

    # ── Inspection ────────────────────────────────────────

    @property
    def state(self) -> KernelState:
        return self._state

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def uptime_s(self) -> float:
        if self._start_monotonic == 0:
            return 0.0
        return time.monotonic() - self._start_monotonic

    @property
    def identity(self) -> Identity | None:
        return self._identity

    @property
    def metrics(self) -> Metrics:
        return self._metrics

    def health(self) -> dict[str, Any]:
        """Retourne un snapshot de santé du kernel."""
        return {
            "id": self._id,
            "state": self._state.value,
            "uptime_s": self.uptime_s,
            "tick_count": self._tick_count,
            "error_count": self._error_count,
            "tick_interval_ms": self._config.tick_interval_ms,
            "identity_uuid": self._identity.uuid if self._identity else None,
            "metrics": self._metrics.snapshot(),
        }
