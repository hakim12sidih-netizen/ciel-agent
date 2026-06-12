"""
CIEL v1.0 — TransmutationBudget : limiteur de taux pour auto-réécriture.

Migré depuis Hydra, adapté pour CIEL.
Empêche les modifications de code trop fréquentes.
  - Limite par heure
  - Limite par jour
  - Permet les whitelist
"""
from __future__ import annotations

import time
from collections import defaultdict


class TransmutationBudget:
    """Budget de transmutation pour limiter l'auto-réécriture.

    Protège contre les boucles d'auto-amélioration incontrôlées.
    """

    def __init__(self, hourly_budget: int = 5, daily_budget: int = 50):
        self.hourly_budget = hourly_budget
        self.daily_budget = daily_budget
        self._usage_hourly: list[tuple[str, float]] = []
        self._usage_daily: list[tuple[str, float]] = []
        self._whitelist: set[str] = set()

    def whitelist(self, proposal_id: str) -> None:
        self._whitelist.add(proposal_id)

    def consume(self, proposal_id: str) -> bool:
        if proposal_id in self._whitelist:
            return True

        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400

        # Nettoie les entrées obsolètes
        self._usage_hourly = [(pid, ts) for pid, ts in self._usage_hourly if ts > hour_ago]
        self._usage_daily = [(pid, ts) for pid, ts in self._usage_daily if ts > day_ago]

        if len(self._usage_hourly) >= self.hourly_budget:
            return False
        if len(self._usage_daily) >= self.daily_budget:
            return False

        self._usage_hourly.append((proposal_id, now))
        self._usage_daily.append((proposal_id, now))
        return True

    def refund(self, proposal_id: str) -> None:
        self._usage_hourly = [(pid, ts) for pid, ts in self._usage_hourly if pid != proposal_id]
        self._usage_daily = [(pid, ts) for pid, ts in self._usage_daily if pid != proposal_id]

    def remaining(self) -> dict:
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400
        recent_hourly = sum(1 for _, ts in self._usage_hourly if ts > hour_ago)
        recent_daily = sum(1 for _, ts in self._usage_daily if ts > day_ago)
        return {
            "hourly": self.hourly_budget - recent_hourly,
            "daily": self.daily_budget - recent_daily,
        }
