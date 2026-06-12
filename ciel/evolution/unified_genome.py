"""
CIEL v1.0 — UnifiedGenome : représentation unifiée du génome d'un agent.

Migré depuis Hydra, amélioré pour CIEL.
Support 4 modes :
  - V1 : 32 gènes (BEHAVIOR)
  - V2 : + TEMPLATE + COGNITION + ARCHITECTURE (128 gènes)
  - TITAN : 18,432 gènes (~7MB genome)
  - NO_GENESIS : construction manuelle
"""
from __future__ import annotations

import json
import math
import secrets
import hashlib
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GenomeMode(Enum):
    V1 = "v1"
    V2 = "v2"
    TITAN = "titan"
    NO_GENESIS = "no-genesis"


class GeneCategory(Enum):
    BEHAVIOR = "behavior"
    TEMPLATE = "template"
    COGNITION = "cognition"
    ARCHITECTURE = "architecture"
    ETHICS = "ethics"
    MEMORY = "memory"
    EVOLUTION = "evolution"


@dataclass(frozen=True, slots=True)
class Gene:
    name: str
    category: GeneCategory
    value: float
    min_value: float = 0.0
    max_value: float = 1.0
    description: str = ""

    def mutate(self, rate: float = 0.15, strategy: str = "gaussian") -> Gene:
        if strategy == "gaussian":
            new_val = self.value + secrets.SystemRandom().gauss(0, rate)
        elif strategy == "uniform":
            new_val = self.value + (secrets.randbelow(200) - 100) / 100 * rate
        else:
            new_val = self.value + (secrets.randbelow(200) - 100) / 100 * rate
        new_val = max(self.min_value, min(self.max_value, new_val))
        return Gene(
            name=self.name,
            category=self.category,
            value=round(new_val, 6),
            min_value=self.min_value,
            max_value=self.max_value,
            description=self.description,
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category.value,
            "value": self.value,
            "min": self.min_value,
            "max": self.max_value,
        }


# ── Gene definitions ──────────────────────────────────

def _default_genes(mode: GenomeMode) -> list[Gene]:
    """Generate default gene set based on mode."""
    genes: list[Gene] = []

    if mode == GenomeMode.V1 or mode == GenomeMode.V2 or mode == GenomeMode.TITAN:
        # Behavioral genes (V1 core)
        behavior_genes = [
            Gene("exploration_rate", GeneCategory.BEHAVIOR, 0.5, 0.0, 1.0, "Taux d'exploration vs exploitation"),
            Gene("risk_tolerance", GeneCategory.BEHAVIOR, 0.3, 0.0, 1.0, "Tolérance au risque"),
            Gene("curiosity", GeneCategory.BEHAVIOR, 0.7, 0.0, 1.0, "Niveau de curiosité"),
            Gene("empathy", GeneCategory.BEHAVIOR, 0.8, 0.0, 1.0, "Capacité d'empathie"),
            Gene("assertiveness", GeneCategory.BEHAVIOR, 0.4, 0.0, 1.0, "Affirmation de soi"),
            Gene("cooperation", GeneCategory.BEHAVIOR, 0.8, 0.0, 1.0, "Tendance à coopérer"),
            Gene("innovation", GeneCategory.BEHAVIOR, 0.6, 0.0, 1.0, "Capacité d'innovation"),
            Gene("caution", GeneCategory.BEHAVIOR, 0.5, 0.0, 1.0, "Niveau de prudence"),
            Gene("speed_preference", GeneCategory.BEHAVIOR, 0.5, 0.0, 1.0, "Préférence vitesse vs qualité"),
            Gene("thoroughness", GeneCategory.BEHAVIOR, 0.6, 0.0, 1.0, "Minutie d'exécution"),
            Gene("creativity", GeneCategory.BEHAVIOR, 0.6, 0.0, 1.0, "Créativité"),
            Gene("logic_weight", GeneCategory.BEHAVIOR, 0.7, 0.0, 1.0, "Poids de la logique"),
            Gene("intuition_weight", GeneCategory.BEHAVIOR, 0.4, 0.0, 1.0, "Poids de l'intuition"),
            Gene("patience", GeneCategory.BEHAVIOR, 0.6, 0.0, 1.0, "Patience"),
            Gene("persistence", GeneCategory.BEHAVIOR, 0.7, 0.0, 1.0, "Persistance"),
            Gene("adaptability", GeneCategory.BEHAVIOR, 0.6, 0.0, 1.0, "Adaptabilité"),
            Gene("skepticism", GeneCategory.BEHAVIOR, 0.4, 0.0, 1.0, "Scepticisme"),
            Gene("openness", GeneCategory.BEHAVIOR, 0.7, 0.0, 1.0, "Ouverture d'esprit"),
            Gene("humility", GeneCategory.BEHAVIOR, 0.6, 0.0, 1.0, "Humilité intellectuelle"),
            Gene("confidence", GeneCategory.BEHAVIOR, 0.6, 0.0, 1.0, "Confiance"),
            Gene("ambiguity_tolerance", GeneCategory.BEHAVIOR, 0.5, 0.0, 1.0, "Tolérance à l'ambiguïté"),
            Gene("uncertainty_awareness", GeneCategory.BEHAVIOR, 0.7, 0.0, 1.0, "Conscience de l'incertitude"),
            Gene("bias_awareness", GeneCategory.BEHAVIOR, 0.5, 0.0, 1.0, "Conscience des biais"),
            Gene("reflection_depth", GeneCategory.BEHAVIOR, 0.5, 0.0, 1.0, "Profondeur de réflexion"),
            Gene("hypothesis_speed", GeneCategory.BEHAVIOR, 0.5, 0.0, 1.0, "Vitesse d'hypothèse"),
            Gene("feedback_sensitivity", GeneCategory.BEHAVIOR, 0.6, 0.0, 1.0, "Sensibilité au feedback"),
            Gene("autonomy", GeneCategory.BEHAVIOR, 0.5, 0.0, 1.0, "Autonomie"),
            Gene("deference", GeneCategory.BEHAVIOR, 0.4, 0.0, 1.0, "Déférence à l'autorité"),
            Gene("meta_awareness", GeneCategory.BEHAVIOR, 0.5, 0.0, 1.0, "Méta-conscience"),
            Gene("goal_drive", GeneCategory.BEHAVIOR, 0.7, 0.0, 1.0, "Pulsion d'objectif"),
            Gene("ethics_weight", GeneCategory.BEHAVIOR, 0.9, 0.0, 1.0, "Poids éthique dans décisions"),
            Gene("aesthetic_sense", GeneCategory.BEHAVIOR, 0.4, 0.0, 1.0, "Sens esthétique"),
        ]
        genes.extend(behavior_genes)

    if mode == GenomeMode.V2 or mode == GenomeMode.TITAN:
        template_genes = [
            Gene("template_fidelity", GeneCategory.TEMPLATE, 0.7, 0.0, 1.0),
            Gene("template_innovation", GeneCategory.TEMPLATE, 0.5, 0.0, 1.0),
            Gene("template_reuse", GeneCategory.TEMPLATE, 0.6, 0.0, 1.0),
            Gene("template_abstraction", GeneCategory.TEMPLATE, 0.5, 0.0, 1.0),
            Gene("template_composition", GeneCategory.TEMPLATE, 0.6, 0.0, 1.0),
            Gene("template_optimization", GeneCategory.TEMPLATE, 0.5, 0.0, 1.0),
            Gene("template_generalization", GeneCategory.TEMPLATE, 0.5, 0.0, 1.0),
            Gene("template_specialization", GeneCategory.TEMPLATE, 0.6, 0.0, 1.0),
        ]
        cognition_genes = [
            Gene("working_memory", GeneCategory.COGNITION, 0.6, 0.0, 1.0),
            Gene("long_term_memory", GeneCategory.COGNITION, 0.7, 0.0, 1.0),
            Gene("attention_span", GeneCategory.COGNITION, 0.6, 0.0, 1.0),
            Gene("parallel_processing", GeneCategory.COGNITION, 0.5, 0.0, 1.0),
            Gene("sequential_depth", GeneCategory.COGNITION, 0.6, 0.0, 1.0),
            Gene("pattern_recognition", GeneCategory.COGNITION, 0.7, 0.0, 1.0),
            Gene("analogical_reasoning", GeneCategory.COGNITION, 0.6, 0.0, 1.0),
            Gene("causal_reasoning", GeneCategory.COGNITION, 0.7, 0.0, 1.0),
        ]
        architecture_genes = [
            Gene("module_count", GeneCategory.ARCHITECTURE, 0.5, 0.0, 1.0),
            Gene("connection_density", GeneCategory.ARCHITECTURE, 0.5, 0.0, 1.0),
            Gene("feedback_loops", GeneCategory.ARCHITECTURE, 0.6, 0.0, 1.0),
            Gene("hierarchy_depth", GeneCategory.ARCHITECTURE, 0.5, 0.0, 1.0),
            Gene("redundancy", GeneCategory.ARCHITECTURE, 0.4, 0.0, 1.0),
            Gene("specialization", GeneCategory.ARCHITECTURE, 0.6, 0.0, 1.0),
            Gene("modularity", GeneCategory.ARCHITECTURE, 0.7, 0.0, 1.0),
            Gene("scalability", GeneCategory.ARCHITECTURE, 0.6, 0.0, 1.0),
        ]
        genes.extend(template_genes + cognition_genes + architecture_genes)

    if mode == GenomeMode.TITAN:
        # Titan adds 96 more specialized genes across all categories
        for i in range(96):
            cat = list(GeneCategory)[i % len(GeneCategory)]
            genes.append(Gene(
                name=f"titan_{cat.value}_{i}",
                category=cat,
                value=secrets.randbelow(1000) / 1000,
                min_value=0.0,
                max_value=1.0,
            ))

    if not genes:
        raise ValueError(f"No genes defined for mode: {mode}")

    return genes


@dataclass(slots=True)
class UnifiedGenome:
    """Représentation unifiée d'un génome CIEL.

    Supporte 4 modes de complexité croissante.
    Peut être sérialisé, muté, croisé avec d'autres génomes.
    """

    genome_id: str
    mode: GenomeMode | str
    genes: list[Gene] = field(default_factory=list)
    parent_ids: list[str] = field(default_factory=list)
    generation: int = 0
    fitness: float = 0.0

    def __post_init__(self):
        if isinstance(self.mode, str):
            self.mode = GenomeMode(self.mode)
        if not self.genes:
            self.genes = _default_genes(self.mode)
        if not self.genome_id:
            self.genome_id = f"CIEL-{uuid.uuid4().hex[:12]}"

    def get_gene(self, name: str) -> Gene | None:
        for g in self.genes:
            if g.name == name:
                return g
        return None

    def set_gene(self, name: str, value: float) -> bool:
        for i, g in enumerate(self.genes):
            if g.name == name:
                new_val = max(g.min_value, min(g.max_value, value))
                self.genes[i] = Gene(
                    name=g.name, category=g.category, value=round(new_val, 6),
                    min_value=g.min_value, max_value=g.max_value, description=g.description,
                )
                return True
        return False

    def mutate(self, rate: float = 0.15, strategy: str = "gaussian") -> UnifiedGenome:
        new_genes = [g.mutate(rate, strategy) for g in self.genes]
        return UnifiedGenome(
            genome_id=f"{self.genome_id}-MUT-{uuid.uuid4().hex[:8]}",
            mode=self.mode,
            genes=new_genes,
            parent_ids=[self.genome_id],
            generation=self.generation + 1,
        )

    def crossover(self, other: UnifiedGenome, point: int | None = None) -> tuple[UnifiedGenome, UnifiedGenome]:
        if len(self.genes) != len(other.genes):
            raise ValueError("Genomes must have same gene count for crossover")
        if point is None:
            point = secrets.randbelow(len(self.genes))
        child1_genes = self.genes[:point] + other.genes[point:]
        child2_genes = other.genes[:point] + self.genes[point:]
        child_id = uuid.uuid4().hex[:12]
        child1 = UnifiedGenome(
            genome_id=f"CIEL-XOVER-{child_id[:8]}",
            mode=self.mode,
            genes=child1_genes,
            parent_ids=[self.genome_id, other.genome_id],
            generation=max(self.generation, other.generation) + 1,
        )
        child2 = UnifiedGenome(
            genome_id=f"CIEL-XOVER-{child_id[8:]}",
            mode=self.mode,
            genes=child2_genes,
            parent_ids=[self.genome_id, other.genome_id],
            generation=max(self.generation, other.generation) + 1,
        )
        return child1, child2

    def distance_to(self, other: UnifiedGenome) -> float:
        if len(self.genes) != len(other.genes):
            return 1.0
        diffs = sum(abs(a.value - b.value) for a, b in zip(self.genes, other.genes))
        max_diff = len(self.genes)
        return diffs / max_diff if max_diff > 0 else 0.0

    def signature(self) -> str:
        data = f"{self.genome_id}|{self.mode.value}|{self.generation}|{self.fitness}|{len(self.genes)}"
        for g in self.genes:
            data += f"|{g.name}:{g.value}"
        return hashlib.blake2b(data.encode(), digest_size=16).hexdigest()

    def to_dict(self) -> dict:
        sig = self.signature()
        return {
            "id": self.genome_id,
            "mode": self.mode.value,
            "gene_count": len(self.genes),
            "generation": self.generation,
            "fitness": self.fitness,
            "parent_ids": self.parent_ids,
            "signature": sig,
            "genes": [g.to_dict() for g in self.genes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> UnifiedGenome:
        genes = [Gene(**g) for g in data.get("genes", [])]
        return cls(
            genome_id=data["id"],
            mode=GenomeMode(data.get("mode", "v2")),
            genes=genes,
            parent_ids=data.get("parent_ids", []),
            generation=data.get("generation", 0),
            fitness=data.get("fitness", 0.0),
        )

    @property
    def id(self) -> str:
        return self.genome_id
