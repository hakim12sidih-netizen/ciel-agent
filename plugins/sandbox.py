"""
CIEL v∞.8 — Plugin Sandbox.
Restricted execution for untrusted plugin code.
"""
from __future__ import annotations

import ast
import sys
import traceback
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.plugins.permissions import (
    PermissionSet, PermissionPolicy, SandboxJail, Capability,
    PermissionDenied,
)


__all__ = [
    "PluginSandbox", "SandboxedPlugin", "SandboxResult",
]


SANDBOX_TIMEOUT = 10
SANDBOX_MAX_OUTPUT = 100_000
SANDBOX_MAX_STATEMENTS = 1000


@dataclass
class SandboxResult:
    success: bool = False
    output: Any = None
    error: str = ""
    duration_ms: float = 0.0
    stdout: str = ""


_BLOCKED_AST_NODES = {
    ast.Import: "import not allowed in sandbox",
    ast.ImportFrom: "import not allowed in sandbox",
    ast.Global: "global not allowed",
    ast.Nonlocal: "nonlocal not allowed",
    ast.Delete: "del not allowed",
}

if hasattr(ast, "Exec"):
    _BLOCKED_AST_NODES[ast.Exec] = "exec not allowed"


class _SandboxVisitor(ast.NodeVisitor):
    def __init__(self):
        self._node_count = 0

    def visit(self, node):
        self._node_count += 1
        if self._node_count > SANDBOX_MAX_STATEMENTS:
            raise PermissionDenied(Capability.ALL, "sandbox", "Too many statements")
        node_type = type(node)
        if node_type in _BLOCKED_AST_NODES:
            raise PermissionDenied(Capability.ALL, "sandbox", _BLOCKED_AST_NODES[node_type])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "subprocess":
                        raise PermissionDenied(Capability.PROCESS_SPAWN, "sandbox", "subprocess not allowed")
        self.generic_visit(node)


class PluginSandbox:
    def __init__(self):
        self.jail = SandboxJail()
        self.jail.allow_directory(Path.home() / ".ciel")
        self._results: list[SandboxResult] = []

    def set_permissions(self, permission_set: PermissionSet):
        self._permissions = permission_set

    def execute(self, code: str, plugin_name: str = "",
                timeout: int = SANDBOX_TIMEOUT) -> SandboxResult:
        start = time.time()
        result = SandboxResult()

        try:
            tree = ast.parse(code)
            visitor = _SandboxVisitor()
            visitor.visit(tree)

            restricted_globals = self.jail.get_restricted_globals(plugin_name)
            restricted_globals["__name__"] = f"__sandbox__{plugin_name or 'anon'}__"

            output_capture: list[str] = []

            def _safe_print(*args, **kwargs):
                text = " ".join(str(a) for a in args)
                output_capture.append(text)
                real_print(*args, **kwargs)

            import builtins
            real_print = builtins.print
            restricted_globals["__builtins__"]["print"] = _safe_print

            compiled = compile(tree, f"<sandbox:{plugin_name}>", "exec")

            local_ns: dict[str, Any] = {}

            exec(compiled, restricted_globals, local_ns)

            result.success = True
            result.stdout = "\n".join(output_capture)

            if "_return" in local_ns:
                result.output = local_ns["_return"]
            elif output_capture:
                result.output = output_capture[-1]

        except PermissionDenied as e:
            result.error = str(e)
        except SyntaxError as e:
            result.error = f"SyntaxError: {e}"
        except Exception as e:
            result.error = f"{type(e).__name__}: {e}"
            tb = traceback.format_exc()
            if result.error:
                pass

        result.duration_ms = (time.time() - start) * 1000
        self._results.append(result)
        return result

    def get_stats(self) -> dict:
        return {
            "executions": len(self._results),
            "last_success": self._results[-1].success if self._results else None,
        }


class SandboxedPlugin:
    def __init__(self, plugin_name: str, code: str,
                 permission_set: PermissionSet | None = None):
        self.plugin_name = plugin_name
        self.code = code
        self.sandbox = PluginSandbox()
        self.permission_set = permission_set or PermissionSet()

    def run(self, func_name: str = "", **kwargs) -> SandboxResult:
        wrapped = self.code
        if func_name:
            wrapped = f"{self.code}\n_return = {func_name}(**{kwargs!r})"
        elif kwargs:
            wrapped = f"{self.code}\n_return = {kwargs}"
        return self.sandbox.execute(wrapped, self.plugin_name)
