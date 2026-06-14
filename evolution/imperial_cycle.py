"""
CIEL v1.0 — ImperialCycle : cycle d'évolution darwinien.

Migré depuis Hydra, adapté pour CIEL.
Le cycle complet comporte 8 phases :
  1. GENESIS     — Génération de N génomes
  2. SANGLANTE   — Évaluation et sélection des elites
  3. FUSION      — Absorption de gènes des défunts
  4. FACTIONS    — Clustering par spécialité
  5. SYMBIOSE    — Création de super-organismes
  6. REPOPULATION— Croisement des elites
  7. HERITIERS   — Génération d'héritiers
  8. APPRENTISSAGE — Mise à jour RL

Respecte les 4 axiomes CIEL :
  - α : la fitness inclut le poids éthique
  - β : chaque étape est tracée
  - γ : les génomes parents sont conservés
  - δ : le cycle est infini (perpetuel)
"""
from __future__ import annotations

import math
import secrets
import statistics
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.unified_genome import UnifiedGenome, GenomeMode
from ciel.evolution.fitness_evaluator import FitnessEvaluator, FitnessResult
from ciel.evolution.genetic_optimizer import GeneticOptimizer
from ciel.evolution.symbiotic_protocol import SymbioticProtocol
from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class GenerationResult:
    number: int
    population_size: int
    elite_count: int
    best_fitness: float
    avg_fitness: float
    diversity: float
    faction_count: int
    symbiotic_pacts: int
    duration_ms: float
    phase_results: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "generation": self.number,
            "population": self.population_size,
            "elites": self.elite_count,
            "best_fitness": round(self.best_fitness, 4),
            "avg_fitness": round(self.avg_fitness, 4),
            "diversity": round(self.diversity, 4),
            "factions": self.faction_count,
            "pacts": self.symbiotic_pacts,
            "duration_ms": round(self.duration_ms, 2),
            "phases": self.phase_results,
        }


@dataclass(slots=True)
class ImperialCycleConfig:
    population_size: int = 100
    elite_fraction: float = 0.1
    mutation_rate: float = 0.15
    crossover_rate: float = 0.7
    heirs_per_faction: int = 2
    genome_mode: GenomeMode = GenomeMode.V2
    enable_symbiosis: bool = True
    enable_factions: bool = True
    enable_rl: bool = False
    max_generations: int | None = None


class ImperialCycle:
    """Moteur principal du cycle d'évolution CIEL.

    Gère la population, les générations, et orchestre
    les 8 phases du cycle darwinien.
    """

    def __init__(
        self,
        config: ImperialCycleConfig | None = None,
        evaluator: FitnessEvaluator | None = None,
        optimizer: GeneticOptimizer | None = None,
        leader_network: LeaderNetwork | None = None,
    ):
        self.config = config or ImperialCycleConfig()
        self.evaluator = evaluator or FitnessEvaluator()
        self.optimizer = optimizer or GeneticOptimizer()
        self.leader_network = leader_network or LeaderNetwork()
        self.symbiotic = SymbioticProtocol()
        self.population: list[UnifiedGenome] = []
        self.elites: list[UnifiedGenome] = []
        self.factions: dict[str, list[UnifiedGenome]] = {}
        self.generation = 0
        self.history: list[GenerationResult] = []
        self._cycle_id = f"CYCLE-{uuid.uuid4().hex[:12]}"

    # ── Phase 1: GENESIS ──────────────────────────────────

    def genesis(self) -> list[UnifiedGenome]:
        """Crée la population initiale de N génomes."""
        pop = []
        for i in range(self.config.population_size):
            genome = UnifiedGenome(
                genome_id=f"{self._cycle_id}-G{i:04d}",
                mode=self.config.genome_mode,
            )
            pop.append(genome)
        self.population = pop
        self.leader_network.emit("genesis", {"count": len(pop), "mode": self.config.genome_mode.value})
        return pop

    # ── Phase 2: LA SANGLANTE ─────────────────────────────

    def evaluate(self) -> list[UnifiedGenome]:
        """Évalue tous les génomes et sélectionne les elites."""
        results = []
        for genome in self.population:
            result = self.evaluator.evaluate(genome)
            results.append((genome, result.score))

        # Tri par fitness décroissante
        results.sort(key=lambda x: x[1], reverse=True)
        elite_count = max(1, int(len(results) * self.config.elite_fraction))

        self.elites = [r[0] for r in results[:elite_count]]
        self.population = [r[0] for r in results]

        self.leader_network.emit("selection", {
            "elite_count": elite_count,
            "best_fitness": results[0][1] if results else 0,
            "worst_fitness": results[-1][1] if results else 0,
        })
        return self.elites

    # ── Phase 3: FUSION (Testaments) ─────────────────────

    def fusion(self) -> list[UnifiedGenome]:
        """Chaque elite absorbe des gènes des défunts (non-elites)."""
        if len(self.population) <= len(self.elites):
            return self.elites

        dead = [g for g in self.population if g not in self.elites]
        if not dead:
            return self.elites

        for elite in self.elites:
            # Chaque elite absorbe 7 gènes de 7 agents défunts aléatoires
            donors = secrets.SystemRandom().sample(
                dead, min(7, len(dead))
            )
            for donor in donors:
                donor_genes = donor.genes
                if donor_genes:
                    gene = secrets.choice(donor_genes)
                    elite.set_gene(gene.name, gene.value)

        self.leader_network.emit("fusion", {
            "elites": len(self.elites),
            "donors": len(dead),
            "genes_absorbed": len(self.elites) * min(7, len(dead)),
        })
        return self.elites

    # ── Phase 4: FACTIONS ────────────────────────────────

    def form_factions(self) -> dict[str, list[UnifiedGenome]]:
        """Cluster les génomes par spécialité (K-means simple)."""
        if not self.config.enable_factions or len(self.elites) < 3:
            self.factions = {"unified": self.elites}
            return self.factions

        # K-means simplifié basé sur les catégories de gènes
        from ciel.evolution.faction import FactionManager
        manager = FactionManager()
        self.factions = manager.cluster(self.elites, k=3)
        self.leader_network.emit("factions", {
            "count": len(self.factions),
            "names": list(self.factions.keys()),
        })
        return self.factions

    # ── Phase 5: SUPER-ORGANISMES (Symbiose) ─────────────

    def symbiosis(self) -> list[UnifiedGenome]:
        """Crée des super-organismes via SymbioticProtocol."""
        if not self.config.enable_symbiosis or len(self.factions) < 2:
            return []

        pacts = self.symbiotic.create_pacts(self.factions)
        super_organisms = self.symbiotic.create_super_organisms(pacts)
        self.leader_network.emit("symbiosis", {
            "pacts": len(pacts),
            "super_organisms": len(super_organisms),
        })
        return super_organisms

    # ── Phase 6: REPOPULATION ────────────────────────────

    def repopulate(self) -> list[UnifiedGenome]:
        """Croise les elites pour créer la prochaine génération."""
        children: list[UnifiedGenome] = []
        needed = self.config.population_size - len(self.elites)

        if needed <= 0:
            return self.elites

        # Élitisme : garde les elites
        children.extend(self.elites)

        while len(children) < self.config.population_size:
            if len(self.elites) < 2:
                break
            parent1, parent2 = secrets.SystemRandom().sample(self.elites, 2)
            if secrets.randbelow(1000) / 1000 < self.config.crossover_rate:
                child1, child2 = parent1.crossover(parent2)
                # Mutation
                if secrets.randbelow(1000) / 1000 < self.config.mutation_rate:
                    child1 = child1.mutate()
                if secrets.randbelow(1000) / 1000 < self.config.mutation_rate:
                    child2 = child2.mutate()
                children.append(child1)
                if len(children) < self.config.population_size:
                    children.append(child2)
            else:
                # Reproduction asexuée
                child = parent1.mutate(self.config.mutation_rate)
                children.append(child)

        self.population = children[:self.config.population_size]
        self.leader_network.emit("repopulation", {
            "new_population": len(self.population),
            "children_created": len(self.population) - len(self.elites),
        })
        return self.population

    # ── Phase 7: HÉRITIERS ───────────────────────────────

    def heirs(self) -> list[UnifiedGenome]:
        """Chaque chef de faction génère des héritiers."""
        heirs_list: list[UnifiedGenome] = []
        for faction_name, members in self.factions.items():
            if not members:
                continue
            # Le meilleur de la faction est le chef
            chief = max(members, key=lambda g: g.fitness)
            for _ in range(self.config.heirs_per_faction):
                heir = chief.mutate(self.config.mutation_rate * 0.5)  # Mutation réduite
                heir.genome_id = f"{chief.genome_id}-HEIR-{uuid.uuid4().hex[:8]}"
                heirs_list.append(heir)

        self.leader_network.emit("heirs", {
            "count": len(heirs_list),
            "factions": list(self.factions.keys()),
        })
        return heirs_list

    # ── Run full cycle ───────────────────────────────────

    def run_generation(self, phase_mask: int = 0xFF) -> GenerationResult:
        """Exécute un cycle complet de 8 phases.

        Args:
            phase_mask: Bitmask des phases à exécuter (0xFF = toutes)
        """
        start = time.monotonic()
        phase_results: dict[str, Any] = {}

        if self.generation == 0 or not self.population:
            # Phase 1
            if phase_mask & 0x01:
                self.genesis()
                phase_results["genesis"] = {"count": len(self.population)}

        # Phase 2
        if phase_mask & 0x02:
            self.evaluate()
            phase_results["selection"] = {
                "elites": len(self.elites),
                "best": self.elites[0].fitness if self.elites else 0,
            }

        # Phase 3
        if phase_mask & 0x04:
            self.fusion()
            phase_results["fusion"] = {"elites_after": len(self.elites)}

        # Phase 4
        if phase_mask & 0x08:
            self.form_factions()
            phase_results["factions"] = {k: len(v) for k, v in self.factions.items()}

        # Phase 5
        super_orgs = []
        if phase_mask & 0x10:
            super_orgs = self.symbiosis()
            phase_results["symbiosis"] = {"super_organisms": len(super_orgs)}

        # Phase 6
        if phase_mask & 0x20:
            self.repopulate()
            phase_results["repopulation"] = {"population": len(self.population)}

        # Phase 7
        heirs_result = []
        if phase_mask & 0x40:
            heirs_result = self.heirs()
            phase_results["heirs"] = {"count": len(heirs_result)}

        self.generation += 1

        # Statistiques
        fitnesses = [g.fitness for g in self.population]
        best_fitness = max(fitnesses) if fitnesses else 0
        avg_fitness = statistics.mean(fitnesses) if fitnesses else 0
        diversity = statistics.stdev(fitnesses) if len(fitnesses) > 1 else 0
        duration = (time.monotonic() - start) * 1000

        result = GenerationResult(
            number=self.generation,
            population_size=len(self.population),
            elite_count=len(self.elites),
            best_fitness=best_fitness,
            avg_fitness=avg_fitness,
            diversity=diversity,
            faction_count=len(self.factions),
            symbiotic_pacts=len(super_orgs),
            duration_ms=duration,
            phase_results=phase_results,
        )

        self.history.append(result)

        # Phase 8: RL update (if enabled)
        if phase_mask & 0x80 and self.config.enable_rl:
            self._rl_update(result)

        self.leader_network.emit("generation_complete", result.to_dict())
        return result

    def _rl_update(self, result: GenerationResult) -> None:
        """Met à jour via RL (placeholder pour TorchRLBridge)."""
        pass

    def run_evolution(self, generations: int | None = None) -> list[GenerationResult]:
        """Lance N générations d'évolution."""
        max_gen = generations or self.config.max_generations or 10
        for _ in range(max_gen):
            result = self.run_generation()
            print(f"  Génération {result.number}: "
                  f"best={result.best_fitness:.4f} "
                  f"avg={result.avg_fitness:.4f} "
                  f"({result.duration_ms:.0f}ms)")
        return self.history
