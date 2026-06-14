"""
Transverse — INTERFACES : 6 modes d'interaction avec l'extérieur.
  - cli, tui, voice, canvas, api_server, acp
"""
from __future__ import annotations

from ciel.interfaces.core import InterfacesEngine
from ciel.interfaces.capabilities import get_detector, TerminalCapabilityDetector
from ciel.interfaces.themes import get_theme, set_theme, list_themes

__all__ = [
    "InterfacesEngine", "cli",
    "get_detector", "TerminalCapabilityDetector",
    "get_theme", "set_theme", "list_themes",
]


def cli() -> None:
    from ciel.interfaces.cli import cli as _cli
    _cli()
