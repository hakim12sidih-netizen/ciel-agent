"""
CIEL v1.0 — SymbioticProtocol : création de super-organismes.

Migré depuis Hydra, adapté pour CIEL.
Permet à des génomes complémentaires de former des
pacts symbiotiques et de créer des super-organismes.
"""
from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.unified_genome import UnifiedGenome
from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class Pact:
    """Pacte symbiotique entre factions."""
    id: str
    faction_a: str
    faction_b: str
    compatibility: float
    created_at: float

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "factions": [self.faction_a, self.faction_b],
            "compatibility": round(self.compatibility, 4),
        }


@dataclass(slots=True)
class SuperOrganism:
    """Super-organisme créé par fusion de génomes."""
    id: str
    name: str
    genomes: list[UnifiedGenome]
    pact_id: str
    fitness: float = 0.0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "genome_count": len(self.genomes),
            "fitness": round(self.fitness, 4),
            "pact_id": self.pact_id,
        }


SYMBIOTIC_NAMES = [
    "Phénix", "Chimère", "Griffon", "Sphinx",
    "Hydre", "Pegase", "Cerbere", "Minotaure",
    "Kraken", "Leviathan", "Bahamut", "Tiamat",
]


class SymbioticProtocol:
    """Gère les relations symbiotiques entre génomes CIEL.

    Détecte la complémentarité entre factions et
    crée des super-organismes par fusion génomique.
    """

    def __init__(self):
        self.pacts: list[Pact] = []
        self.super_organisms: list[SuperOrganism] = []
        self.leader_network = LeaderNetwork()

    def create_pacts(self, factions: dict[str, list[UnifiedGenome]]) -> list[Pact]:
        """Crée des pacts entre factions complémentaires."""
        self.pacts.clear()
        faction_names = list(factions.keys())

        if len(faction_names) < 2:
            return []

        for i in range(len(faction_names)):
            for j in range(i + 1, len(faction_names)):
                compat = self._compute_compatibility(
                    factions[faction_names[i]], factions[faction_names[j]]
                )
                if compat > 0.4:
                    pact = Pact(
                        id=f"PACT-{uuid.uuid4().hex[:12]}",
                        faction_a=faction_names[i],
                        faction_b=faction_names[j],
                        compatibility=compat,
                        created_at=__import__("time").time(),
                    )
                    self.pacts.append(pact)

        self.leader_network.emit("pacts_created", {"count": len(self.pacts)})
        return self.pacts

    def create_super_organisms(self, pacts: list[Pact] | None = None) -> list[SuperOrganism]:
        """Crée des super-organismes à partir des pacts."""
        self.super_organisms.clear()
        active_pacts = pacts if pacts is not None else self.pacts

        for pact in active_pacts:
            so = SuperOrganism(
                id=f"SO-{uuid.uuid4().hex[:12]}",
                name=secrets.choice(SYMBIOTIC_NAMES),
                genomes=[],  # Les génomes seront fusionnés
                pact_id=pact.id,
                fitness=pact.compatibility,
            )
            self.super_organisms.append(so)

        self.leader_network.emit("super_organisms_created", {"count": len(self.super_organisms)})
        return self.super_organisms

    def _compute_compatibility(
        self, group_a: list[UnifiedGenome], group_b: list[UnifiedGenome]
    ) -> float:
        """Calcule la compatibilité entre deux groupes de génomes."""
        if not group_a or not group_b:
            return 0.0
        avg_a = sum(g.fitness for g in group_a) / len(group_a)
        avg_b = sum(g.fitness for g in group_b) / len(group_b)
        return (avg_a + avg_b) / 2 + secrets.SystemRandom().uniform(-0.2, 0.2)
