"""
CIEL v∞.9 — Tests Phase 2.5 : Solver, Transaction, Middleware, State, Cache,
Testing DSL, Telemetry, Graph, Resource.
"""
from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest

from ciel.plugins.solver import (
    SemVer, VersionSpec, VersionConstraint, Op,
    parse_spec, format_spec, Dependency, DependencySolver,
    SolveConflict, SolveMissing, SolveError,
)
from ciel.plugins.transaction import (
    PluginTransaction, TransactionError, transactional, current_tx,
)
from ciel.plugins.middleware import (
    MiddlewarePipeline, Middleware, MiddlewareError,
    MiddlewareResult, MiddlewareRegistry,
)
from ciel.plugins.state import (
    PluginState, StateMachine, StateTransition,
    StateError, TransitionDenied, Guard,
    PLUGIN_STATE_MACHINE, VALID_TRANSITIONS,
)
from ciel.plugins.cache import (
    BytecodeCache, CacheEntry, CacheStats,
    get_cache, compile_and_cache,
)
from ciel.plugins.testing import (
    PluginTestSuite, TestResult, MockHook, MockPermission,
    assert_sandbox_blocks, assert_lifecycle,
)
from ciel.plugins.telemetry import (
    TelemetryEngine, AuditEntry, get_telemetry,
)
from ciel.plugins.graph import (
    PluginGraph, DependencyGraph, HookGraph,
    ImpactAnalysis, CouplingMetrics,
)
from ciel.plugins.resource import (
    ResourceController, ResourceQuota, ResourceUsage,
    RateLimiter, get_resource_controller,
)
from ciel.plugins.core import PluginBase, PluginManifest
from ciel.plugins.permissions import PermissionDecision


# ═══════════════════════════════════════════════════════════
# SOLVER
# ═══════════════════════════════════════════════════════════

class TestSemVer:
    def test_parse_full(self):
        v = SemVer.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_parse_partial(self):
        v = SemVer.parse("2.0")
        assert v.major == 2
        assert v.minor == 0
        assert v.patch == 0

    def test_parse_prerelease(self):
        v = SemVer.parse("1.0.0-alpha.1")
        assert v.prerelease == "alpha.1"

    def test_parse_build(self):
        v = SemVer.parse("1.0.0+build42")
        assert v.build == "build42"

    def test_parse_invalid_raises(self):
        with pytest.raises(ValueError):
            SemVer.parse("abc")

    def test_comparison_lt(self):
        assert SemVer.parse("1.0.0") < SemVer.parse("2.0.0")
        assert SemVer.parse("1.0.0") < SemVer.parse("1.1.0")
        assert SemVer.parse("1.0.0") < SemVer.parse("1.0.1")
        assert not (SemVer.parse("2.0.0") < SemVer.parse("1.0.0"))

    def test_prerelease_lt_release(self):
        assert SemVer.parse("1.0.0-alpha") < SemVer.parse("1.0.0")

    def test_eq(self):
        assert SemVer.parse("1.0.0") == SemVer.parse("1.0.0")
        assert SemVer.parse("1.0.0") != SemVer.parse("1.0.1")

    def test_str_roundtrip(self):
        for s in ["1.0.0", "2.3.4", "0.1.0-alpha", "1.2.3+build"]:
            assert str(SemVer.parse(s)) == s


class TestVersionSpec:
    def test_eq(self):
        spec = VersionSpec(Op.EQ, SemVer.parse("1.0.0"))
        assert spec.matches(SemVer.parse("1.0.0"))
        assert not spec.matches(SemVer.parse("1.0.1"))

    def test_neq(self):
        spec = VersionSpec(Op.NEQ, SemVer.parse("1.0.0"))
        assert spec.matches(SemVer.parse("2.0.0"))
        assert not spec.matches(SemVer.parse("1.0.0"))

    def test_gt(self):
        spec = VersionSpec(Op.GT, SemVer.parse("1.0.0"))
        assert spec.matches(SemVer.parse("2.0.0"))
        assert not spec.matches(SemVer.parse("1.0.0"))

    def test_gte(self):
        spec = VersionSpec(Op.GTE, SemVer.parse("1.0.0"))
        assert spec.matches(SemVer.parse("1.0.0"))
        assert spec.matches(SemVer.parse("1.0.1"))

    def test_lt(self):
        spec = VersionSpec(Op.LT, SemVer.parse("2.0.0"))
        assert spec.matches(SemVer.parse("1.0.0"))
        assert not spec.matches(SemVer.parse("2.0.0"))

    def test_lte(self):
        spec = VersionSpec(Op.LTE, SemVer.parse("2.0.0"))
        assert spec.matches(SemVer.parse("2.0.0"))
        assert spec.matches(SemVer.parse("1.0.0"))

    def test_wildcard(self):
        spec = VersionSpec(Op.WILDCARD)
        assert spec.matches(SemVer.parse("99.99.99"))
        assert spec.matches(SemVer.parse("0.0.1"))

    def test_tilde(self):
        spec = VersionSpec(Op.TILDE, SemVer.parse("1.2.0"))
        assert spec.matches(SemVer.parse("1.2.3"))
        assert spec.matches(SemVer.parse("1.2.9"))
        assert not spec.matches(SemVer.parse("1.3.0"))
        assert not spec.matches(SemVer.parse("2.0.0"))

    def test_caret_major(self):
        spec = VersionSpec(Op.CARET, SemVer.parse("1.2.3"))
        assert spec.matches(SemVer.parse("1.5.0"))
        assert spec.matches(SemVer.parse("1.9.9"))
        assert not spec.matches(SemVer.parse("2.0.0"))
        assert not spec.matches(SemVer.parse("0.9.0"))

    def test_caret_zero_minor(self):
        spec = VersionSpec(Op.CARET, SemVer.parse("0.1.0"))
        assert spec.matches(SemVer.parse("0.1.5"))
        assert not spec.matches(SemVer.parse("0.2.0"))

    def test_caret_zero_patch(self):
        spec = VersionSpec(Op.CARET, SemVer.parse("0.0.3"))
        assert spec.matches(SemVer.parse("0.0.4"))
        assert not spec.matches(SemVer.parse("0.1.0"))


class TestParseSpec:
    def test_simple_eq(self):
        c = parse_spec("==1.0.0")
        assert c.matches(SemVer.parse("1.0.0"))
        assert not c.matches(SemVer.parse("1.0.1"))

    def test_range(self):
        c = parse_spec(">=1.0, <2.0")
        assert c.matches(SemVer.parse("1.5.0"))
        assert not c.matches(SemVer.parse("2.0.0"))
        assert c.matches(SemVer.parse("1.0.0"))

    def test_tilde_spec(self):
        c = parse_spec("~=1.2.0")
        assert c.matches(SemVer.parse("1.2.3"))
        assert not c.matches(SemVer.parse("1.3.0"))

    def test_caret_spec(self):
        c = parse_spec("^1.2.3")
        assert c.matches(SemVer.parse("1.5.0"))
        assert not c.matches(SemVer.parse("2.0.0"))

    def test_wildcard(self):
        c = parse_spec("*")
        assert c.matches(SemVer.parse("42.0.0"))

    def test_not_equal(self):
        c = parse_spec("!=1.0.0")
        assert c.matches(SemVer.parse("2.0.0"))
        assert not c.matches(SemVer.parse("1.0.0"))

    def test_inequality(self):
        c = parse_spec(">1.0.0")
        assert c.matches(SemVer.parse("1.0.1"))
        assert not c.matches(SemVer.parse("1.0.0"))

    def test_format_spec(self):
        c = parse_spec(">=1.0, <2.0")
        formatted = format_spec(c)
        assert ">=" in formatted
        assert "<" in formatted


class TestDependencySolver:
    def test_solve_simple(self):
        plugins = {
            "base": [("1.0.0", {"name": "base", "version": "1.0.0", "deps": []})],
        }
        solver = DependencySolver()
        result = solver.solve("base", plugins)
        assert "base" in result

    def test_solve_chain(self):
        plugins = {
            "a": [("1.0.0", {"name": "a", "version": "1.0.0", "deps": ["b"]})],
            "b": [("1.0.0", {"name": "b", "version": "1.0.0", "deps": ["c"]})],
            "c": [("1.0.0", {"name": "c", "version": "1.0.0", "deps": []})],
        }
        solver = DependencySolver()
        result = solver.solve("a", plugins)
        assert all(k in result for k in ["a", "b", "c"])

    def test_solve_prefers_newest(self):
        plugins = {
            "base": [
                ("1.0.0", {"name": "base", "version": "1.0.0", "deps": []}),
                ("2.0.0", {"name": "base", "version": "2.0.0", "deps": []}),
            ],
        }
        solver = DependencySolver()
        result = solver.solve("base", plugins)
        assert result["base"]["version"] == "2.0.0"

    def test_solve_missing_raises(self):
        plugins = {
            "a": [("1.0.0", {"name": "a", "version": "1.0.0", "deps": ["missing"]})],
        }
        solver = DependencySolver()
        with pytest.raises(SolveMissing):
            solver.solve("a", plugins)

    def test_solve_matching_constraint(self):
        plugins = {
            "base": [
                ("1.0.0", {"name": "base", "version": "1.0.0", "deps": []}),
                ("2.0.0", {"name": "base", "version": "2.0.0", "deps": []}),
                ("3.0.0", {"name": "base", "version": "3.0.0", "deps": []}),
            ],
        }
        constraint = parse_spec(">=1.0, <3.0")
        solver = DependencySolver()
        result = solver.solve("base", plugins, constraint)
        assert SemVer.parse(result["base"]["version"]) < SemVer.parse("3.0.0")

    def test_find_best(self):
        candidates = [
            ("1.0.0", {"name": "x", "deps": []}),
            ("2.0.0", {"name": "x", "deps": []}),
            ("3.0.0", {"name": "x", "deps": []}),
        ]
        solver = DependencySolver()
        best = solver.find_best(candidates, parse_spec(">=1.0, <3.0"))
        assert best is not None
        assert best[0] == "2.0.0"


# ═══════════════════════════════════════════════════════════
# TRANSACTION
# ═══════════════════════════════════════════════════════════

class MockRegistry:
    def __init__(self):
        self._manifests = {"p1": "v1.0", "p2": "v2.0"}
        self._plugins = {"p1": "loaded", "p2": "loaded"}
        self._hooks = {"hook1": [("p1", 0, lambda: None)]}
        self._events = {"evt1": [("p2", 0, lambda: None)]}


class TestPluginTransaction:
    def test_begin_then_commit(self):
        import asyncio
        reg = MockRegistry()
        tx = PluginTransaction(reg, "test-tx")
        tx.begin()
        result = asyncio.run(tx.commit())
        assert result["status"] == "committed"

    def test_rollback_restores_state(self):
        import asyncio
        reg = MockRegistry()
        original_manifests = dict(reg._manifests)

        tx = PluginTransaction(reg, "rollback-test")
        tx.begin()
        reg._manifests["new"] = "v3.0"
        asyncio.run(tx.rollback())

        assert "new" not in reg._manifests
        assert reg._manifests == original_manifests

    def test_double_commit_raises(self):
        import asyncio
        reg = MockRegistry()
        tx = PluginTransaction(reg)
        tx.begin()
        asyncio.run(tx.commit())
        with pytest.raises(TransactionError):
            asyncio.run(tx.commit())

    def test_rollback_after_commit_raises(self):
        import asyncio
        reg = MockRegistry()
        tx = PluginTransaction(reg)
        tx.begin()
        asyncio.run(tx.commit())
        with pytest.raises(TransactionError):
            asyncio.run(tx.rollback())

    def test_log_operation(self):
        import asyncio
        reg = MockRegistry()
        tx = PluginTransaction(reg)
        tx.begin()
        tx.log_operation("install", name="test-plugin")
        asyncio.run(tx.commit())
        assert len(tx._pending) == 1

    def test_duration_ms(self):
        reg = MockRegistry()
        tx = PluginTransaction(reg)
        tx.begin()
        time.sleep(0.001)
        assert tx.duration_ms > 0

    def test_current_tx(self):
        import asyncio
        from ciel.plugins.transaction import _thread_local
        _thread_local.current_tx = None
        reg = MockRegistry()
        tx = PluginTransaction(reg)
        tx.begin()
        assert current_tx() is tx
        asyncio.run(tx.commit())
        assert current_tx() is None


class TestTransactionalDecorator:
    def test_async_context_manager(self):
        reg = MockRegistry()
        import asyncio
        async def test():
            async with transactional(reg, "test-ctx") as tx:
                assert current_tx() is tx
                tx.log_operation("test", key="value")
            return True
        assert asyncio.run(test())

    def test_auto_rollback_on_error(self):
        import asyncio
        reg = MockRegistry()
        orig_keys = set(reg._manifests.keys())
        async def test():
            try:
                async with transactional(reg, "failing") as tx:
                    tx.log_operation("modify", key="value")
                    reg._manifests["new"] = "v3.0"
                    raise ValueError("boom")
            except ValueError:
                pass
        asyncio.run(test())
        assert set(reg._manifests.keys()) == orig_keys


# ═══════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════

class TestMiddlewarePipeline:
    def test_register_and_chain(self):
        pipeline = MiddlewarePipeline()
        calls = []

        class TestMW(Middleware):
            async def before(self, ctx):
                calls.append("before")
                return ctx

            async def after(self, ctx, result):
                calls.append("after")
                return result

        mw = TestMW(name="test-mw", plugin="test", hook_name="test.hook", priority=0)
        pipeline.register(mw, mw)

        async def my_hook(ctx):
            calls.append("hook")
            return "done"

        wrapped = pipeline.wrap_hook("test.hook", my_hook)
        import asyncio
        result = asyncio.run(wrapped({"key": "val"}))
        assert result == "done"
        assert calls == ["before", "hook", "after"]

    def test_around_wraps(self):
        pipeline = MiddlewarePipeline()
        calls = []

        class AroundMW(Middleware):
            async def around(self, ctx, next_hook):
                calls.append("around_start")
                result = await next_hook(ctx)
                calls.append("around_end")
                return result.upper()

        mw = AroundMW(name="around", plugin="test", hook_name="test.hook", priority=0)
        pipeline.register(mw, mw)

        async def my_hook(ctx):
            calls.append("hook")
            return "hello"

        wrapped = pipeline.wrap_hook("test.hook", my_hook)
        import asyncio
        result = asyncio.run(wrapped({}))
        assert result == "HELLO"
        assert calls == ["around_start", "hook", "around_end"]

    def test_priority_order(self):
        pipeline = MiddlewarePipeline()
        order = []

        class LowMW(Middleware):
            async def before(self, ctx):
                order.append("low")
                return ctx

        class HighMW(Middleware):
            async def before(self, ctx):
                order.append("high")
                return ctx

        pipeline.register(
            LowMW(name="low", plugin="p", hook_name="test", priority=100), LowMW("low", "p", "test", 100))
        pipeline.register(
            HighMW(name="high", plugin="p", hook_name="test", priority=-100), HighMW("high", "p", "test", -100))

        async def hook(ctx):
            order.append("hook")
            return "ok"

        wrapped = pipeline.wrap_hook("test", hook)
        import asyncio
        asyncio.run(wrapped({}))
        assert order == ["high", "low", "hook"]

    def test_on_error_catches(self):
        pipeline = MiddlewarePipeline()

        class ErrorMW(Middleware):
            async def on_error(self, ctx, error):
                return "recovered"

        pipeline.register(
            ErrorMW(name="err", plugin="p", hook_name="test", priority=0),
            ErrorMW("err", "p", "test", 0))

        async def failing_hook(ctx):
            raise ValueError("fail")

        wrapped = pipeline.wrap_hook("test", failing_hook)
        import asyncio
        result = asyncio.run(wrapped({}))
        assert result == "recovered"

    def test_unregister(self):
        pipeline = MiddlewarePipeline()
        mw = Middleware(name="mw", plugin="p", hook_name="test", priority=0)
        pipeline.register(mw, mw)
        assert len(pipeline.list_middlewares()) == 1
        pipeline.unregister("p")
        assert len(pipeline.list_middlewares()) == 0

    def test_stats(self):
        pipeline = MiddlewarePipeline()

        async def hook(ctx):
            return "ok"

        wrapped = pipeline.wrap_hook("perf.test", hook)
        import asyncio
        asyncio.run(wrapped({}))
        asyncio.run(wrapped({}))

        stats = pipeline.get_stats("perf.test")
        assert stats["count"] == 2
        assert stats["avg_ms"] > 0


# ═══════════════════════════════════════════════════════════
# STATE MACHINE
# ═══════════════════════════════════════════════════════════

class TestStateMachine:
    def test_initial_state_unknown(self):
        sm = StateMachine()
        assert sm.get_state("test-plugin") == PluginState.UNKNOWN

    def test_valid_transition(self):
        sm = StateMachine()
        t = sm.transition("p", PluginState.INSTALLED)
        assert t.to_state == PluginState.INSTALLED
        assert sm.get_state("p") == PluginState.INSTALLED
        assert not t.forced
        assert t.from_state == PluginState.UNKNOWN

    def test_invalid_transition_raises(self):
        sm = StateMachine()
        sm.transition("p", PluginState.INSTALLED)
        with pytest.raises(TransitionDenied, match="Invalid"):
            sm.transition("p", PluginState.ACTIVE)

    def test_force_transition_bypasses_guards(self):
        sm = StateMachine()
        sm.add_guard(PluginState.UNKNOWN, PluginState.INSTALLED,
                     Guard("always_fail", lambda p, f, t, c: False, "cannot install"))
        t = sm.force_transition("p", PluginState.INSTALLED, reason="forced")
        assert t.forced
        assert sm.get_state("p") == PluginState.INSTALLED

    def test_guard_blocks_transition(self):
        sm = StateMachine()
        sm.add_guard(PluginState.UNKNOWN, PluginState.INSTALLED,
                     Guard("block", lambda p, f, t, c: False, "blocked"))
        with pytest.raises(TransitionDenied):
            sm.transition("p", PluginState.INSTALLED)

    def test_global_guard(self):
        sm = StateMachine()
        sm.add_global_guard(
            Guard("always_block", lambda p, f, t, c: False, "globally blocked"))
        with pytest.raises(TransitionDenied):
            sm.transition("p", PluginState.INSTALLED)

    def test_on_transition_callback(self):
        sm = StateMachine()
        calls = []
        sm.on_transition(lambda p, t: calls.append((p, t.to_state)))
        sm.transition("p", PluginState.INSTALLED)
        assert ("p", PluginState.INSTALLED) in calls

    def test_history(self):
        sm = StateMachine()
        sm.transition("p", PluginState.INSTALLED, reason="install")
        sm.transition("p", PluginState.DISABLED, reason="disable")
        history = sm.get_history("p")
        assert len(history) == 2
        assert history[0].reason == "install"
        assert history[1].reason == "disable"

    def test_error_state_tracking(self):
        sm = StateMachine()
        sm.transition("p", PluginState.INSTALLED)
        sm.transition("p", PluginState.ERROR, reason="crash")
        stats = sm.get_stats("p")
        assert stats["error_count"] == 1

    def test_reset(self):
        sm = StateMachine()
        sm.transition("p", PluginState.INSTALLED)
        sm.reset("p")
        assert sm.get_state("p") == PluginState.UNKNOWN

    def test_get_all_states(self):
        sm = StateMachine()
        sm.transition("a", PluginState.INSTALLED)
        sm.transition("b", PluginState.INSTALLED)
        sm.transition("b", PluginState.ENABLED)
        sm.transition("b", PluginState.LOADING)
        sm.transition("b", PluginState.ACTIVE)
        all_s = sm.get_all_states()
        assert all_s["a"] == "installed"
        assert all_s["b"] == "active"

    def test_valid_transitions_complete(self):
        for from_state, to_states in VALID_TRANSITIONS.items():
            for to_state in to_states:
                sm = StateMachine()
                if from_state != PluginState.UNKNOWN:
                    sm.force_transition("p", from_state)
                t = sm.transition("p", to_state)
                assert sm.get_state("p") == to_state, f"{from_state} -> {to_state} failed"


# ═══════════════════════════════════════════════════════════
# BYTECODE CACHE
# ═══════════════════════════════════════════════════════════

class TestBytecodeCache:
    def test_put_and_get(self, tmp_path):
        cache = BytecodeCache(tmp_path)
        source = "x = 1 + 1"
        bytecode = compile_and_cache(source, "test", "1.0.0", cache)
        assert len(bytecode) > 0

        cached = cache.get("test", source)
        assert cached is not None
        assert cached == bytecode

    def test_cache_miss(self, tmp_path):
        cache = BytecodeCache(tmp_path)
        result = cache.get("unknown", "nonexistent")
        assert result is None

    def test_invalidate(self, tmp_path):
        cache = BytecodeCache(tmp_path)
        source = "x = 42"
        compile_and_cache(source, "my-plugin", "1.0.0", cache)
        assert cache.get("my-plugin", source) is not None
        cache.invalidate("my-plugin")
        assert cache.get("my-plugin", source) is None

    def test_clear(self, tmp_path):
        cache = BytecodeCache(tmp_path)
        compile_and_cache("x = 1", "p1", "1.0", cache)
        compile_and_cache("y = 2", "p2", "1.0", cache)
        cache.clear()
        assert cache.get_stats()["entries"] == 0
        assert cache.get_stats()["total_size"] == 0

    def test_stats(self, tmp_path):
        cache = BytecodeCache(tmp_path)
        compile_and_cache("x = 1", "p", "1.0", cache)
        cache.get("p", "x = 1")
        cache.get("p", "x = 999")
        stats = cache.get_stats()
        assert stats["entries"] == 1
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1

    def test_get_cache_singleton(self):
        c1 = get_cache()
        c2 = get_cache()
        assert c1 is c2

    def test_different_source_same_plugin(self, tmp_path):
        cache = BytecodeCache(tmp_path)
        src1 = "x = 1"
        src2 = "x = 2"
        bc1 = compile_and_cache(src1, "p", "1.0", cache)
        bc2 = compile_and_cache(src2, "p", "1.0", cache)
        assert bc1 != bc2
        assert cache.get("p", src1) == bc1
        assert cache.get("p", src2) == bc2


# ═══════════════════════════════════════════════════════════
# TESTING DSL
# ═══════════════════════════════════════════════════════════

class TestTestingDSL:
    def test_mock_hook(self):
        mock = MockHook("test.hook")
        mock.returns(42)
        import asyncio
        result = asyncio.run(mock({}))
        assert result == 42
        assert mock.called
        assert mock.call_count == 1

    def test_mock_hook_side_effect(self):
        mock = MockHook("test.hook")
        mock.side_effect(lambda ctx: ctx.get("x", 0) + 1)
        import asyncio
        result = asyncio.run(mock({"x": 10}))
        assert result == 11

    def test_mock_permission(self):
        mp = MockPermission()
        ps = mp.allow("fs.read")
        assert ps.check("fs.read") == PermissionDecision.ALLOW

    def test_mock_permission_deny(self):
        mp = MockPermission()
        ps = mp.deny("net.http")
        assert ps.check("net.http") == PermissionDecision.DENY

    def test_assert_sandbox_blocks_import(self):
        err = assert_sandbox_blocks("import os")
        assert "not allowed" in err

    def test_assert_sandbox_blocks_subprocess(self):
        err = assert_sandbox_blocks("import subprocess")
        assert "not allowed" in err

    def test_assert_lifecycle(self):
        p = PluginBase()
        p.manifest = PluginManifest(name="lifecycle-test", version="1.0")
        states = assert_lifecycle(p)
        assert len(states) == 5
        from ciel.plugins.state import PLUGIN_STATE_MACHINE
        assert PLUGIN_STATE_MACHINE.get_state("lifecycle-test") == PluginState.DISABLED


# ═══════════════════════════════════════════════════════════
# TELEMETRY
# ═══════════════════════════════════════════════════════════

class TestTelemetryEngine:
    def test_log_audit(self):
        te = TelemetryEngine()
        entry = te.log_audit("test-plugin", "hook.run",
                             capability="fs.read", decision="allow")
        assert entry.plugin == "test-plugin"
        assert entry.action == "hook.run"
        assert entry.decision == "allow"
        assert entry.id.startswith("aud-")

    def test_log_hook(self):
        te = TelemetryEngine()
        h = te.log_hook("test.hook", "test-plugin", 12.5, success=True)
        assert h.hook_name == "test.hook"
        assert h.duration_ms == 12.5
        assert h.success is True

    def test_log_hook_failure(self):
        te = TelemetryEngine()
        te.log_hook("fail.hook", "p", 5.0, success=False, error="timeout")
        stats = te.get_error_report()
        assert stats["total_errors"] >= 1

    def test_heatmap(self):
        te = TelemetryEngine()
        te.log_hook("h1", "p1", 10.0)
        te.log_hook("h1", "p1", 20.0)
        te.log_hook("h2", "p2", 5.0)
        heatmap = te.get_heatmap()
        assert "h1" in heatmap
        assert heatmap["h1"]["count"] == 2
        assert heatmap["h1"]["avg_ms"] == 15.0

    def test_crash_report(self):
        te = TelemetryEngine()
        report = te.report_crash("p", "Segfault", trace="line 42", context={"x": 1})
        assert report["plugin"] == "p"
        assert report["error"] == "Segfault"
        assert report["traceback"] == "line 42"

    def test_permission_audit(self):
        te = TelemetryEngine()
        te.log_audit("p", "check", capability="net.http", decision="allow")
        te.log_audit("p", "check", capability="net.http", decision="deny")
        audit = te.get_permission_audit()
        assert "net.http" in audit
        assert audit["net.http"]["allow"] >= 1
        assert audit["net.http"]["deny"] >= 1

    def test_flush(self):
        te = TelemetryEngine()
        te.log_audit("p", "test")
        te.flush()
        stats = te.get_stats()
        assert stats["total_audit_entries"] >= 1

    def test_get_telemetry_singleton(self):
        t1 = get_telemetry()
        t2 = get_telemetry()
        assert t1 is t2


# ═══════════════════════════════════════════════════════════
# GRAPH
# ═══════════════════════════════════════════════════════════

class TestDependencyGraph:
    def test_empty_graph(self):
        g = DependencyGraph()
        assert g.nodes == []
        assert g.edges == []
        assert not g.has_cycles

    def test_no_cycles(self):
        g = DependencyGraph(
            nodes=["a", "b", "c"],
            edges=[("a", "b"), ("b", "c")],
        )
        assert not g.has_cycles
        assert g.cycles() == []

    def test_has_cycles(self):
        g = DependencyGraph(
            nodes=["a", "b", "c"],
            edges=[("a", "b"), ("b", "c"), ("c", "a")],
        )
        assert g.has_cycles

    def test_to_dot(self):
        g = DependencyGraph(nodes=["a", "b"], edges=[("a", "b")], labels={"a": "A v1"})
        dot = g.to_dot()
        assert "digraph" in dot
        assert '"a" -> "b"' in dot

    def test_to_json(self):
        g = DependencyGraph(nodes=["a"], edges=[("a", "b")], labels={"a": "A"})
        j = g.to_json()
        assert j["nodes"] == ["a"]


class TestHookGraph:
    def test_basic(self):
        g = HookGraph(hooks={"h1": ["p1", "p2"]})
        dot = g.to_dot()
        assert "h1" in dot

    def test_to_json(self):
        g = HookGraph(hooks={"h1": ["p1"]}, events={"e1": ["p2"]})
        j = g.to_json()
        assert j["hooks"]["h1"] == ["p1"]


class TestImpactAnalysis:
    def test_impact_of_removal(self):
        from ciel.plugins.core import PluginRegistry, PluginManifest
        reg = PluginRegistry()
        reg._manifests["base"] = PluginManifest(name="base", version="1.0")
        reg._manifests["dep"] = PluginManifest(name="dep", version="1.0", dependencies=["base"])
        impact = ImpactAnalysis(reg)
        result = impact.impact_of_removal("base")
        assert result["breaking"] is True
        assert "dep" in result["direct_dependents"]

    def test_no_impact(self):
        from ciel.plugins.core import PluginRegistry, PluginManifest
        reg = PluginRegistry()
        reg._manifests["alone"] = PluginManifest(name="alone", version="1.0")
        impact = ImpactAnalysis(reg)
        result = impact.impact_of_removal("alone")
        assert result["breaking"] is False


class TestCouplingMetrics:
    def test_compute(self):
        from ciel.plugins.core import PluginRegistry, PluginManifest
        reg = PluginRegistry()
        reg._manifests["a"] = PluginManifest(name="a", version="1.0")
        reg._manifests["b"] = PluginManifest(name="b", version="1.0", dependencies=["a"])
        cm = CouplingMetrics(reg)
        m = cm.compute()
        assert m["plugin_count"] == 2
        assert m["total_dependencies"] >= 1
        assert "avg_coupling" in m

    def test_empty_registry(self):
        from ciel.plugins.core import PluginRegistry
        reg = PluginRegistry()
        cm = CouplingMetrics(reg)
        m = cm.compute()
        assert "error" in m


# ═══════════════════════════════════════════════════════════
# RESOURCE CONTROLLER
# ═══════════════════════════════════════════════════════════

class TestResourceController:
    def test_track_hook(self):
        rc = ResourceController()
        allowed = rc.track_hook("test-p", 10.0)
        assert allowed is True
        usage = rc.get_usage("test-p")
        assert usage.hook_calls == 1
        assert usage.cpu_ms == 10.0

    def test_release_hook(self):
        rc = ResourceController()
        rc.track_hook("p", 1.0)
        rc.release_hook("p")

    def test_quota(self):
        rc = ResourceController()
        quota = ResourceQuota(max_cpu_ms_per_minute=100.0)
        rc.set_quota("limited", quota)
        rc.track_hook("limited", 50.0)
        rc.track_hook("limited", 60.0)
        usage = rc.get_usage("limited")
        assert usage.rate_limited

    def test_cooldown(self):
        rc = ResourceController()
        rc.cooldown("p", 0.01)
        import time
        time.sleep(0.02)
        allowed = rc.track_hook("p", 1.0)
        assert allowed is True

    def test_track_error(self):
        rc = ResourceController()
        rc.track_error("p")
        usage = rc.get_usage("p")
        assert usage.errors == 1

    def test_get_all_usages(self):
        rc = ResourceController()
        rc.track_hook("p1", 10.0)
        rc.track_hook("p2", 20.0)
        usages = rc.get_all_usages()
        assert len(usages) == 2

    def test_get_stats(self):
        rc = ResourceController()
        rc.track_hook("p", 5.0)
        stats = rc.get_stats()
        assert stats["plugins_tracked"] >= 1
        assert stats["total_hook_calls"] >= 1

    def test_get_resource_controller_singleton(self):
        r1 = get_resource_controller()
        r2 = get_resource_controller()
        assert r1 is r2
