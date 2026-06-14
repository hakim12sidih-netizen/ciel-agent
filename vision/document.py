"""Document analysis — OCR, layout, structure extraction."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("ciel.vision.document")


def analyze_document(path: str) -> dict[str, Any]:
    """Analyse un document (image, PDF) pour en extraire le texte et la structure."""
    log.info("Document analysis stub: %s", path)
    return {"path": path, "text": "", "pages": 0, "error": "Not implemented"}


def extract_text(path: str) -> str:
    """Extrait le texte d'un document."""
    return ""


def detect_layout(path: str) -> list[dict[str, Any]]:
    """Détecte la mise en page d'un document."""
    return []
