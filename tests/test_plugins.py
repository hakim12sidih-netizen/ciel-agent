"""
Tests complets du Plugin System CIEL v∞.8.
Registry, permissions, sandbox, CLI.
"""
from __future__ import annotations

import json
import os
import tempfile
import shutil
from pathlib import Path

import pytest

from ciel.plugins.core import (
    PluginManifest, PluginBase, PluginRegistry, PluginHook,
    PluginError, PluginDependencyError, HookPriority,
    get_registry,
)
from ciel.plugins.permissions import (
    Capability, Permission, PermissionSet, PermissionPolicy,
    PermissionDenied, SandboxJail, PermissionDecision,
)
from ciel.plugins.sandbox import (
    PluginSandbox, SandboxedPlugin, SandboxResult,
)


# ── PluginManifest ──

class TestPluginManifest:
    def test_from_dict_keeps_valid_fields(self):
        data = {
            "name": "test-plugin", "version": "1.0.0",
            "description": "Test", "author": "CIEL",
            "permissions": ["core", "network"],
            "tags": ["test"],
            "hooks": {"on_load": 0, "on_enable": 10},
        }
        m = PluginManifest.from_dict(data)
        assert m.name == "test-plugin"
        assert m.version == "1.0.0"
        assert m.author == "CIEL"
        assert m.permissions == ["core", "network"]
        assert m.tags == ["test"]
        assert m.hooks == {"on_load": 0, "on_enable": 10}

    def test_from_dict_ignores_invalid(self):
        m = PluginManifest.from_dict({"name": "p", "version": "1", "unknown_field": "x"})
        assert not hasattr(m, "unknown_field")
        assert m.name == "p"

    def test_to_dict_roundtrip(self):
        m = PluginManifest(name="p", version="1", description="d", author="a")
        d = m.to_dict()
        assert d["name"] == "p"
        assert d["version"] == "1"
        assert d["author"] == "a"
        m2 = PluginManifest.from_dict(d)
        assert m2.name == m.name
        assert m2.version == m.version

    def test_discover_from_empty_dir(self, tmp_path):
        found = PluginManifest.discover_from(tmp_path)
        assert found == []

    def test_discover_from_json(self, tmp_path):
        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()
        manifest = {"name": "my-plugin", "version": "1.0.0"}
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest))
        found = PluginManifest.discover_from(tmp_path)
        assert len(found) == 1
        assert found[0].name == "my-plugin"

    def test_discover_from_yaml(self, tmp_path):
        plugin_dir = tmp_path / "yaml-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.yaml").write_text("name: yaml-plugin\nversion: 2.0.0\n")
        found = PluginManifest.discover_from(tmp_path)
        assert len(found) == 1
        assert found[0].name == "yaml-plugin"
        assert found[0].version == "2.0.0"

    def test_discover_from_invalid_json_skipped(self, tmp_path):
        plugin_dir = tmp_path / "bad"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text("not json")
        found = PluginManifest.discover_from(tmp_path)
        assert found == []


# ── PluginRegistry ──

class TestPluginRegistry:
    def test_add_plugin_dir(self):
        r = PluginRegistry()
        with tempfile.TemporaryDirectory() as d:
            r.add_plugin_dir(d)
            assert len(r._plugin_dirs) == 1

    def test_discover_plugins(self, tmp_path):
        r = PluginRegistry()
        r.add_plugin_dir(tmp_path)
        pdir = tmp_path / "test-p"
        pdir.mkdir()
        (pdir / "plugin.json").write_text(json.dumps({"name": "test-p", "version": "1.0"}))
        found = r.discover()
        assert len(found) == 1
        assert found[0].name == "test-p"

    def test_get_registry_singleton(self):
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_list_empty(self):
        r = PluginRegistry()
        assert r.list() == []

    def test_loaded_count(self):
        r = PluginRegistry()
        assert r.loaded_count == 0

    def test_get_unknown(self):
        r = PluginRegistry()
        assert r.get("unknown") is None

    def test_resolve_dependencies_unknown(self):
        r = PluginRegistry()
        with pytest.raises(PluginDependencyError):
            r.resolve_dependencies("nonexistent")

    def test_resolve_dependencies_circular(self, tmp_path):
        r = PluginRegistry()
        r.add_plugin_dir(tmp_path)
        for name in ["a", "b", "c"]:
            d = tmp_path / name
            d.mkdir()
            deps = {"b": ["c"], "c": ["a"], "a": ["b"]}
            (d / "plugin.json").write_text(json.dumps({
                "name": name, "version": "1.0",
                "dependencies": deps.get(name, []),
            }))
        r.discover()
        with pytest.raises(PluginDependencyError, match="Circular"):
            r.resolve_dependencies("a")

    def test_resolve_dependencies_linear(self, tmp_path):
        r = PluginRegistry()
        r.add_plugin_dir(tmp_path)
        for name, deps in [("base", []), ("mid", ["base"]), ("top", ["base", "mid"])]:
            d = tmp_path / name
            d.mkdir()
            (d / "plugin.json").write_text(json.dumps({
                "name": name, "version": "1.0", "dependencies": deps,
            }))
        r.discover()
        order = r.resolve_dependencies("top")
        assert "base" in order
        assert "mid" in order


# ── Permission System ──

class TestPermissionSet:
    def test_default_decision_is_prompt(self):
        ps = PermissionSet()
        assert ps.check(Capability.NETWORK_HTTP) == PermissionDecision.PROMPT

    def test_allow_matches(self):
        ps = PermissionSet()
        ps.allow(Capability.FILESYSTEM_READ)
        assert ps.check(Capability.FILESYSTEM_READ) == PermissionDecision.ALLOW

    def test_deny_overrides_allow(self):
        ps = PermissionSet()
        ps.allow(Capability.ALL)
        ps.deny(Capability.NETWORK_HTTP)
        assert ps.check(Capability.NETWORK_HTTP) == PermissionDecision.DENY
        assert ps.check(Capability.FILESYSTEM_READ) == PermissionDecision.ALLOW

    def test_wildcard_resource(self):
        ps = PermissionSet()
        ps.allow(Capability.FILESYSTEM_READ)
        assert ps.check(Capability.FILESYSTEM_READ, "/etc/passwd") == PermissionDecision.ALLOW

    def test_resource_match(self):
        ps = PermissionSet()
        ps.allow(Capability.FILESYSTEM_READ, "/tmp/*")
        assert ps.check(Capability.FILESYSTEM_READ, "/tmp/test.txt") == PermissionDecision.ALLOW
        assert ps.check(Capability.FILESYSTEM_READ, "/etc/passwd") == PermissionDecision.PROMPT

    def test_from_manifest_list_expands_groups(self):
        ps = PermissionSet.from_manifest_list(["core", "llm"])
        assert ps.check(Capability.CIEL_API) == PermissionDecision.ALLOW
        assert ps.check(Capability.LLM_CHAT) == PermissionDecision.ALLOW
        assert ps.check(Capability.NETWORK_HTTP) == PermissionDecision.PROMPT

    def test_from_manifest_with_deny(self):
        ps = PermissionSet.from_manifest_list(["core", "-ciel.api"])
        assert ps.check(Capability.CIEL_BRAIN) == PermissionDecision.ALLOW
        assert ps.check(Capability.CIEL_API) == PermissionDecision.DENY


class TestPermissionPolicy:
    def test_allow_decision(self):
        import asyncio
        ps = PermissionSet()
        ps.allow(Capability.FILESYSTEM_READ)
        policy = PermissionPolicy()
        result = asyncio.run(policy.check(Capability.FILESYSTEM_READ, "", "test-plugin", ps))
        assert result is True

    def test_deny_decision(self):
        import asyncio
        ps = PermissionSet()
        ps.deny(Capability.FILESYSTEM_READ)
        policy = PermissionPolicy()
        with pytest.raises(PermissionDenied):
            asyncio.run(policy.check(Capability.FILESYSTEM_READ, "", "test-plugin", ps))

    def test_auto_approve_raises_on_deny(self):
        import asyncio
        ps = PermissionSet()
        ps.deny(Capability.NETWORK_HTTP)
        policy = PermissionPolicy(auto_approve=True)
        with pytest.raises(PermissionDenied):
            asyncio.run(policy.check(Capability.NETWORK_HTTP, "", "test-plugin", ps))

    def test_auto_approve_allows_prompt(self):
        import asyncio
        ps = PermissionSet()
        policy = PermissionPolicy(auto_approve=True)
        result = asyncio.run(policy.check(Capability.NETWORK_HTTP, "", "test-plugin", ps))
        assert result is True

    def test_auto_deny_raises_on_prompt(self):
        import asyncio
        ps = PermissionSet()
        policy = PermissionPolicy(auto_deny=True)
        with pytest.raises(PermissionDenied):
            asyncio.run(policy.check(Capability.NETWORK_HTTP, "", "test-plugin", ps))

    def test_approval_callback_called(self):
        ps = PermissionSet()
        calls = []
        async def callback(cap, res, plugin):
            calls.append((cap, res, plugin))
            return True
        policy = PermissionPolicy(approval_callback=callback)
        import asyncio
        result = asyncio.run(policy.check(Capability.NETWORK_HTTP, "", "test-plugin", ps))
        assert result is True
        assert len(calls) == 1
        assert calls[0] == (Capability.NETWORK_HTTP, "", "test-plugin")

    def test_permission_denied_has_attributes(self):
        e = PermissionDenied(Capability.NETWORK_HTTP, "api.example.com", "my-plugin")
        assert e.capability == Capability.NETWORK_HTTP
        assert e.resource == "api.example.com"
        assert e.plugin == "my-plugin"
        assert "Permission denied" in str(e)


class TestSandboxJail:
    def test_allow_directory(self):
        jail = SandboxJail()
        jail.allow_directory("/tmp")
        assert jail.check_path("/tmp/test.txt") is True
        assert jail.check_path("/etc/passwd") is False

    def test_restricted_globals_has_safe_builtins(self):
        jail = SandboxJail()
        g = jail.get_restricted_globals("test-plugin")
        assert "open" in g["__builtins__"]
        assert "print" in g["__builtins__"]
        assert "subprocess" not in g
        assert "os" in g

    def test_restricted_globals_open_raises_on_denied(self):
        jail = SandboxJail()
        jail.allow_directory("/tmp")
        g = jail.get_restricted_globals("test-plugin")
        safe_open = g["__builtins__"]["open"]
        assert safe_open is not None


# ── PluginSandbox ──

class TestPluginSandbox:
    def test_execute_simple_code(self):
        sandbox = PluginSandbox()
        result = sandbox.execute("x = 1 + 1\nprint(x)")
        assert result.success is True
        assert "2" in result.stdout

    def test_execute_return_value(self):
        sandbox = PluginSandbox()
        result = sandbox.execute("_return = 42")
        assert result.success is True
        assert result.output == 42

    def test_execute_syntax_error(self):
        sandbox = PluginSandbox()
        result = sandbox.execute("if true")
        assert result.success is False
        assert "SyntaxError" in result.error

    def test_execute_runtime_error(self):
        sandbox = PluginSandbox()
        result = sandbox.execute("1 / 0")
        assert result.success is False
        assert "ZeroDivisionError" in result.error

    def test_import_blocked(self):
        sandbox = PluginSandbox()
        result = sandbox.execute("import os")
        assert result.success is False
        assert "not allowed" in result.error

    def test_from_import_blocked(self):
        sandbox = PluginSandbox()
        result = sandbox.execute("from pathlib import Path")
        assert result.success is False

    def test_subprocess_blocked_in_code(self):
        sandbox = PluginSandbox()
        result = sandbox.execute("import subprocess; subprocess.run(['ls'])")
        assert result.success is False

    def test_timing_in_result(self):
        sandbox = PluginSandbox()
        result = sandbox.execute("x = 1")
        assert result.duration_ms > 0

    def test_get_stats(self):
        sandbox = PluginSandbox()
        sandbox.execute("x = 1")
        stats = sandbox.get_stats()
        assert stats["executions"] == 1
        assert stats["last_success"] is True


class TestSandboxedPlugin:
    def test_run_sandboxed(self):
        sp = SandboxedPlugin("test", "_return = 10 + 20")
        result = sp.run()
        assert result.success is True
        assert result.output == 30

    def test_run_function(self):
        code = """
def greet(name):
    return f"Hello, {name}!"
"""
        sp = SandboxedPlugin("test", code)
        result = sp.run(func_name="greet", name="CIEL")
        assert result.success is True
        assert "Hello, CIEL!" in str(result.output)


# ── PluginBase lifecycle ──

class TestPluginBaseLifecycle:
    def test_on_load_called(self):
        import asyncio
        calls = []
        class TestPlugin(PluginBase):
            async def on_load(self):
                calls.append("load")
            async def on_unload(self):
                calls.append("unload")
            async def on_enable(self):
                calls.append("enable")
            async def on_disable(self):
                calls.append("disable")

        p = TestPlugin()
        p.manifest = PluginManifest(name="test", version="1.0")

        async def run():
            await p.on_load()
            assert "load" in calls
            await p.on_enable()
            assert "enable" in calls
            await p.on_disable()
            assert "disable" in calls
            await p.on_unload()
            assert "unload" in calls

        asyncio.run(run())


# ── Hook system ──

class TestHookSystem:
    def test_register_and_run_hooks(self):
        r = PluginRegistry()
        results = []

        async def hook_a(ctx):
            results.append("a")

        async def hook_b(ctx):
            results.append("b")

        r.register_hook("test.hook", "plugin-a", hook_a, HookPriority.NORMAL)
        r.register_hook("test.hook", "plugin-b", hook_b, HookPriority.EARLY)

        import asyncio
        asyncio.run(r.run_hook("test.hook"))
        assert len(results) == 2

    def test_hook_with_context(self):
        r = PluginRegistry()

        async def echo(ctx):
            return ctx.get("value", 0)

        r.register_hook("echo", "p", echo)
        import asyncio
        res = asyncio.run(r.run_hook("echo", {"value": 42}))
        assert ("p", 42) in res

    def test_hook_error_does_not_break_others(self):
        r = PluginRegistry()

        async def failing(ctx):
            raise ValueError("boom")

        async def ok(ctx):
            return "ok"

        r.register_hook("test", "a", failing)
        r.register_hook("test", "b", ok)
        import asyncio
        res = asyncio.run(r.run_hook("test"))
        assert isinstance(res[0][1], ValueError)
        assert res[1][1] == "ok"

    def test_emit_and_on(self):
        r = PluginRegistry()
        received = []

        async def handler(data):
            received.append(data.get("msg"))

        r.on("my.event", "p", handler)
        import asyncio
        asyncio.run(r.emit("my.event", msg="hello"))
        assert "hello" in received


# ── Permissions integration ──

class TestPermissionsIntegration:
    def test_permission_set_from_manifest_simple(self):
        manifest = PluginManifest(
            name="test", version="1.0",
            permissions=["core", "fs.read", "-ciel.api"],
        )
        ps = PermissionSet.from_manifest_list(manifest.permissions)
        assert ps.check(Capability.CIEL_BRAIN) == PermissionDecision.ALLOW
        assert ps.check(Capability.CIEL_API) == PermissionDecision.DENY
        assert ps.check(Capability.FILESYSTEM_READ) == PermissionDecision.ALLOW

    def test_builtin_capability_groups_complete(self):
        for group_name, caps in [
            ("core", [Capability.CIEL_API, Capability.UI_NOTIFY]),
            ("network", [Capability.NETWORK_HTTP]),
            ("admin", [Capability.ALL]),
        ]:
            ps = PermissionSet.from_manifest_list([group_name])
            for c in caps:
                assert ps.check(c) == PermissionDecision.ALLOW, f"{group_name} should allow {c}"


# ── Plugin discovery integration ──

class TestDiscoveryIntegration:
    def test_multiple_plugin_dirs(self, tmp_path):
        r = PluginRegistry()
        d1 = tmp_path / "dir1"
        d2 = tmp_path / "dir2"
        d1.mkdir()
        d2.mkdir()

        (d1 / "p1").mkdir()
        (d1 / "p1" / "plugin.json").write_text(json.dumps({"name": "p1", "version": "1.0"}))
        (d2 / "p2").mkdir()
        (d2 / "p2" / "plugin.json").write_text(json.dumps({"name": "p2", "version": "2.0"}))

        r.add_plugin_dir(d1)
        r.add_plugin_dir(d2)
        found = r.discover()
        assert len(found) == 2

    def test_discover_does_not_duplicate(self, tmp_path):
        r = PluginRegistry()
        r.add_plugin_dir(tmp_path)
        (tmp_path / "p").mkdir()
        (tmp_path / "p" / "plugin.json").write_text(json.dumps({"name": "p", "version": "1.0"}))

        found1 = r.discover()
        found2 = r.discover()
        assert len(found1) == 1
        assert len(found2) == 0  # already registered

    def test_manifest_from_pyproject_toml(self, tmp_path):
        (tmp_path / "myp").mkdir()
        (tmp_path / "myp" / "pyproject.toml").write_text('''
[tool.ciel.plugin]
name = "myp"
version = "3.0.0"
description = "From pyproject.toml"
''')
        found = PluginManifest.discover_from(tmp_path)
        assert len(found) == 1
        assert found[0].name == "myp"
        assert found[0].version == "3.0.0"
