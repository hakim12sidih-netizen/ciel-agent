"""
Backends d'interface CIEL.

Chaque backend implémente `InterfaceBackend` (ABC) et
s'enregistre via `registry.register()`.
"""
from __future__ import annotations

from .base import InterfaceBackend, BackendSession
from .registry import register, get, get_all, get_available, load_default_backends

__all__ = [
    "InterfaceBackend", "BackendSession",
    "register", "get", "get_all", "get_available", "load_default_backends",
]
