"""
CIEL v∞.3 — VSM : Modèle du Système Viable (Stafford Beer).

5 sous-systèmes interconnectés :
  S1 — Implémentation (Implementation)
  S2 — Coordination
  S3 — Contrôle (Autonomie)
  S3* — Audit/Monitoring
  S4 — Intelligence (R&D, prospective)
  S5 — Identité (Politique/Éthique)

Loi de la diversité : seule la diversité peut absorber la diversité.
"""
from __future__ import annotations

from ciel.vsm.core import (
    ViableSystemModel,
    Subsystem,
    VSMState,
    VarietyEngine,
)

__all__ = [
    "ViableSystemModel", "Subsystem", "VSMState", "VarietyEngine",
]
