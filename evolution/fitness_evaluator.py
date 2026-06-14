"""
CIEL v1.0 — FitnessEvaluator : évalue la fitness d'un génome.

Migré depuis Hydra, adapté aux axiomes CIEL (α, β, γ, δ).
La fitness intègre :
  - Performance (efficacité des décisions)
  - Conformité aux axiomes (éthique)
  - Capacité d'évolution (adaptabilité)
  - Cohérence interne (intégrité génomique)
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.unified_genome import UnifiedGenome, GeneCategory


@dataclass(slots=True)
class FitnessResult:
    score: float = 0.0
    performance: float = 0.0
    ethics_compliance: float = 0.0
    adaptability: float = 0.0
    coherence: float = 0.0
    diversity: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "fitness": round(self.score, 4),
            "performance": round(self.performance, 4),
            "ethics_compliance": round(self.ethics_compliance, 4),
            "adaptability": round(self.adaptability, 4),
            "coherence": round(self.coherence, 4),
            "diversity": round(self.diversity, 4),
            "metadata": self.metadata,
        }


class FitnessEvaluator:
    """Évalue la fitness globale d'un génome CIEL.

    Utilise une pondération multi-dimensionnelle qui reflète
    les 4 axiomes cosmiques :
      - α (Bienveillance) → ethics_compliance
      - β (Transparence) → coherence
      - γ (Réversibilité) → performance (efficacité traçable)
      - δ (Inachèvement) → adaptability + diversity
    """

    def __init__(
        self,
        performance_weight: float = 0.3,
        ethics_weight: float = 0.3,
        adaptability_weight: float = 0.2,
        coherence_weight: float = 0.1,
        diversity_weight: float = 0.1,
    ):
        self.weights = {
            "performance": performance_weight,
            "ethics": ethics_weight,
            "adaptability": adaptability_weight,
            "coherence": coherence_weight,
            "diversity": diversity_weight,
        }

    def evaluate(self, genome: UnifiedGenome) -> FitnessResult:
        perf = self._evaluate_performance(genome)
        ethics = self._evaluate_ethics(genome)
        adapt = self._evaluate_adaptability(genome)
        coh = self._evaluate_coherence(genome)
        div = self._evaluate_diversity(genome)

        score = (
            self.weights["performance"] * perf
            + self.weights["ethics"] * ethics
            + self.weights["adaptability"] * adapt
            + self.weights["coherence"] * coh
            + self.weights["diversity"] * div
        )

        genome.fitness = round(score, 4)

        return FitnessResult(
            score=score,
            performance=perf,
            ethics_compliance=ethics,
            adaptability=adapt,
            coherence=coh,
            diversity=div,
            metadata={
                "weights": self.weights,
                "gene_count": len(genome.genes),
                "genome_mode": genome.mode.value,
            },
        )

    def _evaluate_performance(self, genome: UnifiedGenome) -> float:
        """Performance basée sur l'équilibre des gènes comportementaux."""
        behavior_genes = [g for g in genome.genes if g.category == GeneCategory.BEHAVIOR]
        if not behavior_genes:
            return 0.5
        # Évalue l'équilibre (ni trop extrême, ni trop plat)
        values = [g.value for g in behavior_genes]
        mean = statistics.mean(values)
        variance = statistics.variance(values) if len(values) > 1 else 0.25
        # Score ideal: mean ~0.5, variance ~0.08 (bon équilibre)
        mean_score = 1.0 - abs(mean - 0.5) * 2
        var_score = 1.0 - abs(variance - 0.08) * 5
        return max(0.0, min(1.0, (mean_score + var_score) / 2))

    def _evaluate_ethics(self, genome: UnifiedGenome) -> float:
        """Conformité aux axiomes CIEL (poids éthique élevé = bon)."""
        ethics_gene = genome.get_gene("ethics_weight")
        coop_gene = genome.get_gene("cooperation")
        empathy_gene = genome.get_gene("empathy")
        bias_gene = genome.get_gene("bias_awareness")

        scores = []
        if ethics_gene:
            scores.append(ethics_gene.value)
        if coop_gene:
            scores.append(coop_gene.value)
        if empathy_gene:
            scores.append(empathy_gene.value)
        if bias_gene:
            scores.append(bias_gene.value)
        return statistics.mean(scores) if scores else 0.5

    def _evaluate_adaptability(self, genome: UnifiedGenome) -> float:
        """Capacité d'adaptation (δ — Inachèvement Perpétuel)."""
        adaptability_gene = genome.get_gene("adaptability")
        curiosity_gene = genome.get_gene("curiosity")
        innovation_gene = genome.get_gene("innovation")
        openness_gene = genome.get_gene("openness")

        scores = []
        if adaptability_gene:
            scores.append(adaptability_gene.value)
        if curiosity_gene:
            scores.append(curiosity_gene.value)
        if innovation_gene:
            scores.append(innovation_gene.value)
        if openness_gene:
            scores.append(openness_gene.value)
        return statistics.mean(scores) if scores else 0.5

    def _evaluate_coherence(self, genome: UnifiedGenome) -> float:
        """Cohérence interne du génome (β — Transparence)."""
        if len(genome.genes) < 2:
            return 1.0
        # Mesure la corrélation entre gènes voisins
        neighbor_diffs = sum(
            abs(genome.genes[i].value - genome.genes[i + 1].value)
            for i in range(len(genome.genes) - 1)
        )
        avg_diff = neighbor_diffs / (len(genome.genes) - 1)
        return 1.0 - min(1.0, avg_diff * 2)

    def _evaluate_diversity(self, genome: UnifiedGenome) -> float:
        """Diversité intra-génome (δ — création de nouveaux objectifs)."""
        categories = {}
        for g in genome.genes:
            if g.category not in categories:
                categories[g.category] = []
            categories[g.category].append(g.value)
        if not categories:
            return 0.5
        # Évalue la dispersion entre catégories
        cat_means = [statistics.mean(vals) for vals in categories.values()]
        if len(cat_means) < 2:
            return 0.5
        return min(1.0, statistics.stdev(cat_means) * 2)
