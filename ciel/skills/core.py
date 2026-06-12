"""
CIEL v∞.8 — Skills Core Engine (stub).
"""
from __future__ import annotations

from ciel.skills import SkillManager


class ForgeronEngine:
    """Moteur de compétences Forgeron."""

    def __init__(self):
        self._manager = SkillManager()

    def load_all(self):
        return self._manager.list()

    def get(self, name: str):
        return self._manager.get(name)
