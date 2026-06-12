"""
Transverse — INTERFACES : 6 modes d'interaction avec l'extérieur.
  - cli, tui, voice, canvas, api_server, acp
"""
from __future__ import annotations

from ciel.interfaces.core import InterfacesEngine

__all__ = ["InterfacesEngine", "cli"]


def cli() -> None:
    from ciel.interfaces.cli import cli as _cli
    _cli()
