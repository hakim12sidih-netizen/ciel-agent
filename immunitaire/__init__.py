"""
CIEL v∞.3 — Strate 4 : GARDIEN IMMUNITAIRE (AIS).

Système immunitaire artificiel pour CIEL :
- Self/Nonself discrimination
- Sélection négative (détection d'anomalies)
- Sélection clonale (optimisation immunitaire)
- Théorie du Danger (réponse adaptative)
- Mémoire immunitaire (réponse secondaire rapide)
- Tolérance centrale et périphérique
"""
from __future__ import annotations

from ciel.immunitaire.ais import (
    AIS,
    Antibody,
    ImmuneMemory,
    ImmuneState,
    ImmuneResponse,
)
from ciel.immunitaire.negative_selection import (
    NegativeSelector,
    DetectorSet,
)
from ciel.immunitaire.clonal_selection import (
    ClonalSelector,
    AffinityMaturation,
)
from ciel.immunitaire.danger_theory import (
    DangerSignal,
    SignalType,
    APC,
    DangerZone,
)

__all__ = [
    "AIS", "Antibody", "ImmuneMemory", "ImmuneState", "ImmuneResponse",
    "NegativeSelector", "DetectorSet",
    "ClonalSelector", "AffinityMaturation",
    "DangerSignal", "SignalType", "APC", "DangerZone",
]
