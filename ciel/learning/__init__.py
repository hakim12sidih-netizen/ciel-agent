"""
CIEL v1.0 — Learning : boucle d'apprentissage autonome.

Composant CIEL natif — auto-amélioration continue :
  - Curator : nettoyage et archivage background des skills/sessions
  - SkillGen : génération automatique de skills après tâches complexes
  - Trajectory : compression des trajectoires pour entraînement
"""
from __future__ import annotations

from ciel.learning.curator import Curator
from ciel.learning.skill_gen import SkillGen

__all__ = ["Curator", "SkillGen"]
