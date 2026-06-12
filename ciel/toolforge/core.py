"""
CIEL v∞.8 — TOOLFORGE ENGINE.
CIEL forge ses propres outils — création, registry, découverte.

Concept : CIEL peut créer dynamiquement des outils (scripts Python,
fonctions, wrappers API) et les enregistrer dans un registre.
Les outils sont découverts par nom, description ou tag.
Forge invoque le meilleur outil pour chaque problème.
Cycle : besoin → design → forge → test → register → use → retire.
"""
from __future__ import annotations

import importlib.util
import inspect
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class ForgedTool:
    id: str
    name: str
    description: str
    code: str = ""
    fn: Callable | None = None
    tags: list[str] = field(default_factory=list)
    author: str = "ciel"
    version: int = 1
    usage_count: int = 0
    success_rate: float = 1.0
    created_at: float = 0.0
    is_active: bool = True

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "desc": self.description[:60],
                "tags": self.tags, "version": self.version,
                "uses": self.usage_count,
                "success": round(self.success_rate, 2),
                "active": self.is_active}


TOOL_TEMPLATES = {
    "python_function": """
def {name}({params}):
    \"\"\"{description}\"\"\"
    {body}
    return result
""",
    "web_search": """
import httpx
def {name}(query: str) -> dict:
    \"\"\"Search the web.\"\"\"
    r = httpx.get("https://api.duckduckgo.com", params={{"q": query, "format": "json"}})
    return r.json()
""",
    "file_read": """
def {name}(path: str) -> str:
    \"\"\"Read a file.\"\"\"
    with open(path) as f:
        return f.read()
""",
    "math_eval": """
import math
def {name}(expression: str) -> float:
    \"\"\"Evaluate a math expression safely.\"\"\"
    allowed = {{"abs": abs, "math": math, "max": max, "min": min, "round": round, "sum": sum}}
    return eval(expression, {{"__builtins__": {{}}}}, allowed)
""",
}


class ToolForgeEngine:
    """Moteur de forge d'outils — CIEL crée ses propres outils.

    Registry global, forge à la volée, découverte intelligente.
    Les outils sont des callables enregistrés avec métadonnées.
    """

    def __init__(self):
        self.tools: dict[str, ForgedTool] = {}
        self.network = LeaderNetwork()
        self._init_builtins()

    def _init_builtins(self):
        builtins = [
            ("read_file", "Lire le contenu d'un fichier",
             ["file", "io"], "file_read"),
            ("web_search", "Rechercher sur le web",
             ["web", "search"], "web_search"),
            ("math_calc", "Évaluer une expression mathématique",
             ["math", "calc"], "math_eval"),
        ]
        for name, desc, tags, template_key in builtins:
            self.forge(name, desc, tags, template_key)

    def forge(self, name: str, description: str,
              tags: list[str] | None = None,
              template_key: str = "python_function",
              params: str = "*args, **kwargs",
              body: str = "result = None") -> ForgedTool:
        template = TOOL_TEMPLATES.get(template_key, TOOL_TEMPLATES["python_function"])
        code = template.format(name=name, description=description,
                               params=params, body=textwrap.indent(body, "    "))
        fn = self._compile(name, code, description)
        tool = ForgedTool(
            id=f"TOL-{uuid.uuid4().hex[:12]}",
            name=name, description=description,
            code=code, fn=fn, tags=tags or [],
            created_at=time.time(),
        )
        self.tools[tool.id] = tool
        self.network.emit("tool.forged", {"name": name})
        return tool

    def _compile(self, name: str, code: str, desc: str) -> Callable | None:
        try:
            globs = {"__builtins__": __builtins__}
            exec(code, globs)
            return globs.get(name)
        except Exception:
            return None

    def find(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for tool in self.tools.values():
            if not tool.is_active:
                continue
            if q in tool.name.lower() or q in tool.description.lower():
                results.append(tool.to_dict())
            elif any(q in t.lower() for t in tool.tags):
                results.append(tool.to_dict())
        return results[:10]

    def run(self, tool_id: str, *args, **kwargs) -> Any:
        tool = self.tools.get(tool_id)
        if not tool or not tool.fn:
            return {"error": "tool not found"}
        try:
            result = tool.fn(*args, **kwargs)
            tool.usage_count += 1
            return {"success": True, "result": result}
        except Exception as e:
            tool.success_rate = max(0.0, tool.success_rate - 0.1)
            return {"success": False, "error": str(e)}

    def retire(self, tool_id: str) -> bool:
        tool = self.tools.get(tool_id)
        if not tool:
            return False
        tool.is_active = False
        return True

    def suggest_tool(self, problem: str) -> dict | None:
        candidates = self.find(problem)
        if not candidates:
            return None
        best = max(candidates, key=lambda c: c.get("success", 1.0))
        return best

    def get_stats(self) -> dict:
        return {
            "tools": len(self.tools),
            "active": sum(1 for t in self.tools.values() if t.is_active),
            "total_uses": sum(t.usage_count for t in self.tools.values()),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "forge":
            t = self.forge(
                input_data.get("name", "custom_tool"),
                input_data.get("description", ""),
                input_data.get("tags"),
                input_data.get("template", "python_function"),
                input_data.get("params", "*args, **kwargs"),
                input_data.get("body", "result = None"),
            )
            return {"status": "ok", "tool": t.to_dict()}
        elif action == "find":
            return {"status": "ok",
                    "tools": self.find(input_data.get("query", ""))}
        elif action == "run":
            return {"status": "ok",
                    "result": self.run(
                        input_data.get("tool_id", ""),
                        *input_data.get("args", []),
                        **input_data.get("kwargs", {}),
                    )}
        elif action == "retire":
            ok = self.retire(input_data.get("tool_id", ""))
            return {"status": "ok" if ok else "error"}
        elif action == "suggest":
            s = self.suggest_tool(input_data.get("problem", ""))
            return {"status": "ok", "suggestion": s}
        return {"status": "ok", "tools": len(self.tools)}
