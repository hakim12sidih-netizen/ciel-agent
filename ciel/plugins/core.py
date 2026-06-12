"""
CIEL v∞.8 — Plugin SDK.
Système de plugins avec manifest, registry, isolation.
"""
from __future__ import annotations

import sys
import json
import importlib
import inspect
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class PluginManifest:
    """Manifest d'un plugin CIEL."""
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

    @classmethod
    def from_dict(cls, data: dict) -> PluginManifest:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


class PluginBase:
    """Classe de base pour tous les plugins CIEL."""
    manifest: PluginManifest

    async def on_load(self):
        """Appelé lors du chargement du plugin."""

    async def on_unload(self):
        """Appelé lors du déchargement du plugin."""

    async def on_enable(self):
        """Appelé lors de l'activation."""

    async def on_disable(self):
        """Appelé lors de la désactivation."""


class PluginHook(Protocol):
    """Protocole pour les hooks de plugins."""
    async def __call__(self, context: dict | None = None) -> Any: ...


class PluginRegistry:
    """Registre central des plugins."""

    def __init__(self):
        self._plugins: dict[str, PluginBase] = {}
        self._manifests: dict[str, PluginManifest] = {}
        self._hooks: dict[str, list[tuple[str, PluginHook]]] = {}
        self._plugin_dirs: list[Path] = []

    def add_plugin_dir(self, path: str | Path):
        """Ajoute un répertoire de plugins à scanner."""
        p = Path(path).expanduser().resolve()
        if p.is_dir() and p not in self._plugin_dirs:
            self._plugin_dirs.append(p)

    def discover(self) -> list[PluginManifest]:
        """Scanne les répertoires de plugins et découvre les manifests."""
        found = []
        for plugin_dir in self._plugin_dirs:
            for manifest_file in plugin_dir.glob("*/plugin.json"):
                try:
                    data = json.loads(manifest_file.read_text())
                    manifest = PluginManifest.from_dict(data)
                    self._manifests[manifest.name] = manifest
                    found.append(manifest)
                except (json.JSONDecodeError, Exception) as e:
                    print(f"  [red]✗ Plugin invalide: {manifest_file}: {e}[/]")
        return found

    async def load_plugin(self, name: str) -> PluginBase | None:
        """Charge un plugin par son nom."""
        manifest = self._manifests.get(name)
        if not manifest:
            return None

        if name in self._plugins:
            return self._plugins[name]

        try:
            module_path = manifest.entrypoint or f"ciel_plugins.{name}"
            module = importlib.import_module(module_path)

            # Trouver la classe qui hérite de PluginBase
            plugin_class = None
            for _, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and issubclass(obj, PluginBase)
                        and obj is not PluginBase):
                    plugin_class = obj
                    break

            if not plugin_class:
                return None

            instance = plugin_class()
            instance.manifest = manifest
            await instance.on_load()
            self._plugins[name] = instance

            from ciel.persistence import register_plugin
            await register_plugin(name, manifest.version, manifest.to_dict())

            return instance

        except Exception as e:
            print(f"  [red]✗ Échec chargement plugin {name}: {e}[/]")
            return None

    async def unload_plugin(self, name: str):
        """Décharge un plugin."""
        plugin = self._plugins.pop(name, None)
        if plugin:
            await plugin.on_unload()

    async def enable_plugin(self, name: str) -> bool:
        """Active un plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            await plugin.on_enable()
            return True
        return False

    async def disable_plugin(self, name: str) -> bool:
        """Désactive un plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            await plugin.on_disable()
            return True
        return False

    def register_hook(self, hook_name: str, plugin_name: str, hook: PluginHook):
        """Enregistre un hook."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append((plugin_name, hook))

    async def run_hook(self, hook_name: str, context: dict | None = None) -> list[Any]:
        """Exécute tous les hooks d'un type donné."""
        results = []
        for plugin_name, hook in self._hooks.get(hook_name, []):
            try:
                result = await hook(context)
                results.append((plugin_name, result))
            except Exception as e:
                results.append((plugin_name, e))
        return results

    def get(self, name: str) -> PluginBase | None:
        return self._plugins.get(name)

    def list(self) -> list[tuple[str, PluginManifest, bool]]:
        return [
            (name, p.manifest, name in self._plugins)
            for name, p in self._manifests.items()
        ]

    @property
    def loaded_count(self) -> int:
        return len(self._plugins)


# Singleton
_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.add_plugin_dir(Path.home() / ".ciel" / "plugins")
        _registry.add_plugin_dir(Path.cwd() / "plugins")
    return _registry
