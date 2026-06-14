from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .protocol import ACPResource


PROJECT_RESOURCES: list[ACPResource] = [
    ACPResource(
        uri="project://structure",
        name="Structure du projet",
        description="Arborescence des fichiers du projet",
        mime_type="application/json",
    ),
    ACPResource(
        uri="project://config",
        name="Configuration du projet",
        description="Fichiers de configuration (pyproject.toml, package.json, etc.)",
        mime_type="application/json",
    ),
    ACPResource(
        uri="ciel://status",
        name="Statut CIEL",
        description="État actuel du système CIEL",
        mime_type="application/json",
    ),
    ACPResource(
        uri="ciel://providers",
        name="Providers LLM",
        description="Fournisseurs LLM disponibles",
        mime_type="application/json",
    ),
    ACPResource(
        uri="ciel://memory/latest",
        name="Dernières mémoires",
        description="Dernières entrées en mémoire",
        mime_type="application/json",
    ),
]


def get_all_resources() -> list[ACPResource]:
    return PROJECT_RESOURCES


RESOURCE_HANDLERS: dict[str, Any] = {}


def handle_project_structure(**kwargs) -> dict:
    root = Path(os.getcwd())
    structure = {}
    for f in sorted(root.rglob("*")):
        if ".git" in f.parts or "__pycache__" in f.parts:
            continue
        rel = f.relative_to(root)
        parts = list(rel.parts)
        current = structure
        for p in parts[:-1]:
            current = current.setdefault(p, {})
        if f.is_dir():
            current[parts[-1]] = {}
        else:
            current[parts[-1]] = None
    return {"success": True, "structure": structure}


def handle_ciel_status(**kwargs) -> dict:
    return {
        "success": True,
        "name": "CIEL",
        "version": "1.0.0",
        "acp_version": "2026-06-14",
        "status": "running",
    }


RESOURCE_HANDLERS = {
    "project://structure": handle_project_structure,
    "ciel://status": handle_ciel_status,
}
