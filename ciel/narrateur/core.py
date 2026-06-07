from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class NarrativeRole(Enum):
    HERO = "hero"
    VILLAIN = "villain"
    DONOR = "donor"
    HELPER = "helper"
    PRINCESS = "princess"
    DISPATCHER = "dispatcher"
    FALSE_HERO = "false_hero"
    MENTOR = "mentor"
    SHADOW = "shadow"
    TRICKSTER = "trickster"
    GUARDIAN = "guardian"
    HERALD = "herald"
    SHAPE_SHIFTER = "shape_shifter"
    ORACLE = "oracle"
    SACRIFICE = "sacrifice"
    WITNESS = "witness"


class NarrativeFunction(Enum):
    # Propp-inspired
    ABSENTATION = "absent"
    INTERDICTION = "interdict"
    VIOLATION = "violation"
    RECONNAISSANCE = "recon"
    DELIVERY = "delivery"
    TRICKERY = "trickery"
    COMPLICITY = "complicity"
    VILLAINY = "villainy"
    LACK = "lack"
    MEDIATION = "mediation"
    COUNTERACTION = "counter"
    DEPARTURE = "departure"
    TEST = "test"
    REACTION = "reaction"
    RECEIPT = "receipt"
    SPATIAL_SHIFT = "shift"
    STRUGGLE = "struggle"
    BRANDING = "brand"
    VICTORY = "victory"
    LIQUIDATION = "liquidation"
    RETURN = "return"
    PURSUIT = "pursuit"
    RESCUE = "rescue"
    UNRECOGNIZED = "unrecog"
    TRANSFIGURATION = "transfig"
    PUNISHMENT = "punish"
    WEDDING = "wedding"
    # Campbell-inspired
    CALL_TO_ADVENTURE = "call"
    REFUSAL = "refusal"
    SUPERNATURAL_AID = "aid"
    CROSSING_THRESHOLD = "threshold"
    BELLY_OF_WHALE = "belly"
    ROAD_OF_TRIALS = "trials"
    MEETING_GODDESS = "goddess"
    TEMPTATION = "temptation"
    ATONEMENT = "atonement"
    APOTHEOSIS = "apotheosis"
    ULTIMATE_BOON = "boon"
    REFUSAL_RETURN = "refusal_return"
    MAGIC_FLIGHT = "flight"
    RESCUE_WITHOUT = "rescue_without"
    CROSSING_THRESHOLD_RETURN = "threshold_return"
    MASTER_TWO_WORLDS = "master"
    FREEDOM_TO_LIVE = "freedom"


@dataclass(slots=True)
class NarrativeArc:
    name: str
    functions: list[NarrativeFunction]
    roles: dict[str, NarrativeRole] = field(default_factory=dict)
    tension: float = 0.5
    pace: float = 1.0
    theme: str = ""
    mood: str = "neutral"


@dataclass(slots=True)
class Story:
    id: str
    title: str = ""
    arcs: list[NarrativeArc] = field(default_factory=list)
    characters: dict[str, NarrativeRole] = field(default_factory=dict)
    current_arc: int = 0
    current_step: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_arc(self, arc: NarrativeArc) -> None:
        self.arcs.append(arc)

    def add_character(self, name: str, role: NarrativeRole) -> None:
        self.characters[name] = role

    def progress(self) -> tuple[NarrativeArc, NarrativeFunction] | None:
        if self.current_arc >= len(self.arcs):
            return None
        arc = self.arcs[self.current_arc]
        if self.current_step >= len(arc.functions):
            self.current_arc += 1
            self.current_step = 0
            if self.current_arc >= len(self.arcs):
                return None
            arc = self.arcs[self.current_arc]
        func = arc.functions[self.current_step]
        self.current_step += 1
        return arc, func


class NarrativeEngine:
    """Moteur narratif central — génère et analyse des récits."""

    def __init__(self) -> None:
        self.stories: dict[str, Story] = {}
        self._function_weights: dict[NarrativeFunction, float] = {
            f: random.uniform(0.5, 1.0) for f in NarrativeFunction
        }

    def create_story(self, title: str = "") -> Story:
        story = Story(id=str(uuid.uuid4()), title=title)
        self.stories[story.id] = story
        return story

    def generate_hero_journey(self, hero_name: str = "Héros") -> Story:
        story = self.create_story(title=f"Le Voyage de {hero_name}")
        story.add_character(hero_name, NarrativeRole.HERO)
        story.add_character("Mentor", NarrativeRole.MENTOR)
        story.add_character("Ombre", NarrativeRole.SHADOW)
        story.add_character("Gardien", NarrativeRole.GUARDIAN)

        # Departure
        departure = NarrativeArc(
            name="Départ",
            functions=[
                NarrativeFunction.CALL_TO_ADVENTURE,
                NarrativeFunction.REFUSAL,
                NarrativeFunction.SUPERNATURAL_AID,
                NarrativeFunction.CROSSING_THRESHOLD,
                NarrativeFunction.BELLY_OF_WHALE,
            ],
            roles={"hero": NarrativeRole.HERO, "mentor": NarrativeRole.MENTOR},
            tension=0.3,
            mood="curiosity",
        )
        # Initiation
        initiation = NarrativeArc(
            name="Initiation",
            functions=[
                NarrativeFunction.ROAD_OF_TRIALS,
                NarrativeFunction.MEETING_GODDESS,
                NarrativeFunction.TEMPTATION,
                NarrativeFunction.ATONEMENT,
                NarrativeFunction.APOTHEOSIS,
                NarrativeFunction.ULTIMATE_BOON,
            ],
            roles={"hero": NarrativeRole.HERO, "shadow": NarrativeRole.SHADOW},
            tension=0.7,
            mood="struggle",
        )
        # Return
        return_arc = NarrativeArc(
            name="Retour",
            functions=[
                NarrativeFunction.REFUSAL_RETURN,
                NarrativeFunction.MAGIC_FLIGHT,
                NarrativeFunction.RESCUE_WITHOUT,
                NarrativeFunction.CROSSING_THRESHOLD_RETURN,
                NarrativeFunction.MASTER_TWO_WORLDS,
                NarrativeFunction.FREEDOM_TO_LIVE,
            ],
            roles={"hero": NarrativeRole.HERO},
            tension=0.5,
            mood="resolution",
        )
        story.add_arc(departure)
        story.add_arc(initiation)
        story.add_arc(return_arc)
        return story

    def generate_propp_tale(self, characters: dict[str, NarrativeRole]) -> Story:
        story = self.create_story(title="Conte Merveilleux")
        for name, role in characters.items():
            story.add_character(name, role)
        arc = NarrativeArc(
            name="Propp",
            functions=[
                NarrativeFunction.ABSENTATION,
                NarrativeFunction.INTERDICTION,
                NarrativeFunction.VIOLATION,
                NarrativeFunction.RECONNAISSANCE,
                NarrativeFunction.VILLAINY,
                NarrativeFunction.LACK,
                NarrativeFunction.MEDIATION,
                NarrativeFunction.COUNTERACTION,
                NarrativeFunction.DEPARTURE,
                NarrativeFunction.TEST,
                NarrativeFunction.STRUGGLE,
                NarrativeFunction.VICTORY,
                NarrativeFunction.LIQUIDATION,
                NarrativeFunction.RETURN,
                NarrativeFunction.TRANSFIGURATION,
                NarrativeFunction.PUNISHMENT,
                NarrativeFunction.WEDDING,
            ],
            roles=characters,
            tension=0.6,
            mood="epic",
        )
        story.add_arc(arc)
        return story

    def analyze_arc(self, story: Story) -> dict[str, Any]:
        if not story.arcs:
            return {"error": "empty"}
        total = sum(len(a.functions) for a in story.arcs)
        return {
            "story_id": story.id,
            "title": story.title,
            "arcs": len(story.arcs),
            "total_functions": total,
            "characters": list(story.characters.keys()),
            "character_roles": {k: v.value for k, v in story.characters.items()},
            "progress": f"{story.current_arc}/{len(story.arcs)} arcs, {story.current_step}/total steps",
        }

    def tension_profile(self, story: Story) -> list[float]:
        profile = []
        for arc in story.arcs:
            n = len(arc.functions)
            for i in range(n):
                t = arc.tension * (1.0 + 0.5 * math.sin(math.pi * i / max(1, n - 1)))
                profile.append(t)
        return profile

    def _narrate_function(self, func: NarrativeFunction, characters: dict[str, NarrativeRole]) -> str:
        templates = {
            NarrativeFunction.CALL_TO_ADVENTURE: "Un appel retentit, brisant le silence du quotidien.",
            NarrativeFunction.CROSSING_THRESHOLD: "La limite est franchie ; le monde connu s'éloigne.",
            NarrativeFunction.ROAD_OF_TRIALS: "Une série d'épreuves se dresse sur le chemin.",
            NarrativeFunction.ULTIMATE_BOON: "Enfin, le trésor tant convoité est à portée de main.",
            NarrativeFunction.RETURN: "Le chemin du retour s'ouvre, mais rien ne sera plus comme avant.",
            NarrativeFunction.VICTORY: "La victoire est remportée, au prix de grands sacrifices.",
            NarrativeFunction.WEDDING: "L'union scelle le destin des héros.",
        }
        return templates.get(func, f"L'étape narrative '{func.value}' se déroule.")

import math
