from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FactionType(Enum):
    WARRIORS = "warriors"
    SAGES = "sages"
    EXPLORERS = "explorers"
    ROYAL_BLOOD = "royal_blood"
    SPECTRES = "spectres"


@dataclass(slots=True)
class Skill:
    id: str = ""
    power: float = 0.0
    is_sealed: bool = False


@dataclass(slots=True)
class PersonalityProfile:
    id: str = ""
    velocity: float = 0.5
    precision: float = 0.5
    dominance: float = 0.5
    empathy: float = 0.5
    stealth: float = 0.5
    skills: list[Skill] = field(default_factory=list)
    generation: int = 0
    lineage_id: str = ""


def unified_to_personality(g: Any) -> PersonalityProfile:
    phen = {}
    if hasattr(g, "get_phenotype"):
        phen = g.get_phenotype()
    return PersonalityProfile(
        id=getattr(g, "id", ""),
        velocity=phen.get("exploration_rate", 0.5),
        precision=1.0 - phen.get("risk_tolerance", 0.5),
        dominance=phen.get("creativity_index", 0.5),
        empathy=phen.get("collaboration_drive", 0.5),
        stealth=1.0 - phen.get("exploration_rate", 0.5),
        generation=getattr(g, "generation", 0),
        lineage_id=getattr(g, "faction_id", ""),
    )


class GeneticOptimizer:
    def __init__(self) -> None:
        self._agent_genomes: dict[str, PersonalityProfile] = {}
        self._initialize_genomes()

    def _initialize_genomes(self) -> None:
        default = PersonalityProfile(velocity=0.5, precision=0.8, dominance=0.5, empathy=0.7, stealth=0.5)
        self._agent_genomes["zeus"] = PersonalityProfile(**{**default.__dict__, "dominance": 1.0})
        self._agent_genomes["athena"] = PersonalityProfile(**{**default.__dict__, "precision": 1.0})
        self._agent_genomes["hydra_ui"] = PersonalityProfile(**{**default.__dict__, "velocity": 1.0, "stealth": 0.8})
        self._agent_genomes["erebus"] = PersonalityProfile(**{**default.__dict__, "id": "erebus", "precision": 0.9, "stealth": 1.0})

    async def absorb_into(self, survivor: Any, victim: Any) -> None:
        if survivor is None or victim is None:
            return
        victim_genes = getattr(victim, "g_behavior", [])
        if not victim_genes:
            return
        victim_gene = random.choice(victim_genes)
        survivor_genes = getattr(survivor, "g_behavior", [])
        if not survivor_genes:
            return
        survivor_gene = random.choice(survivor_genes)
        survivor_gene.value = victim_gene.value
        if hasattr(survivor, "mutate"):
            survivor.mutate(0.05)

    def generate_heirs_from(self, chief: Any, partner: Any) -> list[Any]:
        if chief is None or partner is None:
            return []
        heirs: list[Any] = []
        for i in range(2):
            if hasattr(chief, "crossover"):
                heir = chief.crossover(partner)
                heir.agent_name = f"{getattr(chief, 'agent_name', 'unknown')}_heir_{i}_gen{getattr(chief, 'generation', 0) + 1}"
                heir.generation = max(getattr(chief, "generation", 0), getattr(partner, "generation", 0)) + 1
                if hasattr(heir, "faction_id"):
                    heir.faction_id = getattr(chief, "faction_id", None)
                if hasattr(heir, "mutate"):
                    heir.mutate(0.15)
                heirs.append(heir)
        return heirs

    def generate_heirs(self, chief_id: str, partner_id: str) -> list[PersonalityProfile]:
        chief = self._agent_genomes.get(chief_id)
        partner = self._agent_genomes.get(partner_id)
        if chief is None or partner is None:
            return []
        heirs: list[PersonalityProfile] = []
        for _ in range(2):
            heirs.append(PersonalityProfile(
                velocity=(chief.velocity + partner.velocity) / 2 + (random.random() - 0.5) * 0.1,
                precision=(chief.precision + partner.precision) / 2 + (random.random() - 0.5) * 0.1,
                dominance=chief.dominance,
                empathy=partner.empathy,
                stealth=(chief.stealth + partner.stealth) / 2,
                skills=[s for s in chief.skills if s.is_sealed][:2],
                generation=chief.generation + 1,
                lineage_id=chief_id,
            ))
        return heirs

    def elect_patron(self, faction: FactionType, avg_genome: PersonalityProfile) -> str:
        scores = {
            "athena": avg_genome.precision * 1.5 + avg_genome.velocity * 0.5,
            "hermes": avg_genome.velocity * 1.5 + avg_genome.empathy * 0.5,
            "zeus": avg_genome.dominance * 1.5 + avg_genome.precision * 0.5,
        }
        elected = max(scores, key=scores.get)
        return elected

    async def mutate_faction(
        self,
        faction: FactionType,
        trait: str,
        intensity: float,
        population: list[Any] | None = None,
    ) -> dict[str, Any]:
        if population is None:
            population = []
        mutated = 0
        for genome in population:
            if hasattr(genome, "mutate_by_strategy"):
                strategy = self._pick_strategy_for_faction(faction)
                behavior = getattr(genome, "g_behavior", [])
                if behavior:
                    await genome.mutate_by_strategy(
                        random.randint(0, len(behavior) - 1),
                        "BEHAVIOR",
                        strategy,
                    )
                    mutated += 1
        return {"status": "applied", "count": mutated, "faction": faction.value}

    def _pick_strategy_for_faction(self, faction: FactionType) -> str:
        mapping = {
            FactionType.WARRIORS: "sacrifice",
            FactionType.SAGES: "epigenetic",
            FactionType.EXPLORERS: "transposon",
            FactionType.ROYAL_BLOOD: "bricolage",
            FactionType.SPECTRES: "gaussian",
        }
        return mapping.get(faction, "gaussian")

    def process(self, input_data: Any) -> dict[str, Any]:
        return {"optimizer": "GeneticOptimizer", "profiles": list(self._agent_genomes.keys())}
