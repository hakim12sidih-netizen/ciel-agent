from __future__ import annotations

import sys
import json
import importlib
import inspect
import weakref
import hashlib
import subprocess
import tempfile
import shutil
import re
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Awaitable, Protocol
from collections import defaultdict


__all__ = [
    "PluginManifest", "PluginBase", "PluginHook", "HookPriority",
    "PluginRegistry", "get_registry", "PluginError", "PluginDependencyError",
]


class PluginError(Exception):
    pass


class PluginDependencyError(PluginError):
    pass


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str = ""
    author: str = ""
    homepage: str = ""
    license: str = "AGPL-3.0-or-later"
    entrypoint: str = ""
    dependencies: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    min_ciel_version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    repository: str = ""
    documentation: str = ""
    hooks: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> PluginManifest:
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def discover_from(cls, path: Path) -> list[PluginManifest]:
        manifests = []
        for manifest_path in _find_manifests(path):
            try:
                raw = manifest_path.read_text(encoding="utf-8")
                if manifest_path.suffix == ".json":
                    data = json.loads(raw)
                elif manifest_path.suffix in (".yaml", ".yml"):
                    import yaml
                    data = yaml.safe_load(raw) or {}
                elif manifest_path.name == "pyproject.toml":
                    import tomllib
                    data = tomllib.loads(raw)
                    data = data.get("tool", {}).get("ciel", {}).get("plugin", {})
                    if not data:
                        continue
                else:
                    continue
                manifest = cls.from_dict(data)
                manifests.append(manifest)
            except Exception:
                pass
        return manifests


def _find_manifests(plugin_dir: Path) -> list[Path]:
    results = []
    for sub in plugin_dir.iterdir():
        if not sub.is_dir():
            continue
        candidates = [
            sub / "plugin.json",
            sub / "plugin.yaml",
            sub / "plugin.yml",
            sub / "pyproject.toml",
        ]
        for c in candidates:
            if c.exists():
                results.append(c)
                break
    return results


class PluginBase:
    manifest: PluginManifest
    _registry: weakref.ref | None = None

    async def on_load(self):
        pass

    async def on_unload(self):
        pass

    async def on_enable(self):
        pass

    async def on_disable(self):
        pass

    async def on_install(self):
        pass

    async def on_remove(self):
        pass

    async def on_config_change(self, changes: dict[str, Any]):
        pass


class PluginHook(Protocol):
    async def __call__(self, context: dict | None = None) -> Any: ...


class HookPriority:
    EARLIEST = -100
    EARLY = -50
    NORMAL = 0
    LATE = 50
    LATEST = 100


HookEntry = tuple[str, int, Callable[..., Awaitable[Any]]]


class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, PluginBase] = {}
        self._manifests: dict[str, PluginManifest] = {}
        self._hooks: dict[str, list[HookEntry]] = defaultdict(list)
        self._events: dict[str, list[tuple[str, int, Callable[..., Awaitable[Any]]]]] = defaultdict(list)
        self._plugin_dirs: list[Path] = []

    def add_plugin_dir(self, path: str | Path):
        p = Path(path).expanduser().resolve()
        if p.is_dir() and p not in self._plugin_dirs:
            self._plugin_dirs.append(p)

    def discover(self) -> list[PluginManifest]:
        found = []
        for plugin_dir in self._plugin_dirs:
            for manifest in PluginManifest.discover_from(plugin_dir):
                if manifest.name not in self._manifests:
                    self._manifests[manifest.name] = manifest
                    found.append(manifest)
        return found

    def resolve_dependencies(self, name: str, stack: set[str] | None = None) -> list[str]:
        manifest = self._manifests.get(name)
        if not manifest:
            raise PluginDependencyError(f"Plugin {name} not found")
        if stack is None:
            stack = set()
        if name in stack:
            raise PluginDependencyError(f"Circular dependency: {stack} -> {name}")
        stack.add(name)
        order = []
        for dep in manifest.dependencies:
            order.extend(self.resolve_dependencies(dep, stack.copy()))
            order.append(dep)
        return order

    async def load_plugin(self, name: str) -> PluginBase | None:
        manifest = self._manifests.get(name)
        if not manifest:
            return None

        if name in self._plugins:
            return self._plugins[name]

        deps = self.resolve_dependencies(name)
        for dep_name in deps:
            if dep_name not in self._plugins:
                await self.load_plugin(dep_name)

        try:
            module_path = manifest.entrypoint or f"ciel_plugins.{name}"
            module = importlib.import_module(module_path)

            plugin_class = None
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, PluginBase) and obj is not PluginBase:
                    plugin_class = obj
                    break

            if not plugin_class:
                return None

            instance = plugin_class()
            instance.manifest = manifest
            instance._registry = weakref.ref(self)
            await instance.on_load()
            self._plugins[name] = instance

            for hook_name, priority in manifest.hooks.items():
                hook_method = getattr(instance, hook_name, None)
                if hook_method and callable(hook_method):
                    self.register_hook(hook_name, name, hook_method, priority)

            try:
                from ciel.persistence import register_plugin
                await register_plugin(name, manifest.version, manifest.to_dict())
            except ImportError:
                pass

            return instance

        except Exception as e:
            raise PluginError(f"Failed to load plugin {name}: {e}") from e

    async def unload_plugin(self, name: str):
        plugin = self._plugins.pop(name, None)
        if plugin:
            await plugin.on_unload()
        self._hooks = defaultdict(list, {
            k: [(pn, pri, hook) for pn, pri, hook in v if pn != name]
            for k, v in self._hooks.items()
        })
        self._events = defaultdict(list, {
            k: [(pn, pri, cb) for pn, pri, cb in v if pn != name]
            for k, v in self._events.items()
        })

    async def enable_plugin(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        if plugin:
            await plugin.on_enable()
            try:
                from ciel.persistence import register_plugin
                await register_plugin(name, plugin.manifest.version, plugin.manifest.to_dict())
            except ImportError:
                pass
            return True
        return False

    async def disable_plugin(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        if plugin:
            await plugin.on_disable()
            return True
        return False

    def register_hook(self, hook_name: str, plugin_name: str,
                      hook: Callable[..., Awaitable[Any]], priority: int = HookPriority.NORMAL):
        self._hooks[hook_name].append((plugin_name, priority, hook))
        self._hooks[hook_name].sort(key=lambda x: x[1])

    async def run_hook(self, hook_name: str, context: dict | None = None) -> list[Any]:
        results = []
        for plugin_name, priority, hook in self._hooks.get(hook_name, []):
            try:
                result = await hook(context)
                results.append((plugin_name, result))
            except Exception as e:
                results.append((plugin_name, e))
        return results

    def on(self, event_name: str, plugin_name: str,
           callback: Callable[..., Awaitable[Any]], priority: int = HookPriority.NORMAL):
        self._events[event_name].append((plugin_name, priority, callback))
        self._events[event_name].sort(key=lambda x: x[1])

    async def emit(self, event_name: str, **kwargs) -> list[Any]:
        results = []
        for plugin_name, priority, cb in self._events.get(event_name, []):
            try:
                result = await cb(kwargs)
                results.append((plugin_name, result))
            except Exception as e:
                results.append((plugin_name, e))
        return results

    def get(self, name: str) -> PluginBase | None:
        return self._plugins.get(name)

    def list(self) -> list[tuple[str, PluginManifest, bool]]:
        return [
            (name, p, name in self._plugins)
            for name, p in self._manifests.items()
        ]

    @property
    def loaded_count(self) -> int:
        return len(self._plugins)

    async def reload_plugin(self, name: str) -> PluginBase | None:
        await self.unload_plugin(name)
        if name in sys.modules:
            del sys.modules[name]
        module_path = self._manifests.get(name, PluginManifest(name="", version="")).entrypoint
        if module_path and module_path in sys.modules:
            del sys.modules[module_path]
        return await self.load_plugin(name)


_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.add_plugin_dir(Path.home() / ".ciel" / "plugins")
        _registry.add_plugin_dir(Path.cwd() / "plugins")
    return _registry
