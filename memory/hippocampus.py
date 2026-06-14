"""Hippocampus — mémoire épisodique et consolidation."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("ciel.memory.hippocampus")


def store_episode(trace: dict[str, Any]) -> str:
    """Stocke un épisode dans l'hippocampe."""
    log.info("Hippocampus stub: store episode")
    return ""


def recall(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Rappelle des épisodes par similarité sémantique."""
    return []


def consolidate() -> int:
    """Consolide les épisodes court-terme vers le cortex."""
    return 0
