"""
CIEL v1.0 — SANDBOX. Exécution sécurisée de code — backends multiples.
"""
from __future__ import annotations
from ciel.sandbox.core import (
    SandboxEngine, SandboxResult, SandboxPolicy,
    DockerBackend, LocalBackend, SSHBackend,
    get_backend, detect_best_backend, BACKENDS, LANGUAGES,
)

__all__ = [
    "SandboxEngine", "SandboxResult", "SandboxPolicy",
    "DockerBackend", "LocalBackend", "SSHBackend",
    "get_backend", "detect_best_backend", "BACKENDS", "LANGUAGES",
]
