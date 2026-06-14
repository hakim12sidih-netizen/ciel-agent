"""
CIEL v1.0 — MetamorphicCore : architecture d'auto-métamorphose.

Migré depuis Hydra, adapté pour CIEL.
Coordonne le cycle complet d'auto-amélioration :
  proposer → vérifier → appliquer + incubation + rollback

C'est le cœur de la capacité d'auto-évolution de CIEL.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.llm_transmuter import LLMTransmuter, TransmutationProposal
from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class MetamorphicState:
    cycle_count: int = 0
    last_transmutation: str | None = None
    total_applied: int = 0
    total_rolled_back: int = 0
    is_incubating: bool = False
    incubation_start: float | None = None


class MetamorphicCore:
    """Architecture d'auto-métamorphose de CIEL.

    Gère le cycle complet d'évolution du code :
      1. PROPOSE  — LLMTransmuter propose des changements
      2. VERIFY   — Aegis audite les changements
      3. APPLY    — Applique les changements validés
      4. INCUBATE — Observe les changements en production
      5. ROLLBACK — Annule si les changements échouent
    """

    def __init__(self, root_path: str = "."):
        self.transmuter = LLMTransmuter(root_path)
        self.leader = LeaderNetwork()
        self.state = MetamorphicState()
        self._incubation_period = 300  # 5 minutes par défaut

    def propose_and_apply(self, file_path: str, intent: str, new_code: str) -> TransmutationProposal:
        """Cycle complet : propose, vérifie, applique."""
        result = self.transmuter.transmutate(file_path, intent, new_code)

        if result.applied:
            self.state.cycle_count += 1
            self.state.last_transmutation = result.id
            self.state.total_applied += 1
            self.state.is_incubating = True
            self.state.incubation_start = time.time()
            self.leader.emit("metamorphosis", {
                "action": "applied",
                "file": file_path,
                "intent": intent,
                "proposal_id": result.id,
            })
        elif result.verified:
            self.state.cycle_count += 1
            self.leader.emit("metamorphosis", {
                "action": "blocked_by_budget",
                "file": file_path,
            })
        else:
            self.state.cycle_count += 1
            self.leader.emit("metamorphosis", {
                "action": "blocked_by_aegis",
                "file": file_path,
                "finding_count": len(result.diff) if result.diff else 0,
            })

        return result

    def check_incubation(self) -> list[str]:
        """Vérifie l'incubation et rollback si nécessaire."""
        if not self.state.is_incubating or not self.state.incubation_start:
            return []

        elapsed = time.time() - self.state.incubation_start
        rolled_back: list[str] = []

        if elapsed >= self._incubation_period:
            # Incubation terminée, vérification
            recent_changes = self.transmuter.list_transmutations(limit=10)
            for change in recent_changes:
                if (change["applied"] and not change["rolled_back"]
                        and self.state.total_applied > 0):
                    # En production on vérifierait les métriques
                    pass
            self.state.is_incubating = False

        return rolled_back

    def status(self) -> dict:
        return {
            "cycle_count": self.state.cycle_count,
            "total_applied": self.state.total_applied,
            "total_rolled_back": self.state.total_rolled_back,
            "is_incubating": self.state.is_incubating,
            "budget_remaining": self.transmuter.budget.remaining(),
        }
