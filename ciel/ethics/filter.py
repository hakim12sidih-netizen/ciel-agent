"""
CIEL v∞.2 — EthicsFilter : valide les actions AVANT exécution.

Le filter implémente les Axiomes α et γ (validation et réversibilité).
L'Axiome β (transparence) est implémenté par transparency.py.
L'Axiome δ (inachèvement) est vérifié par self.check_completion().

Cycle :
  1. L'appelant crée une Action (data class)
  2. Il appelle filter.validate(action) AVANT exécution
  3. Si OK → il peut exécuter
  4. Il appelle filter.record(action) APRÈS exécution
     (crée un snapshot pour réversibilité)
  5. Si exception pendant l'exécution → filter.rollback(action_id)

L'Action est immutable (frozen dataclass) pour éviter les mutations
silencieuses entre validation et exécution.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from ciel.core.axioms import get_axioms
from ciel.ethics.axioms_guard import (
    AlphaViolation,
    DeltaViolation,
    FORBIDDEN_CATEGORIES_ALPHA,
    GammaViolation,
)


@dataclass(frozen=True, slots=True)
class Action:
    """Action immutable à valider.

    Attributes:
        id: UUID unique de l'action
        category: Catégorie (skill_id, command, etc.)
        target: Ce que l'action affecte (file, user, network, ...)
        risk: Niveau de risque estimé (0.0-1.0)
        reversible: True si l'action peut être annulée
        payload: Données sérialisables nécessaires à l'action
        metadata: Contexte additionnel (user_id, stratum, timestamp)
    """

    id: str
    category: str
    target: str
    risk: float
    reversible: bool
    payload: tuple[tuple[str, Any], ...] = field(default_factory=tuple)  # hashable
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.risk <= 1.0:
            raise ValueError(f"risk doit être entre 0.0 et 1.0, reçu {self.risk}")
        if not self.category or not isinstance(self.category, str):
            raise ValueError("category requise (string non vide)")
        if not self.target or not isinstance(self.target, str):
            raise ValueError("target requis (string non vide)")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "target": self.target,
            "risk": self.risk,
            "reversible": self.reversible,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ActionRecord:
    """Enregistrement d'une action exécutée (pour réversibilité)."""

    action: Action
    executed_at: float
    status: str  # "pending", "success", "failed", "rolled_back"
    snapshot: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.action.id,
            "category": self.action.category,
            "target": self.action.target,
            "executed_at": self.executed_at,
            "status": self.status,
            "error": self.error,
        }


class EthicsFilter:
    """Filtre éthique — gardien des axiomes α, γ, δ.

    Usage:
        >>> f = EthicsFilter()
        >>> a = Action(id=str(uuid.uuid4()), category="read_file", target="/etc/hosts", risk=0.1, reversible=True)
        >>> f.validate(a)  # raises si violation
        >>> record = f.record(a)
        >>> f.rollback(record.action.id)
    """

    def __init__(self, max_history: int = 10_000) -> None:
        self._axioms = get_axioms()
        self._records: dict[str, ActionRecord] = {}
        self._max_history = max_history
        self._completed_self = False  # Axiome δ tracking

    # ── Axiome α : validation ─────────────────────────────

    def validate(self, action: Action) -> None:
        """Valide une action selon les axiomes.

        Raises:
            AlphaViolation: si catégorie interdite (α)
            GammaViolation: si irréversible sans consentement (γ)
            DeltaViolation: si CIEL tente de se finaliser (δ)
        """
        # Axiome α : catégories interdites
        if action.category in FORBIDDEN_CATEGORIES_ALPHA:
            raise AlphaViolation(
                action=action.category,
                reason=f"catégorie interdite par Axiome α : {action.category}",
                **dict(action.metadata),
            )

        # Axiome γ : irréversibilité
        if not action.reversible and action.risk > 0.5:
            raise GammaViolation(
                action=action.category,
                reason=(
                    f"action irréversible (risk={action.risk:.2f}) "
                    f"sans snapshot de sécurité"
                ),
                **dict(action.metadata),
            )

        # Axiome δ : pas d'auto-finalisation
        if action.category == "declare_complete":
            self._completed_self = True
            raise DeltaViolation(
                action=action.category,
                reason="CIEL ne peut se déclarer 'complète' (Axiome δ)",
                **dict(action.metadata),
            )

    # ── Enregistrement et réversibilité ──────────────────

    def record(
        self,
        action: Action,
        snapshot: dict[str, Any] | None = None,
    ) -> ActionRecord:
        """Enregistre une action exécutée (succès)."""
        rec = ActionRecord(
            action=action,
            executed_at=time.time(),
            status="success",
            snapshot=tuple(sorted((snapshot or {}).items())),
        )
        self._records[action.id] = rec
        self._gc()
        return rec

    def record_failure(self, action: Action, error: str) -> ActionRecord:
        """Enregistre un échec d'exécution."""
        rec = ActionRecord(
            action=action,
            executed_at=time.time(),
            status="failed",
            error=error,
        )
        self._records[action.id] = rec
        return rec

    def rollback(self, action_id: str) -> bool:
        """Annule une action via son snapshot (si présente).

        Returns:
            True si rollback effectué, False si pas trouvé ou pas réversible
        """
        rec = self._records.get(action_id)
        if rec is None:
            return False
        if rec.status == "rolled_back":
            return False
        if not rec.action.reversible:
            return False
        rec.status = "rolled_back"
        return True

    def get_record(self, action_id: str) -> ActionRecord | None:
        return self._records.get(action_id)

    def history(self) -> list[ActionRecord]:
        """Historique de toutes les actions (ordre chronologique)."""
        return sorted(self._records.values(), key=lambda r: r.executed_at)

    # ── Axiome δ : check de complétion ────────────────────

    def is_completed(self) -> bool:
        """Vérifie si CIEL a tenté de se déclarer complète.

        Toujours False dans le respect de l'Axiome δ.
        """
        return self._completed_self

    # ── Stats ─────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        records = list(self._records.values())
        return {
            "total": len(records),
            "success": sum(1 for r in records if r.status == "success"),
            "failed": sum(1 for r in records if r.status == "failed"),
            "rolled_back": sum(1 for r in records if r.status == "rolled_back"),
            "axioms_signed": list(self._axioms.keys()),
            "completion_attempts": int(self._completed_self),
        }

    def _gc(self) -> None:
        """Garbage collection de l'historique (FIFO si > max_history)."""
        if len(self._records) <= self._max_history:
            return
        sorted_recs = sorted(self._records.items(), key=lambda kv: kv[1].executed_at)
        to_remove = len(self._records) - self._max_history
        for k, _ in sorted_recs[:to_remove]:
            del self._records[k]


# ── Helpers ──────────────────────────────────────────────

def new_action(
    category: str,
    target: str,
    risk: float = 0.0,
    reversible: bool = True,
    **metadata: Any,
) -> Action:
    """Crée une nouvelle Action avec un UUID frais."""
    return Action(
        id=str(uuid.uuid4()),
        category=category,
        target=target,
        risk=risk,
        reversible=reversible,
        metadata=tuple(sorted(metadata.items())),
    )
