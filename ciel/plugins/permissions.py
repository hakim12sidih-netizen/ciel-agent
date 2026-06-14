"""
CIEL v∞.8 — Plugin Permission System.
Capability-based, runtime-enforced, with approval flow.
"""
from __future__ import annotations

import os
import sys
import re
from pathlib import Path
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Any


__all__ = [
    "Capability", "Permission", "PermissionSet",
    "PermissionDenied", "PermissionPolicy",
    "SandboxJail",
]


class Capability:
    FILESYSTEM_READ = "fs.read"
    FILESYSTEM_WRITE = "fs.write"
    FILESYSTEM_EXEC = "fs.exec"
    NETWORK_HTTP = "net.http"
    NETWORK_WS = "net.ws"
    NETWORK_LISTEN = "net.listen"
    PROCESS_SPAWN = "process.spawn"
    PROCESS_ENV = "process.env"
    CIEL_API = "ciel.api"
    CIEL_BRAIN = "ciel.brain"
    CIEL_CONFIG = "ciel.config"
    CIEL_PLUGINS = "ciel.plugins"
    CIEL_STORE = "ciel.store"
    UI_NOTIFY = "ui.notify"
    UI_INPUT = "ui.input"
    LLM_CHAT = "llm.chat"
    LLM_EMBED = "llm.embed"
    ALL = "*"


BUILTIN_CAPABILITY_GROUPS: dict[str, list[str]] = {
    "core": [
        Capability.CIEL_API, Capability.CIEL_BRAIN,
        Capability.CIEL_CONFIG, Capability.UI_NOTIFY,
    ],
    "network": [
        Capability.NETWORK_HTTP, Capability.NETWORK_WS,
    ],
    "filesystem.read": [Capability.FILESYSTEM_READ],
    "filesystem.write": [Capability.FILESYSTEM_WRITE],
    "llm": [Capability.LLM_CHAT, Capability.LLM_EMBED],
    "admin": [Capability.ALL],
    "storage": [Capability.CIEL_STORE],
}


@dataclass
class Permission:
    capability: str
    resource: str = "*"
    allow: bool = True

    def matches(self, capability: str, resource: str = "") -> bool:
        if self.capability == "*" or self.capability == capability:
            if self.resource == "*" or not resource or self.resource == resource:
                return True
            if _pattern_match(self.resource, resource):
                return True
        return False


class PermissionDecision(IntEnum):
    DENY = 0
    ALLOW = 1
    PROMPT = 2


@dataclass
class PermissionSet:
    permissions: list[Permission] = field(default_factory=list)

    def check(self, capability: str, resource: str = "") -> PermissionDecision:
        for p in reversed(self.permissions):
            if p.matches(capability, resource):
                return PermissionDecision.ALLOW if p.allow else PermissionDecision.DENY
        return PermissionDecision.PROMPT

    def allow(self, capability: str, resource: str = "*"):
        self.permissions.append(Permission(capability, resource, allow=True))

    def deny(self, capability: str, resource: str = "*"):
        self.permissions.append(Permission(capability, resource, allow=False))

    @classmethod
    def from_manifest_list(cls, caps: list[str]) -> PermissionSet:
        ps = cls()
        expanded: list[str] = []
        seen = set()
        for c in caps:
            if c in BUILTIN_CAPABILITY_GROUPS:
                for sub in BUILTIN_CAPABILITY_GROUPS[c]:
                    if sub not in seen:
                        expanded.append(sub)
                        seen.add(sub)
            else:
                if c not in seen:
                    expanded.append(c)
                    seen.add(c)
        for c in expanded:
            if c.startswith("-"):
                ps.deny(c[1:])
            else:
                ps.allow(c)
        return ps


class PermissionDenied(Exception):
    def __init__(self, capability: str, resource: str = "", plugin: str = ""):
        self.capability = capability
        self.resource = resource
        self.plugin = plugin
        msg = f"Permission denied: {capability}"
        if resource:
            msg += f" on {resource}"
        if plugin:
            msg += f" for plugin {plugin}"
        super().__init__(msg)


ApprovalCallback = Any


@dataclass
class PermissionPolicy:
    auto_approve: bool = False
    auto_deny: bool = False
    approval_callback: ApprovalCallback | None = None

    async def check(self, capability: str, resource: str,
                    plugin: str, permission_set: PermissionSet) -> bool:
        decision = permission_set.check(capability, resource)
        if decision == PermissionDecision.ALLOW:
            return True
        if decision == PermissionDecision.DENY or self.auto_deny:
            raise PermissionDenied(capability, resource, plugin)
        if self.auto_approve:
            return True
        if self.approval_callback:
            result = await self.approval_callback(capability, resource, plugin)
            if result:
                return True
        raise PermissionDenied(capability, resource, plugin)


def _pattern_match(pattern: str, value: str) -> bool:
    if pattern == value:
        return True
    regex = re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")
    return bool(re.fullmatch(regex, value))


class SandboxJail:
    def __init__(self, jail_root: Path | None = None):
        self.jail_root = jail_root or Path.home() / ".ciel" / "sandbox"
        self.jail_root.mkdir(parents=True, exist_ok=True)
        self._allowed_dirs: set[Path] = set()
        self._env_whitelist: set[str] = set()

    def allow_directory(self, path: str | Path):
        self._allowed_dirs.add(Path(path).expanduser().resolve())

    def allow_env(self, key: str):
        self._env_whitelist.add(key)

    def check_path(self, path: str | Path, write: bool = False) -> bool:
        resolved = Path(path).expanduser().resolve()
        for allowed in self._allowed_dirs:
            try:
                resolved.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False

    def get_restricted_globals(self, plugin_name: str = "") -> dict:
        jail = self

        class RestrictedPath:
            def __init__(self, inner_path: str):
                self._path = Path(inner_path).resolve()

            def __getattr__(self, name):
                if name in ("read_text", "write_text", "mkdir", "exists", "is_dir", "is_file", "iterdir", "glob", "rglob", "stat", "lstat", "resolve", "relative_to", "name", "stem", "suffix", "parent"):
                    return getattr(self._path, name)
                raise PermissionDenied(Capability.FILESYSTEM_READ, str(self._path))

        def safe_open(filepath, mode="r", **kwargs):
            resolved = Path(filepath).expanduser().resolve()
            if not jail.check_path(str(resolved), write="w" in mode or "a" in mode or "+" in mode):
                raise PermissionDenied(
                    Capability.FILESYSTEM_WRITE if "w" in mode or "a" in mode else Capability.FILESYSTEM_READ,
                    str(resolved), plugin_name
                )
            return builtins_open(filepath, mode, **kwargs)

        def safe_subprocess(cmd, **kwargs):
            raise PermissionDenied(Capability.PROCESS_SPAWN, str(cmd), plugin_name)

        import builtins
        builtins_open = builtins.open

        return {
            "open": safe_open,
            "os": os,
            "Path": Path,
            "__builtins__": {
                "print": print,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "any": any,
                "all": all,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "type": type,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "hasattr": hasattr,
                "getattr": getattr,
                "setattr": setattr,
                "delattr": delattr,
                "iter": iter,
                "next": next,
                "open": safe_open,
                "__import__": __import__,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "RuntimeError": RuntimeError,
                "StopIteration": StopIteration,
                "True": True,
                "False": False,
                "None": None,
            },
        }
