"""
CIEL v∞.9 — Plugin Graph Engine.
Dependency graph, hook flow analysis, impact analysis, coupling metrics.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ciel.plugins.core import PluginManifest, PluginRegistry, get_registry


__all__ = [
    "PluginGraph", "DependencyGraph", "HookGraph",
    "ImpactAnalysis", "CouplingMetrics",
]


@dataclass
class DependencyGraph:
    nodes: list[str] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)

    def to_dot(self) -> str:
        lines = ["digraph PluginDeps {",
                 "  rankdir=LR;",
                 '  node [shape=box, style=rounded, fillcolor="#1a1a2e", fontcolor=white, color="#4a4a8a"];',
                 '  edge [color="#4a4e8a", arrowhead=vee];']
        for node in self.nodes:
            label = self.labels.get(node, node).replace('"', '\\"')
            lines.append(f'  "{node}" [label="{label}"];')
        for src, dst in self.edges:
            lines.append(f'  "{src}" -> "{dst}";')
        lines.append("}")
        return "\n".join(lines)

    def to_json(self) -> dict:
        return {
            "nodes": self.nodes,
            "edges": [{"source": s, "target": t} for s, t in self.edges],
            "labels": self.labels,
        }

    @property
    def has_cycles(self) -> bool:
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def _dfs(n: str) -> bool:
            visited.add(n)
            rec_stack.add(n)
            for src, dst in self.edges:
                if src == n:
                    if dst not in visited:
                        if _dfs(dst):
                            return True
                    elif dst in rec_stack:
                        return True
            rec_stack.discard(n)
            return False

        for n in self.nodes:
            if n not in visited:
                if _dfs(n):
                    return True
        return False

    def cycles(self) -> list[list[str]]:
        visited: set[str] = set()
        rec_stack: list[str] = []
        found: list[list[str]] = []

        def _dfs(n: str):
            visited.add(n)
            rec_stack.append(n)
            for src, dst in self.edges:
                if src == n:
                    if dst not in visited:
                        _dfs(dst)
                    elif dst in rec_stack:
                        cycle = rec_stack[rec_stack.index(dst):] + [dst]
                        found.append(list(cycle))
            rec_stack.pop()

        for n in self.nodes:
            if n not in visited:
                _dfs(n)
        return found


@dataclass
class HookGraph:
    hooks: dict[str, list[str]] = field(default_factory=dict)
    events: dict[str, list[str]] = field(default_factory=dict)

    def to_dot(self) -> str:
        lines = ["digraph HookFlow {",
                 "  rankdir=TB;",
                 '  node [shape=ellipse, style=filled, fillcolor="#16213e", fontcolor=white, color="#4a6fa5"];',
                 '  edge [color="#4a6fa5", arrowhead=vee];']
        for hook_name, plugins in self.hooks.items():
            label = hook_name.replace('"', '\\"')
            lines.append(f'  "{hook_name}" [label="{label}", shape=box];')
            for p in plugins:
                lines.append(f'  "{p}" -> "{hook_name}";')
        lines.append("}")
        return "\n".join(lines)

    def to_json(self) -> dict:
        return {
            "hooks": self.hooks,
            "events": self.events,
        }


class ImpactAnalysis:
    def __init__(self, registry: PluginRegistry | None = None):
        self.registry = registry or get_registry()

    def impact_of_removal(self, plugin_name: str) -> dict:
        dependents = self._find_dependents(plugin_name)
        hooks_affected = self._find_hooks_affected(plugin_name)
        return {
            "plugin": plugin_name,
            "direct_dependents": dependents,
            "transitive_impact": self._transitive_impact(plugin_name),
            "hooks_removed": len(hooks_affected),
            "hooks_list": hooks_affected,
            "breaking": len(dependents) > 0,
            "blast_radius": len(dependents) + sum(
                len(self._find_dependents(d)) for d in dependents
            ),
        }

    def _find_dependents(self, name: str) -> list[str]:
        dependents = []
        for plugin_name, manifest, loaded in self.registry.list():
            if name in (manifest.dependencies or []):
                dependents.append(plugin_name)
        return dependents

    def _find_hooks_affected(self, name: str) -> list[str]:
        affected = []
        for hook_name, entries in self.registry._hooks.items():
            for plugin_name, _, _ in entries:
                if plugin_name == name:
                    affected.append(hook_name)
        return affected

    def _transitive_impact(self, name: str) -> int:
        visited: set[str] = set()
        def _visit(n: str):
            if n in visited:
                return
            visited.add(n)
            for dep in self._find_dependents(n):
                _visit(dep)
        _visit(name)
        return len(visited) - 1

    def critical_path(self, from_plugin: str, to_plugin: str) -> list[str]:
        adj: dict[str, list[str]] = {}
        for name, manifest, loaded in self.registry.list():
            adj.setdefault(name, [])
            for dep in (manifest.dependencies or []):
                adj.setdefault(name, []).append(dep)

        visited: set[str] = set()
        path: list[str] = []
        result: list[list[str]] = []

        def _dfs(n: str, target: str, p: list[str]):
            if n in visited:
                return
            visited.add(n)
            p.append(n)
            if n == target:
                result.append(list(p))
            else:
                for neighbor in adj.get(n, []):
                    _dfs(neighbor, target, p)
            p.pop()
            visited.discard(n)

        _dfs(from_plugin, to_plugin, [])
        return result[0] if result else []


class CouplingMetrics:
    def __init__(self, registry: PluginRegistry | None = None):
        self.registry = registry or get_registry()

    def compute(self) -> dict:
        plugins = self.registry.list()
        n = len(plugins)
        if n == 0:
            return {"error": "no plugins"}

        total_deps = 0
        dep_counts: dict[str, int] = {}
        dependent_counts: dict[str, int] = {}
        fan_out: dict[str, int] = {}
        fan_in: dict[str, int] = {}

        name_map = {name: manifest for name, manifest, _ in plugins}

        for name, manifest, _ in plugins:
            deps = manifest.dependencies or []
            fan_out[name] = len(deps)
            total_deps += len(deps)
            for d in deps:
                dep_counts[name] = dep_counts.get(name, 0) + 1
                dependent_counts[d] = dependent_counts.get(d, 0) + 1
                fan_in[d] = fan_in.get(d, 0) + 1

        avg_deps = total_deps / n if n else 0
        max_fan_out = max(fan_out.values()) if fan_out else 0
        max_fan_in = max(fan_in.values()) if fan_in else 0

        coupling_coeffs = {}
        for name in name_map:
            fo = fan_out.get(name, 0)
            fi = fan_in.get(name, 0)
            coupling_coeffs[name] = round((fo + fi) / (2 * max(1, n - 1)), 4)

        return {
            "plugin_count": n,
            "total_dependencies": total_deps,
            "avg_dependencies_per_plugin": round(avg_deps, 2),
            "max_fan_out": max_fan_out,
            "max_fan_in": max_fan_in,
            "max_fan_out_plugin": max(fan_out, key=fan_out.get) if fan_out else "",
            "max_fan_in_plugin": max(fan_in, key=fan_in.get) if fan_in else "",
            "coupling_coefficients": coupling_coeffs,
            "avg_coupling": round(sum(coupling_coeffs.values()) / len(coupling_coeffs), 4) if coupling_coeffs else 0,
        }

    def dead_plugins(self) -> list[str]:
        dead = []
        for name, manifest, loaded in self.registry.list():
            has_hooks = any(
                name == pn for hooks in self.registry._hooks.values()
                for pn, _, _ in hooks
            )
            has_events = any(
                name == pn for events in self.registry._events.values()
                for pn, _, _ in events
            )
            if not has_hooks and not has_events:
                dead.append(name)
        return dead


class PluginGraph:
    def __init__(self, registry: PluginRegistry | None = None):
        self.registry = registry or get_registry()
        self.impact = ImpactAnalysis(registry)
        self.metrics = CouplingMetrics(registry)

    def dependency_graph(self) -> DependencyGraph:
        g = DependencyGraph()
        for name, manifest, loaded in self.registry.list():
            g.nodes.append(name)
            g.labels[name] = f"{name} v{manifest.version}"
            for dep in (manifest.dependencies or []):
                g.edges.append((name, dep))
        return g

    def hook_graph(self) -> HookGraph:
        g = HookGraph()
        for hook_name, entries in self.registry._hooks.items():
            g.hooks[hook_name] = [pn for pn, _, _ in entries]
        for event_name, entries in self.registry._events.items():
            g.events[event_name] = [pn for pn, _, _ in entries]
        return g

    def full_report(self) -> dict:
        deps = self.dependency_graph()
        hooks = self.hook_graph()
        metrics = self.metrics.compute()
        return {
            "dependency_graph": deps.to_json(),
            "hook_graph": hooks.to_json(),
            "metrics": metrics,
            "has_cycles": deps.has_cycles,
            "cycles": deps.cycles() if deps.has_cycles else [],
            "dead_plugins": self.metrics.dead_plugins(),
            "dot_deps": deps.to_dot(),
            "dot_hooks": hooks.to_dot(),
        }
