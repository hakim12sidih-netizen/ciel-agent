"""
CIEL v1.0 — FactionManager : clustering de génomes par spécialité.

Migré depuis Hydra (Faction), adapté pour CIEL.
Utilise K-means simplifié basé sur les catégories de gènes.
"""
from __future__ import annotations

import secrets
from collections import defaultdict

from ciel.evolution.unified_genome import UnifiedGenome, GeneCategory


FACTION_NAMES = [
    "explorateurs", "analystes", "créateurs",
    "protecteurs", "innovateurs", "sages",
]


class FactionManager:
    """Gère la formation de factions (clusters) de génomes."""

    def cluster(self, genomes: list[UnifiedGenome], k: int = 3) -> dict[str, list[UnifiedGenome]]:
        if not genomes:
            return {}
        if len(genomes) < k:
            return {"unified": genomes}

        # Feature vectors par catégorie
        features = []
        for g in genomes:
            vec = []
            for cat in GeneCategory:
                cat_genes = [gg for gg in g.genes if gg.category == cat]
                if cat_genes:
                    vec.append(sum(gg.value for gg in cat_genes) / len(cat_genes))
                else:
                    vec.append(0.5)
            features.append(vec)

        # K-means simplifié (1 itération)
        centroids = features[:k]
        assignments = [0] * len(genomes)

        for _ in range(3):  # max 3 itérations
            for i, f in enumerate(features):
                dists = [sum(abs(f[j] - c[j]) for j in range(len(f))) for c in centroids]
                assignments[i] = dists.index(min(dists))
            # Recalcule centroids
            for cluster_idx in range(k):
                cluster_points = [features[i] for i in range(len(genomes)) if assignments[i] == cluster_idx]
                if cluster_points:
                    centroids[cluster_idx] = [
                        sum(p[j] for p in cluster_points) / len(cluster_points)
                        for j in range(len(cluster_points[0]))
                    ]

        # Forme les factions
        factions: dict[str, list[UnifiedGenome]] = {}
        for i, g in enumerate(genomes):
            name = FACTION_NAMES[assignments[i] % len(FACTION_NAMES)]
            if name not in factions:
                factions[name] = []
            factions[name].append(g)

        return factions
