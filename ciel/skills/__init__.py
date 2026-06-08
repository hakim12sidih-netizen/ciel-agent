"""
Strate 7 — FORGERON : Génération & Évolution des Skills.

8 niveaux de skills :
  0. Réflexes        : précompilés, < 1ms
  1. Réactifs        : déclenchés par pattern précis
  2. Adaptatifs      : ajustent selon contexte + historique
  3. Prédictifs      : anticipent avant demande
  4. Génératifs      : créent d'autres skills (méta)
  5. Méta-Méta       : optimisent création de N4
  6. Symbiotiques    : fusionnés avec psycho utilisateur
  7. Transcendants   : capacités natives du Noyau

12 phases du cycle de vie :
  germination → incubation → conception → embryon → test virtuel
  → naissance → enfance → maturité → spécialisation → enseignement
  → fusion → transcendance
"""
from __future__ import annotations

from ciel.skills.core import (
    SkillLevel,
    SkillPhase,
    Skill,
    SkillRegistry,
    SkillExecutor,
    SkillGenerator,
    SkillOptimizer,
    ForgeronEngine,
)

__all__ = [
    "SkillLevel",
    "SkillPhase",
    "Skill",
    "SkillRegistry",
    "SkillExecutor",
    "SkillGenerator",
    "SkillOptimizer",
    "ForgeronEngine",
]
