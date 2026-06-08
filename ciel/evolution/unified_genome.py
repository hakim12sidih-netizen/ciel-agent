from __future__ import annotations

import hashlib
import json
import math
import os
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChromosomeType(Enum):
    STRUCT = "STRUCT"
    BEHAVIOR = "BEHAVIOR"
    EPI = "EPI"
    META = "META"


@dataclass(slots=True)
class Gene:
    id: int
    value: float
    chromosome: ChromosomeType
    mutable: bool = True
    h3k4me3: float = 0.0
    h3k27me3: float = 0.0
    dna_methylation: float = 0.0

    def express(self) -> float:
        if self.h3k27me3 > 0.7:
            return self.value * 0.1
        if self.h3k4me3 > 0.7:
            return self.value * 1.5
        return self.value * (1.0 - self.dna_methylation)

    def clone(self) -> Gene:
        return Gene(self.id, self.value, self.chromosome, self.mutable,
                    self.h3k4me3, self.h3k27me3, self.dna_methylation)


@dataclass(slots=True)
class EpigeneticMarker:
    gene: str
    active: bool = True
    methylation: float = 0.1
    environmental_trigger: str = ""
    stability: float = 0.8


@dataclass(slots=True)
class KarmicRecord:
    id: str
    action: str
    outcome: str  # SUCCESS | FAILURE | NEUTRAL
    impact: float
    generation: int
    lesson: str
    timestamp: float


@dataclass(slots=True)
class ShadowProfile:
    repressed_temperature: float = 0.0
    repressed_tools: list[str] = field(default_factory=list)
    integration_level: float = 0.0
    valence: float = 0.0


@dataclass(slots=True)
class ResonanceSignature:
    frequency: float = 1.0
    amplitude: float = 0.5
    phase: float = 0.0
    harmonics: list[float] = field(default_factory=lambda: [1.0, 1.618, 2.0])


@dataclass(slots=True)
class UnifiedGenomeParams:
    temperature: float = 0.7
    top_p: float = 0.9
    prompt_mutation: str = ""
    tool_weights: dict[str, float] = field(default_factory=lambda: {
        "read_file": 1.0, "write_to_file": 1.0, "edit_file": 1.0,
        "list_dir_glob": 1.0, "web_search": 1.2, "web_fetch": 1.0,
        "run_command": 1.0, "universal_lab": 1.5,
    })
    episodic_retention: float = 0.5
    environmental_sensitivity: float = 0.5
    docker_affinity: float = 0.4
    polyglot_depth: float = 0.3
    resonance_frequency: float = 5.0
    shadow_tolerance: float = 0.5
    karmic_weight: float = 0.35
    epigenetic_sensitivity: float = 0.5
    metamorphic_potential: float = 0.25
    void_attraction: float = 0.35


def _entropy_float() -> float:
    return int.from_bytes(os.urandom(8), "big") / (2 ** 64)


def _gaussian_random(mean: float, stdev: float) -> float:
    u = 1.0 - random.random()
    v = random.random()
    z = math.sqrt(-2.0 * math.log(u)) * math.cos(2.0 * math.pi * v)
    return max(0.0, min(1.0, z * stdev + mean))


class UnifiedGenome:
    """Génome unifié — source unique de vérité pour tous les génomes CIEL.

    Unifie V1 (4 chromosomes × 100 gènes), V2 (épigénome, karma, ombre,
    résonance), V3 Titan (4 chromosomes × 18 432 gènes).
    """

    def __init__(
        self,
        agent_name: str = "genome",
        generation: int = 0,
        params: UnifiedGenomeParams | None = None,
        titan_size: bool = False,
        no_genesis: bool = False,
        initial_fitness: float = 0.0,
        ancestor_ids: list[str] | None = None,
        legacy_v1: bool = False,
    ) -> None:
        self.agent_name = agent_name
        self.generation = generation
        self.fitness = initial_fitness
        self.ancestor_ids = ancestor_ids or []
        self._titan_size = titan_size
        self._legacy_v1 = legacy_v1

        self.id: str = ""
        self.dna_hash: str = ""
        self.fitness_history: list[float] = []
        self.mutation_count: int = 0
        self.faction_id: str | None = None
        self.specialties: list[str] = []
        self.params = params or UnifiedGenomeParams()

        self.g_struct: list[Gene] = []
        self.g_behavior: list[Gene] = []
        self.g_epi: list[Gene] = []
        self.g_meta: list[Gene] = []

        self.epigenome: list[EpigeneticMarker] = []
        self.karmic_ledger: list[KarmicRecord] = []
        self.shadow: ShadowProfile = ShadowProfile()
        self.resonance: ResonanceSignature = ResonanceSignature()
        self.meta_instructions: list[str] = []
        self.is_individuated: bool = False

        if not no_genesis:
            self._init_genesis()

        if not self._legacy_v1:
            self.epigenome = self._initialize_epigenome()
            self.karmic_ledger = []
            self.resonance = ResonanceSignature(
                frequency=self.params.resonance_frequency,
                amplitude=0.5,
                phase=random.random() * math.pi * 2,
                harmonics=[1.0, 1.618, 2.0],
            )
            self.shadow = ShadowProfile(
                repressed_temperature=2.0 - self.params.temperature,
                integration_level=0,
                valence=0,
            )
            self._check_specialties()
            self._update_shadow_profile()
        else:
            self.shadow = ShadowProfile()
            self.resonance = ResonanceSignature()

        self._update_hash()
        if not self._legacy_v1 and not no_genesis:
            self.update_phenotype()

    def _init_genesis(self) -> None:
        sizes = {"struct": 4096, "behavior": 8192, "epi": 2048, "meta": 4096} if self._titan_size \
            else {"struct": 100, "behavior": 100, "epi": 100, "meta": 100}
        for i in range(sizes["struct"]):
            self.g_struct.append(Gene(i, _gaussian_random(0.5, 0.1), ChromosomeType.STRUCT))
        for i in range(sizes["behavior"]):
            self.g_behavior.append(Gene(i, _gaussian_random(0.5, 0.15), ChromosomeType.BEHAVIOR))
        for i in range(sizes["epi"]):
            g = Gene(i, 0.5, ChromosomeType.EPI)
            g.h3k4me3 = 0.3
            g.h3k27me3 = 0.3
            self.g_epi.append(g)
        for i in range(sizes["meta"]):
            self.g_meta.append(Gene(i, _gaussian_random(0.5, 0.05), ChromosomeType.META))

    def _initialize_epigenome(self) -> list[EpigeneticMarker]:
        return [
            EpigeneticMarker("temperature", True, 0.1, "HIGH_CPU", 0.8),
            EpigeneticMarker("polyglotDepth", True, 0.2, "NEW_LANGUAGE", 0.7),
            EpigeneticMarker("dockerAffinity", True, 0.15, "SECURITY_THREAT", 0.9),
            EpigeneticMarker("voidAttraction", True, 0.3, "STAGNATION", 0.5),
            EpigeneticMarker("metamorphicPotential", True, 0.25, "ARCHITECTURAL_CRISIS", 0.6),
        ]

    def _update_hash(self) -> None:
        data = f"{self.agent_name}:{self.generation}"
        sample_size = min(10, len(self.g_struct))
        payload = data
        for i in range(sample_size):
            payload += f"{self.g_struct[i].value:.6f}" if i < len(self.g_struct) else "0.000000"
        h = hashlib.sha256(payload.encode()).hexdigest()[:16]
        self.id = h
        self.dna_hash = h

    def update_phenotype(self) -> None:
        if self._legacy_v1:
            return
        creativity = self.g_behavior[0].express() if self.g_behavior else 0.5
        prudence = self.g_behavior[1].express() if len(self.g_behavior) > 1 else 0.5
        self.params.temperature = 0.1 + creativity * 0.8
        self.params.docker_affinity = self.g_meta[2].express() if len(self.g_meta) > 2 else 0.5
        self.params.polyglot_depth = self.g_meta[3].express() if len(self.g_meta) > 3 else 0.5
        if len(self.g_behavior) > 4:
            self.params.tool_weights = {
                "read_file": self.g_behavior[2].express(),
                "edit_file": self.g_behavior[3].express(),
                "run_command": self.g_behavior[4].express(),
            }
        self.specialties = []
        if creativity > 0.6:
            self.specialties.append("Creative Thinking")
        if prudence > 0.6:
            self.specialties.append("Rigorous Verification")
        if self.g_struct and self.g_struct[0].express() > 0.5:
            self.specialties.append("Deep Architecture")
        mindset = "highly creative and divergent" if creativity > prudence else "highly structured and cautious"
        self.params.prompt_mutation = f"You naturally exhibit a {mindset} mindset."

    def get_phenotype(self) -> dict[str, float]:
        sample_size = min(50, len(self.g_struct))
        epi_sum = sum(self.g_struct[i].express() for i in range(sample_size)) / max(sample_size, 1)
        return {
            "num_layers": len(self.g_struct),
            "exploration_rate": self.g_behavior[0].express() if self.g_behavior else 0.5,
            "creativity_index": self.g_behavior[1].express() if len(self.g_behavior) > 1 else 0.5,
            "risk_tolerance": self.g_behavior[2].express() if len(self.g_behavior) > 2 else 0.5,
            "collaboration_drive": self.g_behavior[3].express() if len(self.g_behavior) > 3 else 0.5,
            "learning_rate": 1e-3,
            "epi_expr": epi_sum,
            "temperature": self.params.temperature,
            "docker_affinity": self.params.docker_affinity,
            "void_attraction": self.params.void_attraction,
            "metamorphic_potential": self.params.metamorphic_potential,
        }

    def express(self, chromosome: ChromosomeType, gene_id: int) -> float:
        gene = self.get_gene(chromosome, gene_id)
        return gene.express() if gene else 0.0

    def get_gene(self, chromosome: ChromosomeType, gene_id: int) -> Gene | None:
        arr = self.get_chromosome(chromosome)
        return arr[gene_id] if 0 <= gene_id < len(arr) else None

    def get_chromosome(self, chromosome: ChromosomeType) -> list[Gene]:
        match chromosome:
            case ChromosomeType.STRUCT:
                return self.g_struct
            case ChromosomeType.BEHAVIOR:
                return self.g_behavior
            case ChromosomeType.EPI:
                return self.g_epi
            case ChromosomeType.META:
                return self.g_meta

    def mutate(self, intensity: float = 0.1) -> None:
        def _mutate_gene(g: Gene) -> None:
            if not g.mutable:
                return
            delta = (random.random() - 0.5) * intensity
            g.value = max(0.0, min(1.0, g.value + delta))
        for g in self.g_struct + self.g_behavior + self.g_epi + self.g_meta:
            _mutate_gene(g)
        self.generation += 1
        self.mutation_count += 1
        self._update_hash()
        self.update_phenotype()

    def mutate_v2(self, rate: float = 0.1) -> None:
        if self._legacy_v1:
            self.mutate(rate)
            return
        mutated = False
        if _entropy_float() < rate:
            self.params.temperature = max(0.0, min(2.0, self.params.temperature + (_entropy_float() * 0.3 - 0.15)))
            mutated = True
        if _entropy_float() < rate:
            self.params.resonance_frequency = max(0.1, min(10.0, self.params.resonance_frequency + (_entropy_float() * 2.0 - 1.0)))
            mutated = True
        if _entropy_float() < rate:
            self.params.shadow_tolerance = max(0.0, min(1.0, self.params.shadow_tolerance + (_entropy_float() * 0.2 - 0.1)))
            mutated = True
        if _entropy_float() < rate:
            self.params.void_attraction = max(0.0, min(1.0, self.params.void_attraction + (_entropy_float() * 0.2 - 0.1)))
            mutated = True
        if _entropy_float() < rate:
            self.params.metamorphic_potential = max(0.0, min(1.0, self.params.metamorphic_potential + (_entropy_float() * 0.2 - 0.1)))
            mutated = True
        if _entropy_float() < rate * 0.5 and self.epigenome:
            marker = random.choice(self.epigenome)
            marker.methylation = max(0.0, min(1.0, marker.methylation + (random.random() * 0.3 - 0.15)))
            marker.active = marker.methylation < 0.5
            mutated = True
        if _entropy_float() < rate * 0.3:
            self.resonance.phase += random.random() * 0.5 - 0.25
            self.resonance.amplitude = max(0.1, min(1.0, self.resonance.amplitude + (random.random() * 0.2 - 0.1)))
            mutated = True
        if mutated:
            self.mutation_count += 1
            self._check_specialties()
            self._update_shadow_profile()

    def mutate_by_strategy(self, target_gene_id: int, chrom: ChromosomeType,
                           strategy: str, gene_bank: Any = None) -> UnifiedGenome:
        genes = self.get_chromosome(chrom)
        if not 0 <= target_gene_id < len(genes):
            return self
        target = genes[target_gene_id]
        match strategy:
            case "gaussian":
                target.value = max(0.0, min(1.0, target.value + (random.random() - 0.5) * 0.1))
            case "epigenetic":
                target.h3k4me3 = 0.9
                target.h3k27me3 = 0.1
                return self
            case "sacrifice":
                target.value = 0.0
            case "transposon":
                sources = [ChromosomeType.STRUCT, ChromosomeType.BEHAVIOR, ChromosomeType.EPI, ChromosomeType.META]
                src = random.choice(sources)
                src_genes = self.get_chromosome(src)
                if src_genes:
                    target.value = random.choice(src_genes).value
            case "bricolage":
                if gene_bank and hasattr(gene_bank, "resurrect_gene"):
                    extinct = gene_bank.resurrect_gene(chrom, target_gene_id)
                    if extinct:
                        target.value = extinct.value
        self._update_hash()
        self.update_phenotype()
        return self

    def crossover(self, other: UnifiedGenome) -> UnifiedGenome:
        child = self.clone()
        child.agent_name = f"{self.agent_name}_{other.agent_name}"
        child.generation = max(self.generation, other.generation) + 1

        def _mix(target: list[Gene], source: list[Gene]) -> None:
            length = min(len(target), len(source))
            for i in range(0, length, 2):
                target[i].value = source[i].value
        _mix(child.g_struct, other.g_struct)
        _mix(child.g_behavior, other.g_behavior)
        _mix(child.g_epi, other.g_epi)
        _mix(child.g_meta, other.g_meta)
        child.fitness = (self.fitness + other.fitness) / 2.0
        child._update_hash()
        child.update_phenotype()
        return child

    def fuse_with(self, other: UnifiedGenome) -> UnifiedGenome:
        fused = self.crossover(other)
        fused.specialties = list(set(self.specialties + other.specialties))
        fused.params.temperature = (self.params.temperature + other.params.temperature) / 2.0
        fused.params.docker_affinity = (self.params.docker_affinity + other.params.docker_affinity) / 2.0
        fused.params.polyglot_depth = (self.params.polyglot_depth + other.params.polyglot_depth) / 2.0
        fused.params.tool_weights = {**self.params.tool_weights, **other.params.tool_weights}
        return fused

    def record_karma(self, action: str, outcome: str, impact: float, lesson: str) -> None:
        self.karmic_ledger.append(KarmicRecord(
            id=f"karma_{time.time()}_{random.randint(0, 999):03d}",
            action=action, outcome=outcome, impact=impact,
            generation=self.generation, lesson=lesson, timestamp=time.time(),
        ))
        if len(self.karmic_ledger) > 100:
            self.karmic_ledger = self.karmic_ledger[-50:]

    def consult_karma(self, proposed_action: str) -> dict[str, Any]:
        prefix = proposed_action.lower().split(" ")[0] if proposed_action else ""
        relevant = [k for k in self.karmic_ledger if prefix in k.action.lower()]
        if not relevant:
            return {"bias": 0.0, "wisdom": "No karmic precedent for this action."}
        successes = sum(1 for k in relevant if k.outcome == "SUCCESS")
        failures = sum(1 for k in relevant if k.outcome == "FAILURE")
        bias = (successes - failures) / len(relevant) * self.params.karmic_weight
        best = max(relevant, key=lambda k: abs(k.impact))
        return {"bias": bias, "wisdom": best.lesson or "Karmic records are ambiguous."}

    def apply_epigenetic_trigger(self, trigger: str) -> None:
        for marker in self.epigenome:
            if marker.environmental_trigger == trigger and _entropy_float() < 0.3:
                marker.active = not marker.active
                marker.methylation = 0.1 if marker.active else 0.9
                if marker.gene == "temperature" and not marker.active:
                    self.params.temperature *= 0.8
                if marker.gene == "voidAttraction" and marker.active:
                    self.params.void_attraction = min(1.0, self.params.void_attraction + 0.1)

    def compute_resonance_with(self, other: UnifiedGenome) -> float:
        freq_ratio = self.resonance.frequency / (other.resonance.frequency + 0.01)
        harmonic_ratios = [1.0, 1.5, 1.618, 2.0, 3.0]
        max_resonance = 0.0
        for hr in harmonic_ratios:
            deviation = abs(freq_ratio - hr) / hr
            if deviation < 0.15:
                max_resonance = max(max_resonance, 1.0 - deviation * 5.0)
        phase_alignment = math.cos(self.resonance.phase - other.resonance.phase)
        return max_resonance * 0.7 + (phase_alignment * 0.5 + 0.5) * 0.3

    def _update_shadow_profile(self) -> None:
        if self._legacy_v1:
            return
        self.shadow.repressed_temperature = 2.0 - self.params.temperature
        entries = list(self.params.tool_weights.items())
        avg = sum(w for _, w in entries) / max(len(entries), 1)
        self.shadow.repressed_tools = [t for t, w in entries if w < avg]
        temp_delta = abs(self.shadow.repressed_temperature - self.params.temperature)
        self.shadow.valence = -0.5 if temp_delta > 1.0 else 0.5
        self.shadow.integration_level = self.params.shadow_tolerance

    def _check_specialties(self) -> None:
        if self._legacy_v1:
            return
        for tool, weight in self.params.tool_weights.items():
            if weight > 1.8 and f"Master of {tool}" not in self.specialties:
                self.specialties.append(f"Master of {tool}")
        if self.params.temperature > 1.5 and "Creative Chaos" not in self.specialties:
            self.specialties.append("Creative Chaos")
        if self.params.temperature < 0.2 and "Absolute Logic" not in self.specialties:
            self.specialties.append("Absolute Logic")
        if self.params.void_attraction > 0.7 and "Void Walker" not in self.specialties:
            self.specialties.append("Void Walker")
        if self.params.metamorphic_potential > 0.7 and "Meta-Architect" not in self.specialties:
            self.specialties.append("Meta-Architect")
        if self.params.shadow_tolerance > 0.8 and "Shadow Integrated" not in self.specialties:
            self.specialties.append("Shadow Integrated")
        if self.params.resonance_frequency > 8.0 and "High Frequency Resonator" not in self.specialties:
            self.specialties.append("High Frequency Resonator")
        if len(self.karmic_ledger) > 20 and "Karmic Sage" not in self.specialties:
            self.specialties.append("Karmic Sage")

    def clone(self) -> UnifiedGenome:
        copy = UnifiedGenome(
            agent_name=self.agent_name, generation=self.generation,
            params=UnifiedGenomeParams(
                temperature=self.params.temperature, top_p=self.params.top_p,
                prompt_mutation=self.params.prompt_mutation,
                tool_weights=dict(self.params.tool_weights),
                episodic_retention=self.params.episodic_retention,
                environmental_sensitivity=self.params.environmental_sensitivity,
                docker_affinity=self.params.docker_affinity,
                polyglot_depth=self.params.polyglot_depth,
                resonance_frequency=self.params.resonance_frequency,
                shadow_tolerance=self.params.shadow_tolerance,
                karmic_weight=self.params.karmic_weight,
                epigenetic_sensitivity=self.params.epigenetic_sensitivity,
                metamorphic_potential=self.params.metamorphic_potential,
                void_attraction=self.params.void_attraction,
            ),
            titan_size=self._titan_size, legacy_v1=self._legacy_v1,
            ancestor_ids=list(self.ancestor_ids), no_genesis=True,
        )
        copy.specialties = list(self.specialties)
        copy.fitness = self.fitness
        return copy

    def serialize(self) -> str:
        return json.dumps({
            "id": self.id, "name": self.agent_name, "generation": self.generation,
            "fitness": self.fitness, "traits": self.specialties,
            "chromosomes": {"struct": len(self.g_struct), "behavior": len(self.g_behavior),
                            "epi": len(self.g_epi), "meta": len(self.g_meta)},
            "karmicLedgerSize": len(self.karmic_ledger),
        })

    @staticmethod
    def deserialize(data: str) -> UnifiedGenome:
        obj = json.loads(data)
        return UnifiedGenome(agent_name=obj.get("name", "genome"),
                             generation=obj.get("generation", 0),
                             initial_fitness=obj.get("fitness", 0.0))

    def fitness_score(self) -> float:
        if not self.fitness_history:
            return self.fitness or 0.5
        recent = self.fitness_history[-10:]
        return sum(recent) / len(recent)

    def is_titan_size(self) -> bool:
        return self._titan_size

    def is_legacy_v1(self) -> bool:
        return self._legacy_v1
