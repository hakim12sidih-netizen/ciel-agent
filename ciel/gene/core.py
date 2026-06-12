"""
CIEL v∞.8 — DIMENSION LIX : CIEL-GENE.
Meta-evolution — les algorithmes eux-mêmes évoluent.

Concept : Les algorithmes d'évolution ont un ADN (5 chromosomes).
Cet ADN évolue via crossover et mutation. Les meilleurs algorithmes
survivent et se reproduisent. Méta-méta-évolution : évolution des
algorithmes qui appliquent l'évolution.
"""
from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from ciel.evolution.leader_network import LeaderNetwork


CHROMOSOME_NAMES = (
    "representation", "operators", "exploration",
    "topology", "memory"
)

REPRESENTATION_GENES = ("binaire", "réel", "entier", "arbre", "graphe", "hybride")
OPERATOR_GENES = ("tournoi-3", "SBX-0.9", "mut-0.1", "élitisme-2",
                  "roulette", "uniforme", "mut-adaptative")
EXPLORATION_GENES = ("ε-greedy", "UCB-1", "Thompson", "Lévy-β=1.5")
TOPOLOGY_GENES = ("panmixie", "îles-4", "cellulaire", "ring", "mesh")
MEMORY_GENES = ("archive-100", "restart-10gen", "no_memory", "elite-archive")


@dataclass(slots=True)
class AlgorithmDNA:
    id: str
    generation: int = 0
    fitness: float = 0.0
    chromosomes: dict[str, str] = field(default_factory=dict)

    def mutate(self, rate: float = 0.1):
        for chrom in CHROMOSOME_NAMES:
            if random.random() < rate:
                pool = self._gene_pool(chrom)
                if pool:
                    self.chromosomes[chrom] = random.choice(pool)

    @staticmethod
    def _gene_pool(chrom: str) -> tuple[str, ...]:
        pools = {
            "representation": REPRESENTATION_GENES,
            "operators": OPERATOR_GENES,
            "exploration": EXPLORATION_GENES,
            "topology": TOPOLOGY_GENES,
            "memory": MEMORY_GENES,
        }
        return pools.get(chrom, ())

    @classmethod
    def random(cls) -> AlgorithmDNA:
        dna = cls(id=f"DNA-{uuid.uuid4().hex[:12]}")
        for chrom in CHROMOSOME_NAMES:
            pool = cls._gene_pool(chrom)
            dna.chromosomes[chrom] = random.choice(pool) if pool else ""
        return dna

    def crossover(self, other: AlgorithmDNA) -> AlgorithmDNA:
        child = AlgorithmDNA(id=f"DNA-{uuid.uuid4().hex[:12]}",
                             generation=max(self.generation, other.generation) + 1)
        for chrom in CHROMOSOME_NAMES:
            child.chromosomes[chrom] = random.choice(
                [self.chromosomes.get(chrom), other.chromosomes.get(chrom)]
            )
        return child

    def to_dict(self) -> dict:
        return {"id": self.id, "gen": self.generation,
                "fitness": round(self.fitness, 4),
                "chromosomes": dict(self.chromosomes)}


@dataclass(slots=True)
class BenchmarkSuite:
    name: str
    problems: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)

    def evaluate(self, dna: AlgorithmDNA) -> float:
        total = 0.0
        for prob in self.problems:
            base = hash(dna.id + prob) % 100 / 100.0
            adapt = 0.0
            if "hybride" in dna.chromosomes.get("representation", ""):
                adapt += 0.1
            if "mut-adaptative" in dna.chromosomes.get("operators", ""):
                adapt += 0.1
            if "archive" in dna.chromosomes.get("memory", ""):
                adapt += 0.05
            total += min(base + adapt, 1.0)
        return total / max(len(self.problems), 1)


class GeneEngine:
    """Moteur de méta-évolution des algorithmes.

    Maintient une population d'ADN algorithmiques, les évalue
    sur des benchmarks, applique sélection/crossover/mutation.
    """

    def __init__(self, pop_size: int = 50):
        self.population: dict[str, AlgorithmDNA] = {}
        self.pop_size = pop_size
        self.generation = 0
        self.benchmarks: list[BenchmarkSuite] = []
        self.best_fitness: float = 0.0
        self.history: list[dict] = []
        self.network = LeaderNetwork()
        self._init_population()

    def _init_population(self):
        for _ in range(self.pop_size):
            dna = AlgorithmDNA.random()
            self.population[dna.id] = dna

    def add_benchmark(self, name: str,
                      problems: list[str] | None = None) -> BenchmarkSuite:
        b = BenchmarkSuite(
            name=name,
            problems=problems or [f"prob_{i}" for i in range(10)],
        )
        self.benchmarks.append(b)
        return b

    def evaluate_all(self) -> dict:
        if not self.benchmarks:
            b = self.add_benchmark("default")
        total_best = 0.0
        for dna in self.population.values():
            scores = []
            for bm in self.benchmarks:
                s = bm.evaluate(dna)
                scores.append(s)
            dna.fitness = sum(scores) / len(scores)
            total_best = max(total_best, dna.fitness)
        self.best_fitness = total_best
        return {"best": total_best, "avg": sum(
            d.fitness for d in self.population.values()) / len(self.population)}

    def evolve(self, elite_pct: float = 0.1, mut_rate: float = 0.1) -> dict:
        self.evaluate_all()
        n_elite = max(1, int(self.pop_size * elite_pct))
        sorted_dna = sorted(self.population.values(),
                            key=lambda d: d.fitness, reverse=True)
        elites = sorted_dna[:max(n_elite, 2)]
        offspring = []
        for e in elites:
            offspring.append(e)
        while len(offspring) < self.pop_size:
            a, b = random.sample(elites, 2)
            child = a.crossover(b)
            child.mutate(mut_rate)
            offspring.append(child)
        self.population = {d.id: d for d in offspring}
        self.generation += 1
        entry = {"gen": self.generation,
                 "best": self.best_fitness,
                 "pop": len(self.population)}
        self.history.append(entry)
        return entry

    def get_niche_specialists(self) -> list[dict]:
        specialists = []
        top = sorted(self.population.values(),
                     key=lambda d: d.fitness, reverse=True)[:5]
        for dna in top:
            specialists.append({
                "id": dna.id,
                "fitness": dna.fitness,
                "representation": dna.chromosomes.get("representation", ""),
                "operators": dna.chromosomes.get("operators", ""),
            })
        return specialists

    def suggest_hybrid(self) -> dict:
        top = sorted(self.population.values(),
                     key=lambda d: d.fitness, reverse=True)[:3]
        if len(top) < 2:
            return {"suggestion": "besoin de plus de générations"}
        hybrid = top[0].crossover(top[1])
        return {"parent_a": top[0].id, "parent_b": top[1].id,
                "hybrid_id": hybrid.id,
                "hybrid_chromosomes": dict(hybrid.chromosomes)}

    def get_stats(self) -> dict:
        return {
            "generation": self.generation,
            "population": len(self.population),
            "best_fitness": round(self.best_fitness, 4),
            "benchmarks": len(self.benchmarks),
            "niches": len(self.get_niche_specialists()),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "evolve":
            return {"status": "ok",
                    "evolution": self.evolve(
                        input_data.get("elite_pct", 0.1),
                        input_data.get("mut_rate", 0.1))}
        elif action == "specialists":
            return {"status": "ok",
                    "specialists": self.get_niche_specialists()}
        elif action == "hybrid":
            return {"status": "ok",
                    "hybrid": self.suggest_hybrid()}
        elif action == "evaluate":
            return {"status": "ok",
                    "evaluation": self.evaluate_all()}
        return {"status": "ok", "generation": self.generation}
