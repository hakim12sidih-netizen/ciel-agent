"""Registre des 11 phases d'entraînement CIEL SAGA 1."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ciel.saga.config import SagaConfig, PhaseConfig


@dataclass
class PhaseFunc:
    name: str
    fn: Callable
    description: str = ""


PHASE_REGISTRY: dict[str, Callable] = {}


def register_phase(name: str, desc: str = ""):
    """Décorateur pour enregistrer une phase dans PHASE_REGISTRY."""
    def decorator(fn):
        PHASE_REGISTRY[name] = fn
        return fn
    return decorator
