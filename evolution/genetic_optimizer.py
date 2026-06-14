"""
CIEL v1.0 — GeneticOptimizer : opérateurs génétiques avancés.

Migré depuis Hydra (CRISPR_Titan), adapté pour CIEL.
Fournit 5 stratégies de mutation :
  - gaussian    : bruit gaussien
  - epigenetic  : changements corrélés
  - transposon  : sauts de gènes
  - bricolage   : réarrangement
  - sacrifice   : réinitialisation ciblée
"""
from __future__ import annotations

import secrets
import statistics
from dataclasses import dataclass
from typing import Callable

from ciel.evolution.unified_genome import UnifiedGenome, Gene


class GeneticOptimizer:
    """Opérateurs génétiques pour l'évolution CIEL."""

    MUTATION_STRATEGIES = {
        "gaussian": "bruit gaussien",
        "epigenetic": "changements corrélés",
        "transposon": "sauts de gènes",
        "bricolage": "réarrangement",
        "sacrifice": "réinitialisation ciblée",
    }

    def mutate(self, genome: UnifiedGenome, strategy: str = "gaussian", rate: float = 0.15) -> UnifiedGenome:
        if strategy == "epigenetic":
            return self._epigenetic_mutate(genome, rate)
        elif strategy == "transposon":
            return self._transposon_mutate(genome, rate)
        elif strategy == "bricolage":
            return self._bricolage_mutate(genome, rate)
        elif strategy == "sacrifice":
            return self._sacrifice_mutate(genome, rate)
        else:
            return genome.mutate(rate, "gaussian")

    def _epigenetic_mutate(self, genome: UnifiedGenome, rate: float) -> UnifiedGenome:
        """Mutation épigénétique : les gènes voisins mutent ensemble."""
        new_genes = list(genome.genes)
        if not new_genes:
            return genome
        num_clusters = max(1, len(new_genes) // 8)
        cluster_size = len(new_genes) // num_clusters
        for c in range(num_clusters):
            if secrets.randbelow(1000) / 1000 < rate:
                start = c * cluster_size
                end = min(start + cluster_size, len(new_genes))
                shift = (secrets.randbelow(200) - 100) / 100 * 0.2
                for i in range(start, end):
                    old = new_genes[i]
                    new_val = max(old.min_value, min(old.max_value, old.value + shift))
                    new_genes[i] = Gene(
                        name=old.name, category=old.category, value=round(new_val, 6),
                        min_value=old.min_value, max_value=old.max_value,
                    )
        return UnifiedGenome(
            genome_id=f"{genome.genome_id}-EPI",
            mode=genome.mode, genes=new_genes,
            parent_ids=[genome.genome_id],
            generation=genome.generation + 1,
        )

    def _transposon_mutate(self, genome: UnifiedGenome, rate: float) -> UnifiedGenome:
        """Mutation transposon : échange deux blocs de gènes."""
        new_genes = list(genome.genes)
        n = len(new_genes)
        if n < 4:
            return genome.mutate(rate, "gaussian")
        if secrets.randbelow(1000) / 1000 >= rate:
            return genome.mutate(rate, "gaussian")

        pos1 = secrets.randbelow(n // 2)
        pos2 = secrets.randbelow(n // 2) + n // 2
        size = secrets.randbelow(min(8, n // 4)) + 1
        end1 = min(pos1 + size, n)
        end2 = min(pos2 + size, n)
        segment1 = new_genes[pos1:end1]
        segment2 = new_genes[pos2:end2]
        new_genes[pos1:end1] = segment2
        new_genes[pos2:end2] = segment1
        return UnifiedGenome(
            genome_id=f"{genome.genome_id}-TNP",
            mode=genome.mode, genes=new_genes,
            parent_ids=[genome.genome_id],
            generation=genome.generation + 1,
        )

    def _bricolage_mutate(self, genome: UnifiedGenome, rate: float) -> UnifiedGenome:
        """Mutation bricolage : réarrange l'ordre des gènes."""
        new_genes = list(genome.genes)
        n = len(new_genes)
        if n < 3:
            return genome.mutate(rate, "gaussian")
        if secrets.randbelow(1000) / 1000 >= rate:
            return genome.mutate(rate, "gaussian")
        # Réarrange par catégorie
        categories = {}
        for g in new_genes:
            categories.setdefault(g.category, []).append(g)
        rearranged = []
        cat_list = list(categories.values())
        for cat_genes in cat_list:
            start = secrets.randbelow(len(cat_genes))
            cat_genes = cat_genes[start:] + cat_genes[:start]
            rearranged.extend(cat_genes)
        return UnifiedGenome(
            genome_id=f"{genome.genome_id}-BRC",
            mode=genome.mode, genes=rearranged,
            parent_ids=[genome.genome_id],
            generation=genome.generation + 1,
        )

    def _sacrifice_mutate(self, genome: UnifiedGenome, rate: float) -> UnifiedGenome:
        """Mutation sacrifice : réinitialise les gènes les plus faibles."""
        new_genes = list(genome.genes)
        if not new_genes:
            return genome
        # Trouve le gène avec la valeur la plus extrême et le réinitialise
        extreme = max(new_genes, key=lambda g: abs(g.value - 0.5))
        idx = new_genes.index(extreme)
        old = new_genes[idx]
        new_genes[idx] = Gene(
            name=old.name, category=old.category, value=0.5,
            min_value=old.min_value, max_value=old.max_value,
        )
        return UnifiedGenome(
            genome_id=f"{genome.genome_id}-SAC",
            mode=genome.mode, genes=new_genes,
            parent_ids=[genome.genome_id],
            generation=genome.generation + 1,
        )

    def crossover(
        self, parent1: UnifiedGenome, parent2: UnifiedGenome
    ) -> tuple[UnifiedGenome, UnifiedGenome]:
        """Croisement standard avec point de coupure aléatoire."""
        return parent1.crossover(parent2)

    def uniform_crossover(
        self, parent1: UnifiedGenome, parent2: UnifiedGenome
    ) -> tuple[UnifiedGenome, UnifiedGenome]:
        """Croisement uniforme : chaque gène a 50% chance de venir de chaque parent."""
        child1_genes = []
        child2_genes = []
        for g1, g2 in zip(parent1.genes, parent2.genes):
            if secrets.randbelow(2):
                child1_genes.append(g1)
                child2_genes.append(g2)
            else:
                child1_genes.append(g2)
                child2_genes.append(g1)
        return (
            UnifiedGenome(
                genome_id=f"{parent1.genome_id}-U1",
                mode=parent1.mode, genes=child1_genes,
                parent_ids=[parent1.genome_id, parent2.genome_id],
                generation=max(parent1.generation, parent2.generation) + 1,
            ),
            UnifiedGenome(
                genome_id=f"{parent2.genome_id}-U2",
                mode=parent2.mode, genes=child2_genes,
                parent_ids=[parent1.genome_id, parent2.genome_id],
                generation=max(parent1.generation, parent2.generation) + 1,
            ),
        )
