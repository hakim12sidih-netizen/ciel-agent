"""
CIEL v1.0 — Skills System : compétences et apprentissage.

Composant CIEL natif — système de compétences.
Architecture progressive :
  Tier 1 : metadata (name + description)
  Tier 2 : SKILL.md complet
  Tier 3 : fichiers (références, templates, scripts)
"""
from __future__ import annotations

from ciel.skills.models import Skill, SkillManager
from ciel.skills.curator import SkillCurator, CuratorState, ConsolidationPlan
from ciel.skills.marketplace import SkillMarketplace, CatalogueEntry

__all__ = [
    "Skill", "SkillManager",
    "SkillCurator", "CuratorState", "ConsolidationPlan",
    "SkillMarketplace", "CatalogueEntry",
]
