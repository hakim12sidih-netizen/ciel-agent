"""
Transverse — INTERFACES : 6 modes d'interaction avec l'extérieur.

  - cli        : CLI en ligne de commande (Typer/Click)
  - tui        : Terminal UI (Textual) — absorption Hermes Ink
  - voice      : Voix synthétique personnalisée — absorption OpenClaw
  - canvas     : Interface graphique 2D/3D — absorption OpenClaw
  - api_server : FastAPI + WebSocket
  - acp        : Agent Client Protocol (VS Code, Zed) — absorption Hermes

Phase 0 : stubs alignés v∞.2. Implémentation Phase 1-3.
"""
from __future__ import annotations
