"""
CIEL v∞.9 — Plugin Testing DSL.
Declarative test framework: mock hooks, simulate permissions, lifecycle test, sandbox assertions.
"""
from __future__ import annotations

import asyncio
import inspect
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

from ciel.plugins.core import PluginBase, PluginManifest, PluginRegistry, get_registry
from ciel.plugins.sandbox import PluginSandbox
from ciel.plugins.permissions import PermissionSet, PermissionDecision, Capability
from ciel.plugins.state import PluginState, PLUGIN_STATE_MACHINE


__all__ = [
    "plugin_test", "PluginTestSuite", "TestResult",
    "MockHook", "MockPermission", "MockRegistry",
    "assert_sandbox_blocks", "assert_lifecycle",
]


@dataclass
class TestResult:
    name: str
    passed: bool
    duration_ms: float = 0.0
    error: str = ""
    assertions: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
            "assertions": self.assertions,
        }


class AssertionCounter:
    def __init__(self):
        self.count = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def ok(self, condition: bool, msg: str = ""):
        self.count += 1
        assert condition, msg


class _PluginTestMeta(type):
    def __new__(cls, name, bases, attrs):
        for key, val in list(attrs.items()):
            if key.startswith("test_") and callable(val):
                attrs[f"_async_{key}"] = val
                attrs[key] = cls._make_sync_wrapper(key, val)
        return super().__new__(cls, name, bases, attrs)

    @staticmethod
    def _make_sync_wrapper(test_name: str, test_fn: Callable):
        import functools
        @functools.wraps(test_fn)
        def wrapper(self, *args, **kwargs):
            if asyncio.iscoroutinefunction(test_fn):
                return asyncio.run(test_fn(self, *args, **kwargs))
            return test_fn(self, *args, **kwargs)
        return wrapper


class MockHook:
    def __init__(self, name: str = ""):
        self.name = name
        self._calls: list[dict] = []
        self._return_value: Any = None
        self._side_effect: Callable | None = None

    def returns(self, value: Any) -> MockHook:
        self._return_value = value
        return self

    def side_effect(self, fn: Callable) -> MockHook:
        self._side_effect = fn
        return self

    async def __call__(self, context: dict | None = None) -> Any:
        call = {"context": context, "timestamp": time.time()}
        self._calls.append(call)
        if self._side_effect:
            return self._side_effect(context)
        return self._return_value

    @property
    def called(self) -> bool:
        return len(self._calls) > 0

    @property
    def call_count(self) -> int:
        return len(self._calls)

    def reset(self):
        self._calls.clear()


class MockPermission:
    def __init__(self, auto_approve: bool = True):
        self.auto_approve = auto_approve
        self._checks: list[dict] = []

    def allow(self, capability: str, resource: str = "*"):
        return PermissionSet.from_manifest_list([capability])

    def deny(self, capability: str):
        return PermissionSet.from_manifest_list([f"-{capability}"])

    async def check(self, capability: str, resource: str, plugin: str) -> bool:
        self._checks.append({
            "capability": capability,
            "resource": resource,
            "plugin": plugin,
            "timestamp": time.time(),
        })
        return self.auto_approve


class MockRegistry:
    def __init__(self):
        self._plugins: dict[str, PluginBase] = {}
        self._hooks: dict[str, list] = {}
        self._events: dict[str, list] = {}

    def register_plugin(self, name: str, instance: PluginBase):
        self._plugins[name] = instance

    def register_hook(self, hook_name: str, plugin_name: str,
                      hook: Callable, priority: int = 0):
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append((plugin_name, priority, hook))
        self._hooks[hook_name].sort(key=lambda x: x[1])

    def run_hook(self, hook_name: str, context: dict | None = None) -> list:
        return [
            (pn, hook(context) if not asyncio.iscoroutinefunction(hook) else asyncio.run(hook(context)))
            for pn, _, hook in self._hooks.get(hook_name, [])
        ]


class PluginTestSuite:
    def __init__(self, name: str = ""):
        self.name = name or "PluginTestSuite"
        self._results: list[TestResult] = []
        self._assertions = 0
        self._sandbox = PluginSandbox()
        self._hook_mocks: dict[str, MockHook] = {}
        self._permission_mock = MockPermission()

    def mock_hook(self, hook_name: str, return_value: Any = None) -> MockHook:
        mock = MockHook(hook_name)
        if return_value is not None:
            mock.returns(return_value)
        self._hook_mocks[hook_name] = mock
        return mock

    def with_permissions(self, caps: list[str]) -> PermissionSet:
        return PermissionSet.from_manifest_list(caps)

    def test(self, name: str) -> Callable:
        def decorator(fn: Callable):
            import functools
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = TestResult(name=name, passed=False)
                try:
                    assertion_count = [0]
                    def assert_ok(condition: bool, msg: str = ""):
                        assertion_count[0] += 1
                        self._assertions += 1
                        assert condition, msg
                    fn(assert_ok, *args, **kwargs)
                    result.passed = True
                    result.assertions = assertion_count[0]
                except AssertionError as e:
                    result.error = str(e)
                except Exception as e:
                    result.error = f"{type(e).__name__}: {e}"
                    import traceback
                    result.error += f"\n{traceback.format_exc()}"
                result.duration_ms = (time.time() - start) * 1000
                self._results.append(result)
                return result
            return wrapper
        return decorator

    def run(self) -> list[TestResult]:
        test_methods = [
            (name, fn) for name, fn in type(self).__dict__.items()
            if name.startswith("test_") and callable(fn)
        ]
        for name, fn in sorted(test_methods):
            try:
                start = time.time()
                if asyncio.iscoroutinefunction(fn):
                    asyncio.run(fn(self))
                else:
                    fn(self)
                elapsed = (time.time() - start) * 1000
                self._results.append(TestResult(
                    name=name, passed=True, duration_ms=elapsed))
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                self._results.append(TestResult(
                    name=name, passed=False, duration_ms=elapsed,
                    error=f"{type(e).__name__}: {e}"))
        return self._results

    def summary(self) -> dict:
        passed = sum(1 for r in self._results if r.passed)
        return {
            "total": len(self._results),
            "passed": passed,
            "failed": len(self._results) - passed,
            "total_assertions": self._assertions,
            "duration_ms": sum(r.duration_ms for r in self._results),
        }


def plugin_test(suite_name: str = ""):
    def decorator(cls):
        if not issubclass(cls, PluginTestSuite):
            cls = type(cls.__name__, (PluginTestSuite, cls), dict(cls.__dict__))
        return cls
    return decorator


def assert_sandbox_blocks(code: str,
                          expected_error: str = "not allowed",
                          sandbox: PluginSandbox | None = None) -> str:
    sb = sandbox or PluginSandbox()
    result = sb.execute(code, plugin_name="__test__")
    if result.success:
        raise AssertionError(f"Sandbox did NOT block code: {code!r}")
    if expected_error and expected_error not in result.error:
        raise AssertionError(
            f"Expected error containing {expected_error!r}, got {result.error!r}")
    return result.error


def assert_lifecycle(plugin: PluginBase,
                     expected_states: list[PluginState] | None = None) -> list[PluginState]:
    states = expected_states or [
        PluginState.INSTALLED,
        PluginState.ENABLED,
        PluginState.LOADING,
        PluginState.ACTIVE,
        PluginState.DISABLED,
    ]
    if not isinstance(plugin, PluginBase):
        raise TypeError(f"Expected PluginBase, got {type(plugin).__name__}")

    for state in states:
        PLUGIN_STATE_MACHINE.force_transition(
            plugin.manifest.name, state,
            reason=f"test_lifecycle: {state.value}")
    return states
