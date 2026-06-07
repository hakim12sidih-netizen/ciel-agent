"""
CIEL v∞.3 — Strate 5 : NARRATEUR (Intelligence Narrative).

Architectures narratives :
- Propp : 31 fonctions du conte merveilleux
- Campbell : Monomythe (Voyage du Héros) en 17 étapes
- Genette : discours narratif (temps, mode, voix)
- Barthes : codes narratifs (herméneutique, proaïrétique, etc.)
- Greimas : modèle actantiel (6 actants, 3 axes)
- Todorov : équilibre → déséquilibre → équilibre
- Structure narrative générative : πλοκή (mythos), ἦθος (ethos), λέξις (lexis)
"""
from __future__ import annotations

from ciel.narrateur.core import (
    NarrativeEngine,
    Story,
    NarrativeArc,
    NarrativeRole,
    NarrativeFunction,
)
from ciel.narrateur.propp import ProppAnalyzer, ProppFunction
from ciel.narrateur.campbell import CampbellMonomyth, HeroJourney, JourneyStage
from ciel.narrateur.actantial import ActantialModel, ActantRole

__all__ = [
    "NarrativeEngine", "Story", "NarrativeArc", "NarrativeRole", "NarrativeFunction",
    "ProppAnalyzer", "ProppFunction",
    "CampbellMonomyth", "HeroJourney", "JourneyStage",
    "ActantialModel", "ActantRole",
]
