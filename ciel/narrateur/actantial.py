from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActantRole(Enum):
    """6 actants du modèle actantiel de Greimas."""
    SUJET = "sujet"           # Sujet (héros)
    OBJET = "objet"           # Objet de la quête
    DESTINATEUR = "destinateur"  # Émetteur de la quête
    DESTINATAIRE = "destinataire"  # Bénéficiaire
    ADJUVANT = "adjuvant"     # Allié
    OPPOSANT = "opposant"     # Opposant


AXES: dict[str, tuple[ActantRole, ActantRole, str]] = {
    "desir": (ActantRole.SUJET, ActantRole.OBJET, "axe du désir"),
    "communication": (ActantRole.DESTINATEUR, ActantRole.DESTINATAIRE, "axe de la communication"),
    "pouvoir": (ActantRole.ADJUVANT, ActantRole.OPPOSANT, "axe du pouvoir"),
}


class ActantialModel:
    """Modèle actantiel de Greimas — 6 actants, 3 axes."""

    def __init__(self) -> None:
        self.actants: dict[ActantRole, str] = {}

    def assign(self, role: ActantRole, character: str) -> None:
        self.actants[role] = character

    def get(self, role: ActantRole) -> str:
        return self.actants.get(role, "")

    def validate(self) -> bool:
        required = {ActantRole.SUJET, ActantRole.OBJET, ActantRole.DESTINATEUR, ActantRole.DESTINATAIRE}
        return required.issubset(self.actants.keys())

    def describe(self) -> dict[str, Any]:
        return {
            "sujet": self.actants.get(ActantRole.SUJET, ""),
            "objet": self.actants.get(ActantRole.OBJET, ""),
            "destinateur": self.actants.get(ActantRole.DESTINATEUR, ""),
            "destinataire": self.actants.get(ActantRole.DESTINATAIRE, ""),
            "adjuvant": self.actants.get(ActantRole.ADJUVANT, ""),
            "opposant": self.actants.get(ActantRole.OPPOSANT, ""),
            "complete": self.validate(),
        }

    def tension_field(self) -> list[tuple[str, str, str]]:
        return [
            (self.actants.get(role_a, "?"), self.actants.get(role_b, "?"), desc)
            for role_a, role_b, desc in AXES.values()
        ]
