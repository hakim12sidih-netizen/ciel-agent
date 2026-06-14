"""Symbolic math engine."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("ciel.math.symbolic")


def simplify(expression: str) -> str:
    """Simplifie une expression mathématique symbolique."""
    log.info("Symbolic stub: simplify %s", expression)
    return expression


def differentiate(expression: str, variable: str = "x") -> str:
    """Dérive une expression."""
    return ""


def integrate(expression: str, variable: str = "x") -> str:
    """Intègre une expression."""
    return ""


def solve(equation: str, variable: str = "x") -> list[str]:
    """Résout une équation symbolique."""
    return []
