from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .protocol import ACPTool, ACPScope


def _format_tool(name: str, description: str,
                 properties: dict, required: list[str] | None = None,
                 scope: ACPScope = ACPScope.PUBLIC,
                 categories: list[str] | None = None) -> ACPTool:
    return ACPTool(
        name=name,
        description=description,
        input_schema={
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
        scope=scope,
        categories=categories or [],
    )


CODE_TOOLS: list[ACPTool] = [
    _format_tool(
        "analyze_code",
        "Analyse un fichier source et retourne des suggestions d'amélioration, bugs, et patterns",
        {
            "file_path": {"type": "string", "description": "Chemin absolu du fichier à analyser"},
            "language": {"type": "string", "description": "Langage de programmation (optionnel)"},
        },
        required=["file_path"],
        categories=["code", "analysis"],
    ),
    _format_tool(
        "search_code",
        "Recherche du code dans le projet par pattern (grep, regex, nom de fichier)",
        {
            "pattern": {"type": "string", "description": "Pattern de recherche (regex supporté)"},
            "path": {"type": "string", "description": "Chemin racine de la recherche"},
            "file_pattern": {"type": "string", "description": "Filtre de fichiers (ex: *.py)"},
            "max_results": {"type": "number", "description": "Nombre max de résultats"},
        },
        required=["pattern"],
        categories=["code", "search"],
    ),
    _format_tool(
        "read_file",
        "Lit le contenu d'un fichier, avec support de plage de lignes",
        {
            "file_path": {"type": "string", "description": "Chemin absolu du fichier"},
            "offset": {"type": "number", "description": "Ligne de départ (optionnel)"},
            "limit": {"type": "number", "description": "Nombre de lignes à lire (optionnel)"},
        },
        required=["file_path"],
        categories=["code", "files"],
    ),
    _format_tool(
        "write_file",
        "Écrit ou remplace le contenu d'un fichier",
        {
            "file_path": {"type": "string", "description": "Chemin absolu du fichier"},
            "content": {"type": "string", "description": "Contenu à écrire"},
        },
        required=["file_path", "content"],
        scope=ACPScope.ADMIN,
        categories=["code", "files"],
    ),
    _format_tool(
        "list_directory",
        "Liste le contenu d'un répertoire",
        {
            "path": {"type": "string", "description": "Chemin absolu du répertoire"},
            "recursive": {"type": "boolean", "description": "Listage récursif"},
        },
        required=["path"],
        categories=["code", "files"],
    ),
    _format_tool(
        "run_command",
        "Exécute une commande shell dans l'environnement de travail",
        {
            "command": {"type": "string", "description": "Commande à exécuter"},
            "workdir": {"type": "string", "description": "Répertoire de travail"},
            "timeout": {"type": "number", "description": "Timeout en secondes"},
        },
        required=["command"],
        scope=ACPScope.ADMIN,
        categories=["system", "exec"],
    ),
    _format_tool(
        "diagnose_file",
        "Analyse un fichier pour détecter des problèmes de syntaxe, lint, et style",
        {
            "file_path": {"type": "string", "description": "Chemin absolu du fichier"},
            "checkers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Analyseurs à utiliser: syntax, lint, style, imports",
            },
        },
        required=["file_path"],
        categories=["code", "diagnostics"],
    ),
    _format_tool(
        "suggest_refactor",
        "Suggère des refactorisations pour un fichier ou une portion de code",
        {
            "file_path": {"type": "string", "description": "Chemin absolu du fichier"},
            "focus": {
                "type": "string",
                "description": "Focus: complexity, duplication, naming, structure, performance",
            },
        },
        required=["file_path"],
        categories=["code", "refactor"],
    ),
    _format_tool(
        "get_diagnostics",
        "Retourne les diagnostics actuels pour un fichier ouvert dans l'IDE",
        {
            "file_path": {"type": "string", "description": "Chemin absolu du fichier"},
        },
        required=["file_path"],
        categories=["code", "diagnostics"],
    ),
]


CIEL_TOOLS: list[ACPTool] = [
    _format_tool(
        "ciel_chat",
        "Envoie un message à CIEL et reçoit une réponse LLM",
        {
            "message": {"type": "string", "description": "Message à envoyer"},
            "provider": {"type": "string", "description": "Provider LLM"},
            "model": {"type": "string", "description": "Modèle LLM"},
            "session_id": {"type": "string", "description": "ID de session"},
        },
        required=["message"],
        categories=["ciel", "llm"],
    ),
    _format_tool(
        "ciel_memory_store",
        "Stocke une information dans la mémoire de CIEL",
        {
            "content": {"type": "string", "description": "Contenu à mémoriser"},
            "tags": {"type": "string", "description": "Tags séparés par des virgules"},
            "source": {"type": "string", "description": "Source de l'information"},
        },
        required=["content"],
        categories=["ciel", "memory"],
    ),
    _format_tool(
        "ciel_memory_query",
        "Interroge la mémoire de CIEL",
        {
            "query": {"type": "string", "description": "Requête de recherche"},
            "limit": {"type": "number", "description": "Nombre max de résultats"},
        },
        required=["query"],
        categories=["ciel", "memory"],
    ),
    _format_tool(
        "ciel_web_search",
        "Effectue une recherche web",
        {
            "query": {"type": "string", "description": "La recherche à effectuer"},
            "count": {"type": "number", "description": "Nombre de résultats"},
        },
        required=["query"],
        categories=["ciel", "web"],
    ),
    _format_tool(
        "ciel_brain_status",
        "État complet du cerveau CIEL (modules, cycles, uptime)",
        {},
        categories=["ciel", "system"],
    ),
    _format_tool(
        "ciel_workflows",
        "Liste les workflows CIEL et leur état",
        {},
        categories=["ciel", "workflow"],
    ),
    _format_tool(
        "ciel_agent_execute",
        "Exécute une tâche via le système agent CIEL",
        {
            "task": {"type": "string", "description": "Description de la tâche"},
        },
        required=["task"],
        categories=["ciel", "agent"],
    ),
    _format_tool(
        "ciel_providers",
        "Liste les fournisseurs LLM disponibles",
        {},
        categories=["ciel", "llm"],
    ),
]


def get_all_tools() -> list[ACPTool]:
    return CODE_TOOLS + CIEL_TOOLS


def get_tools_by_category(category: str) -> list[ACPTool]:
    return [t for t in get_all_tools() if category in t.categories]


# ── Tool Handlers ──

def handle_analyze_code(file_path: str, language: str | None = None,
                        **kwargs) -> dict:
    p = Path(file_path)
    if not p.exists():
        return {"success": False, "error": "File not found"}
    content = p.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    lang = language or p.suffix.lstrip(".") or "unknown"
    issues = []
    # Basic heuristics
    for i, line in enumerate(lines, 1):
        text = line.strip()
        if len(text) > 200:
            issues.append({"line": i, "severity": "warning",
                           "message": f"Line too long ({len(text)} chars > 200)"})
        if text.endswith(("    ", "\t")):
            issues.append({"line": i, "severity": "info",
                           "message": "Trailing whitespace"})
    return {
        "success": True,
        "file": file_path,
        "language": lang,
        "lines": len(lines),
        "size_bytes": p.stat().st_size,
        "issues": issues,
        "suggestion": "Analyse heuristique terminée" if not issues else f"{len(issues)} issues trouvés",
    }


def handle_search_code(pattern: str, path: str | None = None,
                       file_pattern: str | None = None,
                       max_results: int = 50, **kwargs) -> dict:
    search_root = path or os.getcwd()
    cmd = ["rg", "--json", "-n", pattern, str(search_root)]
    if file_pattern:
        cmd.extend(["-g", file_pattern])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        matches = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "match":
                    m = data["data"]
                    matches.append({
                        "path": m["path"]["text"],
                        "line": m["line_number"],
                        "content": m["lines"]["text"].strip()[:200],
                    })
            except (json.JSONDecodeError, KeyError):
                pass
        return {"success": True, "pattern": pattern,
                "results": matches[:max_results], "total": len(matches)}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Search timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "rg (ripgrep) not found. Install with: sudo pacman -S ripgrep"}


def handle_read_file(file_path: str, offset: int | None = None,
                     limit: int | None = None, **kwargs) -> dict:
    p = Path(file_path)
    if not p.exists():
        return {"success": False, "error": "File not found"}
    if not p.is_file():
        return {"success": False, "error": "Not a file"}
    content = p.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    start = (offset or 1) - 1
    end = start + (limit or len(lines))
    selected = lines[start:end]
    return {
        "success": True,
        "file": file_path,
        "total_lines": len(lines),
        "offset": start + 1,
        "content": "\n".join(selected),
    }


def handle_write_file(file_path: str, content: str, **kwargs) -> dict:
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"success": True, "file": file_path, "bytes": len(content.encode("utf-8"))}


def handle_list_directory(path: str, recursive: bool = False, **kwargs) -> dict:
    p = Path(path)
    if not p.exists():
        return {"success": False, "error": "Path not found"}
    if not p.is_dir():
        return {"success": False, "error": "Not a directory"}
    entries = []
    if recursive:
        for f in p.rglob("*"):
            entries.append({
                "name": f.name,
                "path": str(f.relative_to(p)),
                "type": "dir" if f.is_dir() else "file",
                "size": f.stat().st_size if f.is_file() else 0,
            })
    else:
        for f in p.iterdir():
            entries.append({
                "name": f.name,
                "path": f.name,
                "type": "dir" if f.is_dir() else "file",
                "size": f.stat().st_size if f.is_file() else 0,
            })
    return {"success": True, "path": path, "entries": entries, "count": len(entries)}


def handle_run_command(command: str, workdir: str | None = None,
                       timeout: int = 30, **kwargs) -> dict:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            cwd=workdir or os.getcwd(), timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:5000],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


TOOL_HANDLERS: dict[str, Any] = {
    "analyze_code": handle_analyze_code,
    "search_code": handle_search_code,
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "list_directory": handle_list_directory,
    "run_command": handle_run_command,
}
