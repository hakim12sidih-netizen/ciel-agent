"""
CIEL v1.0 — OmegaSync : agent de synchronisation et intégration.

Migré depuis Hydra (OmegaSync), adapté pour CIEL.
Harmonise les strates, synchronise les données,
et assure la cohérence globale du système.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork
from ciel.evolution.unified_genome import UnifiedGenome


@dataclass(slots=True)
class SyncPoint:
    id: str
    source: str
    target: str
    status: str  # pending, syncing, synced, failed
    data_hash: str
    timestamp: float = field(default_factory=time.time)


class OmegaSync:
    """Agent de synchronisation CIEL.

    Responsabilités :
      - Synchronisation entre strates
      - Intégration des données
      - Cohérence globale
      - Harmonisation des génomes
    """

    def __init__(self):
        self.id = f"OMEGASYNC-{uuid.uuid4().hex[:8]}"
        self.network = LeaderNetwork()
        self.sync_points: list[SyncPoint] = []

    def sync(self, source: str, target: str, data: dict) -> SyncPoint:
        """Synchronise des données entre deux strates."""
        sp = SyncPoint(
            id=f"SYNC-{uuid.uuid4().hex[:12]}",
            source=source,
            target=target,
            status="syncing",
            data_hash=hash(str(data)),
        )
        self.sync_points.append(sp)
        sp.status = "synced"
        self.network.emit("omega.sync", {
            "source": source,
            "target": target,
            "sync_id": sp.id,
        })
        return sp

    def harmonize_genome(self, genome: UnifiedGenome) -> UnifiedGenome:
        """Harmonise un génome pour assurer la cohérence interne."""
        gene_map = {g.name: g for g in genome.genes}
        adjusted = False

        # Vérifie les cohérences entre gènes
        if "exploration_rate" in gene_map and "curiosity" in gene_map:
            if gene_map["exploration_rate"].value > 0.8 and gene_map["curiosity"].value < 0.3:
                genome.set_gene("curiosity", 0.5)
                adjusted = True

        if "risk_tolerance" in gene_map and "caution" in gene_map:
            if gene_map["risk_tolerance"].value > 0.8 and gene_map["caution"].value > 0.8:
                genome.set_gene("caution", 0.5)
                adjusted = True

        if adjusted:
            self.network.emit("omega.harmonize", {
                "genome_id": genome.genome_id,
                "adjustments": True,
            })

        return genome

    def status(self) -> dict:
        return {
            "id": self.id,
            "total_syncs": len(self.sync_points),
            "successful": sum(1 for s in self.sync_points if s.status == "synced"),
            "failed": sum(1 for s in self.sync_points if s.status == "failed"),
        }
