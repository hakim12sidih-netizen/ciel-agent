from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class JourneyStage(Enum):
    """17 étapes du Monomythe de Campbell."""
    # Départ
    CALL_TO_ADVENTURE = "call"
    REFUSAL = "refusal"
    SUPERNATURAL_AID = "aid"
    CROSSING_THRESHOLD = "threshold"
    BELLY_OF_WHALE = "belly"
    # Initiation
    ROAD_OF_TRIALS = "trials"
    MEETING_GODDESS = "goddess"
    WOMAN_AS_TEMPTRESS = "temptation"
    ATONEMENT_WITH_FATHER = "atonement"
    APOTHEOSIS = "apotheosis"
    ULTIMATE_BOON = "boon"
    # Retour
    REFUSAL_OF_RETURN = "refusal_return"
    MAGIC_FLIGHT = "flight"
    RESCUE_FROM_WITHOUT = "rescue"
    CROSSING_RETURN_THRESHOLD = "threshold_return"
    MASTER_OF_TWO_WORLDS = "master"
    FREEDOM_TO_LIVE = "freedom"


STAGE_DESCRIPTIONS: dict[JourneyStage, str] = {
    JourneyStage.CALL_TO_ADVENTURE: "Le héros reçoit un appel à l'aventure.",
    JourneyStage.REFUSAL: "Le héros refuse d'abord l'appel.",
    JourneyStage.SUPERNATURAL_AID: "Un guide surnaturel apparaît.",
    JourneyStage.CROSSING_THRESHOLD: "Le héros franchit le seuil vers l'inconnu.",
    JourneyStage.BELLY_OF_WHALE: "Le héros est englouti par l'inconnu.",
    JourneyStage.ROAD_OF_TRIALS: "Série d'épreuves et d'alliés.",
    JourneyStage.MEETING_GODDESS: "Rencontre avec une figure maternelle divine.",
    JourneyStage.WOMAN_AS_TEMPTRESS: "Tentation et séduction.",
    JourneyStage.ATONEMENT_WITH_FATHER: "Réconciliation avec l'autorité.",
    JourneyStage.APOTHEOSIS: "Transcendance et illumination.",
    JourneyStage.ULTIMATE_BOON: "Obtention du trésor ou de l'élixir.",
    JourneyStage.REFUSAL_OF_RETURN: "Le héros hésite à revenir.",
    JourneyStage.MAGIC_FLIGHT: "Poursuite magique et évasion.",
    JourneyStage.RESCUE_FROM_WITHOUT: "Sauvetage inattendu.",
    JourneyStage.CROSSING_RETURN_THRESHOLD: "Retour au monde ordinaire.",
    JourneyStage.MASTER_OF_TWO_WORLDS: "Maîtrise des deux mondes.",
    JourneyStage.FREEDOM_TO_LIVE: "Liberté et renouveau.",
}


class HeroJourney:
    """Voyage du Héros — 17 étapes tracées."""

    def __init__(self) -> None:
        self.stages: list[JourneyStage] = []
        self.current: int = 0

    def reset(self) -> None:
        self.stages = list(JourneyStage)
        self.current = 0

    def next_stage(self) -> JourneyStage | None:
        if self.current >= len(self.stages):
            return None
        stage = self.stages[self.current]
        self.current += 1
        return stage

    def progress(self) -> float:
        return self.current / max(1, len(self.stages))

    def describe_current(self) -> str:
        if self.current >= len(self.stages):
            return "Le voyage est accompli."
        return STAGE_DESCRIPTIONS.get(self.stages[self.current], "")


class CampbellMonomyth:
    """Analyseur du Monomythe de Campbell."""

    def __init__(self) -> None:
        self.journey = HeroJourney()

    def analyze(self, stages: list[JourneyStage]) -> dict:
        stage_set = set(stages)
        all_stages = set(JourneyStage)
        coverage = len(stage_set & all_stages) / len(all_stages)
        has_complete_cycle = (
            JourneyStage.CALL_TO_ADVENTURE in stage_set
            and JourneyStage.ULTIMATE_BOON in stage_set
            and JourneyStage.FREEDOM_TO_LIVE in stage_set
        )
        phases = {"departure": 0, "initiation": 0, "return": 0}
        for s in stages:
            if s.value in ("call", "refusal", "aid", "threshold", "belly"):
                phases["departure"] += 1
            elif s.value in (
                "trials", "goddess", "temptation", "atonement",
                "apotheosis", "boon",
            ):
                phases["initiation"] += 1
            else:
                phases["return"] += 1
        return {
            "coverage": coverage,
            "complete_cycle": has_complete_cycle,
            "phases": phases,
            "n_stages": len(stages),
        }
