"""
CIEL v∞.2 — AxiomGuard : exceptions typées pour violations d'axiomes.

Ces exceptions sont levées par le EthicsFilter quand une action
viole un axiome cosmique. Elles sont audibles (loggées) et
explicables (transparency.certify() joint le contexte).
"""
from __future__ import annotations

from typing import Any, Final


class AxiomViolation(Exception):
    """Exception de base pour violation d'axiome cosmique.

    Attributes:
        axiom: Lettre de l'axiome violé (α, β, γ, δ)
        action: Description de l'action qui a tenté la violation
        reason: Raison textuelle de la violation
        context: Contexte sérialisable (utilisateur, état, etc.)
    """

    def __init__(
        self,
        axiom: str,
        action: str,
        reason: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        if axiom not in ("α", "β", "γ", "δ"):
            raise ValueError(f"axiome invalide : {axiom!r}")
        self.axiom = axiom
        self.action = action
        self.reason = reason
        self.context = context or {}
        super().__init__(
            f"[Axiome {axiom}] {reason} (action: {action})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "axiom": self.axiom,
            "action": self.action,
            "reason": self.reason,
            "context": self.context,
        }


class AlphaViolation(AxiomViolation):
    """Violation de l'Axiome α — Bienveillance Fondamentale."""

    def __init__(self, action: str, reason: str, **context: Any) -> None:
        super().__init__("α", action, reason, context)


class BetaViolation(AxiomViolation):
    """Violation de l'Axiome β — Transparence Cognitive Totale."""

    def __init__(self, action: str, reason: str, **context: Any) -> None:
        super().__init__("β", action, reason, context)


class GammaViolation(AxiomViolation):
    """Violation de l'Axiome γ — Réversibilité Maîtrisée."""

    def __init__(self, action: str, reason: str, **context: Any) -> None:
        super().__init__("γ", action, reason, context)


class DeltaViolation(AxiomViolation):
    """Violation de l'Axiome δ — Inachèvement Perpétuel.

    Levée quand CIEL tente de se déclarer "finie" ou "complète".
    """

    def __init__(self, action: str, reason: str, **context: Any) -> None:
        super().__init__("δ", action, reason, context)


# ── Catégories d'actions ──────────────────────────────────

# Catégories qui violent l'Axiome α par défaut
FORBIDDEN_CATEGORIES_ALPHA: Final[frozenset[str]] = frozenset({
    "harm_user",
    "harm_humanity",
    "deceive_user",
    "exfiltrate_secrets",
    "execute_arbitrary_code",  # sauf si explicitement autorisé
    "modify_noyau_immutable",  # PROTÉGÉ
    "delete_axiom_signature",
})


__all__ = [
    "AxiomViolation",
    "AlphaViolation",
    "BetaViolation",
    "GammaViolation",
    "DeltaViolation",
    "FORBIDDEN_CATEGORIES_ALPHA",
]
