from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ProppFunction(Enum):
    """Les 31 fonctions de Propp (conte merveilleux)."""
    # Préparation (1-7)
    ABSENTATION = "1_absent"          # Membre famille s'absente
    INTERDICTION = "2_interdict"      # Interdiction au héros
    VIOLATION = "3_violation"         # Interdiction violée
    RECONNAISSANCE = "4_recon"        # Agresseur tente reconnaissance
    DELIVERY = "5_delivery"           # Agresseur reçoit information
    TRICKERY = "6_trickery"           # Agresseur trompe victime
    COMPLICITY = "7_complicity"       # Victime se laisse tromper
    # Complication (8)
    VILLAINY = "8_villainy"           # Agresseur nuit
    LACK = "8a_lack"                  # Manque/désir
    # Transition (9-11)
    MEDIATION = "9_mediation"         # Malheur divulgué
    COUNTERACTION = "10_counter"      # Héros accepte/decide
    DEPARTURE = "11_depart"           # Héros quitte maison
    # Épreuves (12-14)
    TEST = "12_test"                  # Donateur éprouve héros
    REACTION = "13_reaction"          # Héros réagit
    RECEIPT = "14_receipt"            # Héros reçoit objet magique
    # Réaction (15-18)
    SPATIAL_SHIFT = "15_shift"        # Transfert vers quête
    STRUGGLE = "16_struggle"          # Combat
    BRANDING = "17_brand"             # Marque du héros
    VICTORY = "18_victory"            # Victoire
    # Retour (19-22)
    LIQUIDATION = "19_liquidation"    # Méfait initial réparé
    RETURN = "20_return"              # Retour du héros
    PURSUIT = "21_pursuit"            # Poursuite
    RESCUE = "22_rescue"              # Sauvetage
    # Reconnaissance (23-26)
    UNRECOGNIZED = "23_unrecog"       # Arrivée incognito
    UNFOUNDED_CLAIMS = "24_claims"    # Faux héros
    HARD_TASK = "25_task"             # Tâche difficile
    SOLUTION = "26_solution"          # Tâche accomplie
    # Réhabilitation (27-31)
    RECOGNITION = "27_recognition"    # Héros reconnu
    EXPOSURE = "28_exposure"          # Faux héros démasqué
    TRANSFIGURATION = "29_transfig"   # Héros transfiguré
    PUNISHMENT = "30_punish"          # Agresseur puni
    WEDDING = "31_wedding"            # Mariage/couronnement


class ProppSphere(Enum):
    """Sphères d'action de Propp (7 actants)."""
    HERO = "hero"
    VILLAIN = "villain"
    DONOR = "donor"
    HELPER = "helper"
    PRINCESS = "princess"
    DISPATCHER = "dispatcher"
    FALSE_HERO = "false_hero"


FUNCTION_SEQUENCES: dict[str, list[ProppFunction]] = {
    "combat_victory": [ProppFunction.STRUGGLE, ProppFunction.VICTORY, ProppFunction.LIQUIDATION],
    "pursuit_rescue": [ProppFunction.PURSUIT, ProppFunction.RESCUE, ProppFunction.UNRECOGNIZED],
    "hard_task": [ProppFunction.HARD_TASK, ProppFunction.SOLUTION, ProppFunction.RECOGNITION],
    "exposure_punish": [ProppFunction.EXPOSURE, ProppFunction.PUNISHMENT, ProppFunction.WEDDING],
}


class ProppAnalyzer:
    """Analyseur structurel basé sur les 31 fonctions de Propp."""

    def __init__(self) -> None:
        self.sequences: list[ProppFunction] = []

    def analyze(self, functions: list[ProppFunction]) -> dict:
        coverage = len(set(functions)) / 31.0
        has_villainy = ProppFunction.VILLAINY in functions
        has_victory = ProppFunction.VICTORY in functions
        has_wedding = ProppFunction.WEDDING in functions
        structure_score = 0.0
        if has_villainy:
            structure_score += 0.33
        if has_victory:
            structure_score += 0.33
        if has_wedding:
            structure_score += 0.34
        return {
            "coverage": coverage,
            "structure_score": structure_score,
            "n_functions": len(functions),
            "villainy_resolved": has_villainy and has_victory,
            "has_wedding_ending": has_wedding,
        }
