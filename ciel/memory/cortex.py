"""Cortex — mémoire sémantique et connaissances structurées."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("ciel.memory.cortex")


def store_knowledge(key: str, value: Any, tags: list[str] | None = None) -> bool:
    """Stocke une connaissance dans le cortex."""
    log.info("Cortex stub: store %s", key)
    return True


def query(concept: str) -> list[dict[str, Any]]:
    """Interroge le cortex sur un concept."""
    return []


def forget(concept: str) -> bool:
    """Supprime une connaissance du cortex."""
    return False


def stats() -> dict[str, int]:
    return {"total": 0, "tags": 0}
