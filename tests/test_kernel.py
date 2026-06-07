"""
Tests unitaires pour le Kernel asyncio.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from ciel.core.kernel import Kernel, KernelConfig, KernelState, Tick, DEFAULT_TICK_INTERVAL_MS
from ciel.core.identity import bootstrap as bootstrap_identity, exists, load as load_identity


class TestKernelConfig:
    def test_default_config(self) -> None:
        c = KernelConfig()
        assert c.tick_interval_ms == DEFAULT_TICK_INTERVAL_MS
        assert c.max_ticks is None
        assert c.name == "ciel-kernel"

    def test_custom_config(self) -> None:
        c = KernelConfig(tick_interval_ms=100, max_ticks=42, name="test")
        assert c.tick_interval_ms == 100
        assert c.max_ticks == 42
        assert c.name == "test"


class TestKernelState:
    def test_states_exist(self) -> None:
        for s in ("IDLE", "RUNNING", "PAUSED", "STOPPING", "STOPPED"):
            assert KernelState(s) is not None

    def test_state_values(self) -> None:
        assert KernelState.IDLE.value == "IDLE"
        assert KernelState.RUNNING.value == "RUNNING"


class TestTickDataclass:
    def test_tick_creation(self) -> None:
        t = Tick(
            number=1,
            uptime_s=0.5,
            timestamp_ms=1718000000000,
            state=KernelState.RUNNING,
            metrics={"ticks_total": 1.0},
        )
        assert t.number == 1
        assert t.uptime_s == 0.5
        assert t.state == KernelState.RUNNING

    def test_tick_to_dict(self) -> None:
        t = Tick(number=2, uptime_s=1.0, timestamp_ms=0, state=KernelState.RUNNING)
        d = t.to_dict()
        assert d["number"] == 2
        assert d["state"] == "RUNNING"


class TestKernelSync:
    def test_kernel_creates_identity(self, identity_dir) -> None:
        assert not exists(identity_dir)
        k = Kernel(root=Path("."), identity_dir=identity_dir)
        asyncio.run(k.start())
        try:
            assert exists(identity_dir)
            assert k.identity is not None
        finally:
            asyncio.run(k.stop())

    def test_kernel_reuses_existing_identity(self, identity_dir) -> None:
        i1 = bootstrap_identity(identity_dir)
        k = Kernel(root=Path("."), identity_dir=identity_dir)
        asyncio.run(k.start())
        try:
            assert k.identity is not None
            assert k.identity.uuid == i1.uuid
        finally:
            asyncio.run(k.stop())

    def test_kernel_health(self, identity_dir) -> None:
        k = Kernel(root=Path("."), identity_dir=identity_dir)
        asyncio.run(k.start())
        try:
            h = k.health()
            assert h["state"] == "RUNNING"
            assert "metrics" in h
            assert "identity_uuid" in h
        finally:
            asyncio.run(k.stop())

    def test_kernel_pause_resume(self, identity_dir) -> None:
        k = Kernel(root=Path("."), identity_dir=identity_dir)
        asyncio.run(k.start())
        try:
            assert k.state == KernelState.RUNNING
            k.pause()
            assert k.state == KernelState.PAUSED
            k.resume()
            assert k.state == KernelState.RUNNING
        finally:
            asyncio.run(k.stop())


class TestKernelAsync:
    def test_run_produces_ticks(self, identity_dir) -> None:
        async def go() -> None:
            k = Kernel(
                root=Path("."),
                identity_dir=identity_dir,
                config=KernelConfig(tick_interval_ms=20),
            )
            async with k:
                ticks = []
                async for tick in k.run(duration_s=0.3):
                    ticks.append(tick)
                assert len(ticks) >= 5  # au moins quelques ticks en 300ms
                assert all(t.state == KernelState.RUNNING for t in ticks)
                # Numéro de tick monotonement croissant
                for i in range(1, len(ticks)):
                    assert ticks[i].number == ticks[i - 1].number + 1

        asyncio.run(go())

    def test_run_respects_duration(self, identity_dir) -> None:
        async def go() -> None:
            k = Kernel(
                root=Path("."),
                identity_dir=identity_dir,
                config=KernelConfig(tick_interval_ms=50),
            )
            async with k:
                start = time.monotonic()
                async for _ in k.run(duration_s=0.2):
                    pass
                elapsed = time.monotonic() - start
                assert 0.15 < elapsed < 0.5  # pas trop court, pas trop long

        asyncio.run(go())

    def test_max_ticks(self, identity_dir) -> None:
        async def go() -> None:
            k = Kernel(
                root=Path("."),
                identity_dir=identity_dir,
                config=KernelConfig(tick_interval_ms=10, max_ticks=5),
            )
            async with k:
                count = 0
                async for _ in k.run():
                    count += 1
                assert count == 5

        asyncio.run(go())

    def test_drift_measurement(self, identity_dir) -> None:
        async def go() -> None:
            k = Kernel(
                root=Path("."),
                identity_dir=identity_dir,
                config=KernelConfig(tick_interval_ms=20),
            )
            async with k:
                async for _ in k.run(duration_s=0.2):
                    pass
                metrics = k.metrics
                hist = metrics.get_histogram("kernel_tick_drift_ms")
                assert hist.count >= 5
                p99 = hist.quantile(0.99)
                assert p99 is not None
                # Drift doit rester raisonnable (< 100ms)
                assert p99 < 100, f"drift p99 trop élevé: {p99}ms"

        asyncio.run(go())

    def test_metrics_after_run(self, identity_dir) -> None:
        async def go() -> None:
            k = Kernel(
                root=Path("."),
                identity_dir=identity_dir,
                config=KernelConfig(tick_interval_ms=20),
            )
            async with k:
                async for _ in k.run(duration_s=0.1):
                    pass
            snap = k.metrics.snapshot()
            assert snap["kernel_ticks_total"] >= 1
            assert "kernel_state" in snap
            assert "kernel_uptime_s" in snap

        asyncio.run(go())

    def test_stop_event_interrupts_run(self, identity_dir) -> None:
        async def go() -> None:
            k = Kernel(
                root=Path("."),
                identity_dir=identity_dir,
                config=KernelConfig(tick_interval_ms=20),
            )
            await k.start()
            task = asyncio.create_task(_collect_ticks(k, 5))
            await asyncio.sleep(0.05)
            await k.stop()
            ticks = await task
            assert len(ticks) <= 10  # interrompu tôt
            assert k.state == KernelState.STOPPED

        asyncio.run(go())


async def _collect_ticks(k: Kernel, n: int) -> list[Tick]:
    out = []
    async for tick in k.run():
        out.append(tick)
        if len(out) >= n:
            break
    return out
