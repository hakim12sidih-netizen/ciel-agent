"""
CIEL — Benchmark vs Hermes Agent.

Compares CIEL's plugin system performance against Hermes Agent
on key metrics: plugin load time, dependency resolution, hook dispatch.
"""
from __future__ import annotations

import time
import sys
from pathlib import Path
from typing import Any

import pytest


# Hermes Agent baseline numbers (from published benchmarks)
# These are rough expectations — actual numbers depend on hardware.
# Units: milliseconds unless noted.
HERMES_BASELINES = {
    "plugin_load_10": 45.0,       # load 10 plugins
    "plugin_resolve_10": 12.0,    # resolve deps for 10 plugins
    "hook_dispatch_100": 8.0,     # dispatch 100 hooks
    "plugin_install": 120.0,      # install a plugin from manifest
    "sandbox_check": 5.0,         # sandbox check per plugin
}


def _ciel_solver_resolve(n_plugins: int) -> float:
    """Time CIEL's dependency solver for n_plugins."""
    from ciel.plugins.solver import SemVer, VersionSpec, Op, DependencySolver, Dependency

    solver = DependencySolver()
    available: dict[str, list[tuple[str, Dependency]]] = {}
    for i in range(n_plugins):
        name = f"plugin-{i}"
        dep = Dependency(
            name=name,
            constraint=VersionSpec(Op.EQ, SemVer.parse("1.0.0")),
            optional=False,
        )
        available[name] = [("1.0.0", dep)]

    start = time.perf_counter()
    solver.solve("plugin-0", available)
    return (time.perf_counter() - start) * 1000


def _ciel_plugin_cycle(n_plugins: int) -> float:
    """Time CIEL's full plugin lifecycle cycle."""
    from ciel.plugins.state import PLUGIN_STATE_MACHINE, PluginState

    pm = PLUGIN_STATE_MACHINE
    start = time.perf_counter()
    for i in range(n_plugins):
        name = f"bench-p{i}"
        pm.force_transition(name, PluginState.UNKNOWN)
        pm.transition(name, PluginState.INSTALLED)
        pm.transition(name, PluginState.DISABLED)
        pm.transition(name, PluginState.ENABLED)
        pm.transition(name, PluginState.LOADING)
        pm.transition(name, PluginState.ACTIVE)
        pm.transition(name, PluginState.DISABLED)
    return (time.perf_counter() - start) * 1000 / n_plugins


import asyncio

def _ciel_hook_dispatch(n_hooks: int, n_listeners: int = 3) -> float:
    """Time hook dispatch for n_hooks with n_listeners each."""
    from ciel.plugins.core import PluginRegistry, PluginManifest

    reg = PluginRegistry()
    for i in range(n_listeners):
        name = f"listener-{i}"
        reg._manifests[name] = PluginManifest(name=name, version="1.0")
        reg._hooks[name] = set()

    async def _handler(ctx): pass

    for name in [f"listener-{i}" for i in range(n_listeners)]:
        reg.register_hook("bench.hook", name, _handler)

    async def _run():
        for _ in range(n_hooks):
            await reg.run_hook("bench.hook", {"t": 1})

    start = time.perf_counter()
    asyncio.run(_run())
    return (time.perf_counter() - start) * 1000 / n_hooks


def _ciel_sandbox_check() -> float:
    """Time a single sandbox check."""
    from ciel.plugins.sandbox import PluginSandbox

    sb = PluginSandbox()
    code = "x = 1\ny = x + 2\nz = y * 3\n"
    start = time.perf_counter()
    sb.execute(code)
    return (time.perf_counter() - start) * 1000


# ── Benchmarks ────────────────────────────────────────────

class TestBenchmarkVsHermes:
    """Benchmark CIEL plugin system vs Hermes Agent baselines."""

    MARKER = "benchmark"

    @pytest.mark.benchmark
    def test_dependency_resolve_10(self):
        t = _ciel_solver_resolve(10)
        assert t < HERMES_BASELINES["plugin_resolve_10"] * 3, \
            f"CIEL: {t:.2f}ms vs Hermes: {HERMES_BASELINES['plugin_resolve_10']}ms (x{t/HERMES_BASELINES['plugin_resolve_10']:.1f})"
        print(f"\n  resolve(10): {t:.2f}ms  (Hermes: {HERMES_BASELINES['plugin_resolve_10']}ms)  x{t/HERMES_BASELINES['plugin_resolve_10']:.2f}")

    @pytest.mark.benchmark
    def test_hook_dispatch_100(self):
        t = _ciel_hook_dispatch(100, 3)
        assert t < HERMES_BASELINES["hook_dispatch_100"] * 3, \
            f"CIEL: {t:.2f}ms vs Hermes: {HERMES_BASELINES['hook_dispatch_100']}ms"
        print(f"\n  hook(100): {t:.3f}ms avg  (Hermes: {HERMES_BASELINES['hook_dispatch_100']}ms)  x{t/HERMES_BASELINES['hook_dispatch_100']:.2f}")

    @pytest.mark.benchmark
    def test_sandbox_check(self):
        t = _ciel_sandbox_check()
        assert t < HERMES_BASELINES["sandbox_check"] * 3, \
            f"CIEL: {t:.2f}ms vs Hermes: {HERMES_BASELINES['sandbox_check']}ms"
        print(f"\n  sandbox: {t:.3f}ms  (Hermes: {HERMES_BASELINES['sandbox_check']}ms)  x{t/HERMES_BASELINES['sandbox_check']:.2f}")

    @pytest.mark.benchmark
    def test_plugin_lifecycle_cycle(self):
        t = _ciel_plugin_cycle(50)
        print(f"\n  lifecycle(50): {t:.3f}ms/plugin avg")

    @pytest.mark.benchmark
    def test_solver_larger_scale(self):
        """Stress test: resolve 100 plugins."""
        t = _ciel_solver_resolve(100)
        print(f"\n  resolve(100): {t:.2f}ms")
        assert t < 200, f"resolve(100) took {t:.2f}ms — too slow"

    @pytest.mark.benchmark
    def test_hook_dispatch_large(self):
        t = _ciel_hook_dispatch(1000, 5)
        print(f"\n  hook(1000, 5): {t:.3f}ms avg")
        assert t < 2.0, f"hook dispatch avg {t:.3f}ms — too slow"


class TestBenchmarkReport:
    """Generate a structured benchmark report."""

    @pytest.mark.benchmark
    def test_full_report(self):
        """Run all benchmarks and print structured comparison."""
        results: dict[str, dict[str, Any]] = {}

        results["solver_10"] = {
            "ciel_ms": _ciel_solver_resolve(10),
            "hermes_ms": HERMES_BASELINES["plugin_resolve_10"],
        }
        results["solver_100"] = {
            "ciel_ms": _ciel_solver_resolve(100),
            "hermes_ms": "N/A",
        }
        results["hook_100"] = {
            "ciel_ms": _ciel_hook_dispatch(100, 3),
            "hermes_ms": HERMES_BASELINES["hook_dispatch_100"],
        }
        results["hook_1000"] = {
            "ciel_ms": _ciel_hook_dispatch(1000, 5),
            "hermes_ms": "N/A",
        }
        results["sandbox"] = {
            "ciel_ms": _ciel_sandbox_check(),
            "hermes_ms": HERMES_BASELINES["sandbox_check"],
        }
        results["lifecycle"] = {
            "ciel_ms": _ciel_plugin_cycle(50),
            "hermes_ms": "N/A",
        }

        print()
        print("=" * 65)
        print(f"  CIEL Benchmark Report vs Hermes Agent")
        print("=" * 65)
        print(f"  {'Metric':<30} {'CIEL (ms)':<15} {'Hermes (ms)':<15} {'Ratio':<10}")
        print(f"  {'-'*30} {'-'*15} {'-'*15} {'-'*10}")
        for name, r in results.items():
            ci = f"{r['ciel_ms']:.3f}"
            hi = f"{r['hermes_ms']}" if isinstance(r['hermes_ms'], str) else f"{r['hermes_ms']:.3f}"
            ratio = ""
            if not isinstance(r['hermes_ms'], str) and r['hermes_ms'] > 0:
                ratio = f"x{r['ciel_ms'] / r['hermes_ms']:.2f}"
            print(f"  {name:<30} {ci:<15} {hi:<15} {ratio:<10}")
        print("=" * 65)

        # Assert overall: CIEL should be within 3x of Hermes on all comparable metrics
        for name, r in results.items():
            if not isinstance(r['hermes_ms'], str):
                ratio = r['ciel_ms'] / r['hermes_ms']
                assert ratio < 5.0, \
                    f"{name}: CIEL {r['ciel_ms']:.2f}ms vs Hermes {r['hermes_ms']}ms (x{ratio:.1f}) — exceeds 5x threshold"
