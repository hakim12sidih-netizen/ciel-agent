from __future__ import annotations

import ast
import importlib
import inspect
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

log = logging.getLogger("ciel.docs.generator")

MODULE_DOCS: dict[str, str] = {
    "mesh": "Réseau distribué CIEL (gRPC+QUIC)",
    "acp": "Agent Communication Protocol — intégration IDE et agents",
    "interfaces": "Interfaces : terminal backends, capabilities, thèmes",
}


def extract_module_info(module_name: str) -> dict[str, Any]:
    mod = importlib.import_module(module_name)
    info: dict[str, Any] = {
        "name": module_name,
        "docstring": (mod.__doc__ or "").strip(),
        "exports": getattr(mod, "__all__", []),
        "classes": [],
        "functions": [],
        "constants": [],
    }

    for name, obj in inspect.getmembers(mod):
        if name.startswith("_"):
            continue

        if inspect.isclass(obj):
            cls_info = {"name": name, "docstring": _clean_doc(obj.__doc__), "methods": []}
            for mname, mobj in inspect.getmembers(obj, predicate=inspect.isfunction):
                if mname.startswith("_") and mname not in ("__init__",):
                    continue
                sig = _format_sig(mobj)
                cls_info["methods"].append({
                    "name": mname,
                    "signature": sig,
                    "docstring": _clean_doc(mobj.__doc__),
                    "abstract": getattr(mobj, "__isabstractmethod__", False),
                })
            info["classes"].append(cls_info)

        elif inspect.isfunction(obj):
            sig = _format_sig(obj)
            info["functions"].append({
                "name": name,
                "signature": sig,
                "docstring": _clean_doc(obj.__doc__),
            })

        elif isinstance(obj, (str, int, float, bool, list, dict, tuple)):
            info["constants"].append({
                "name": name,
                "type": type(obj).__name__,
                "repr": repr(obj)[:120],
            })

    return info


def _clean_doc(doc: str | None) -> str:
    if not doc:
        return ""
    return "\n".join(line.strip() for line in doc.strip().split("\n"))


def _format_sig(obj) -> str:
    try:
        sig = inspect.signature(obj)
        params = []
        for p in sig.parameters.values():
            if p.name == "self":
                continue
            parts = [p.name]
            if p.annotation is not inspect.Parameter.empty:
                ann = _format_annotation(p.annotation)
                parts.append(f": {ann}")
            if p.default is not inspect.Parameter.empty:
                parts.append(f" = {p.default!r}")
            params.append("".join(parts))
        return f"({', '.join(params)})"
    except (ValueError, TypeError):
        return "(...)"


def _format_annotation(ann) -> str:
    if hasattr(ann, "__name__"):
        return ann.__name__
    return str(ann).replace("typing.", "")


def generate_module_doc(module_name: str, title: str | None = None) -> str:
    info = extract_module_info(module_name)
    lines: list[str] = []

    display_name = title or module_name
    lines.append(f"# `{module_name}` — {display_name}")
    lines.append("")

    if info["docstring"]:
        lines.append(info["docstring"])
        lines.append("")
        lines.append("---")
        lines.append("")

    if info["constants"]:
        lines.append("## Constantes")
        lines.append("")
        for c in info["constants"]:
            lines.append(f"- **`{c['name']}`** (`{c['type']}`) — `{c['repr']}`")
        lines.append("")

    if info["classes"]:
        lines.append("## Classes")
        lines.append("")
        for cls in info["classes"]:
            lines.append(f"### `{cls['name']}`")
            if cls["docstring"]:
                lines.append("")
                lines.append(cls["docstring"])
            lines.append("")

            if cls["methods"]:
                lines.append("**Méthodes :**")
                lines.append("")
                for m in cls["methods"]:
                    abstract = " *(abstract)*" if m["abstract"] else ""
                    lines.append(f"- **`{m['name']}{m['signature']}`**{abstract}")
                    if m["docstring"]:
                        lines.append(f"  - {m['docstring'].split(chr(10))[0]}")
                lines.append("")

    if info["functions"]:
        lines.append("## Fonctions")
        lines.append("")
        for fn in info["functions"]:
            lines.append(f"### `{fn['name']}{fn['signature']}`")
            if fn["docstring"]:
                lines.append("")
                lines.append(fn["docstring"])
            lines.append("")

    if info["exports"]:
        lines.append("## Exportations")
        lines.append("")
        for exp in info["exports"]:
            lines.append(f"- `{exp}`")
        lines.append("")

    return "\n".join(lines)


def generate_all(output_dir: str = "docs") -> dict[str, str]:
    modules = {
        "mesh": ("ciel.mesh", "Module Mesh Distribué (gRPC+QUIC)"),
        "acp": ("ciel.acp", "Agent Communication Protocol"),
        "interfaces": ("ciel.interfaces", "Interfaces — Backends, Capabilities, Thèmes"),
    }

    sub_modules = {
        "mesh": [
            ("ciel.mesh.identity", "Identity (Ed25519)"),
            ("ciel.mesh.discovery", "Peer Discovery"),
            ("ciel.mesh.transport", "Transport gRPC"),
            ("ciel.mesh.node", "Mesh Node"),
            ("ciel.mesh.swarm_adapter", "Swarm Adapter"),
            ("ciel.mesh.gateway_bridge", "Gateway Bridge"),
            ("ciel.mesh.cli", "CLI mesh"),
        ],
        "acp": [
            ("ciel.acp.protocol", "Protocol (JSON-RPC 2.0)"),
            ("ciel.acp.tools", "Outils ACP"),
            ("ciel.acp.resources", "Ressources ACP"),
            ("ciel.acp.server", "Serveur WebSocket/stdio"),
            ("ciel.acp.ide", "VS Code / Cursor Integration"),
            ("ciel.acp.cli", "CLI ACP"),
        ],
        "interfaces": [
            ("ciel.interfaces.capabilities", "Terminal Capabilities"),
            ("ciel.interfaces.themes", "Thèmes"),
            ("ciel.interfaces.backends.base", "Base ABC"),
            ("ciel.interfaces.backends.registry", "Registry"),
            ("ciel.interfaces.backends.textual_backend", "Backend Textual TUI"),
            ("ciel.interfaces.backends.web_backend", "Backend Web"),
            ("ciel.interfaces.backends.voice_backend", "Backend Voice"),
            ("ciel.interfaces.backends.cli", "CLI Terminal & Theme"),
        ],
    }

    generated: dict[str, str] = {}
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for key, (mod, title) in modules.items():
        content = generate_module_doc(mod, title)
        filepath = out / f"{key}.md"
        filepath.write_text(content, encoding="utf-8")
        generated[f"{key}.md"] = content
        log.info("Generated docs/%s.md", key)

        # sub-modules
        sub_dir = out / key
        sub_dir.mkdir(parents=True, exist_ok=True)
        for sub_mod, sub_title in sub_modules.get(key, []):
            try:
                sub_content = generate_module_doc(sub_mod, sub_title)
                sub_name = sub_mod.split(".")[-1]
                sub_file = sub_dir / f"{sub_name}.md"
                sub_file.write_text(sub_content, encoding="utf-8")
                generated[f"{key}/{sub_name}.md"] = sub_content
                log.info("Generated docs/%s/%s.md", key, sub_name)
            except Exception as e:
                log.warning("Skipping %s: %s", sub_mod, e)

    # index
    index_lines = [
        "# CIEL — Documentation",
        "",
        "Documentation générée automatiquement.",
        "",
        "## Modules",
        "",
    ]
    for key, (_, title) in modules.items():
        index_lines.append(f"- [`{key}`]({key}.md) — {title}")
    for key, (_, title) in modules.items():
        index_lines.append(f"  - [Sous-modules]({key}/)")
    index_lines.append("")
    index_lines.append("---")
    index_lines.append(f"*Généré le {_now()}*")
    index_lines.append("")

    index_path = out / "index.md"
    index_path.write_text("\n".join(index_lines), encoding="utf-8")
    generated["index.md"] = "\n".join(index_lines)
    log.info("Generated docs/index.md")

    return generated


def _now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_docs(output_dir: str = "docs") -> None:
    generate_all(output_dir)
    print(f"Documentation générée dans {output_dir}/")
    for p in sorted(Path(output_dir).rglob("*.md")):
        print(f"  {p.relative_to(Path(output_dir).parent)}")
