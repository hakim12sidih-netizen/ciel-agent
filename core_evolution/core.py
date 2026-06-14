from __future__ import annotations

import hashlib
import math
import random
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


# ── SystemBus ──────────────────────────────────────────────────────────────

class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass(slots=True)
class Event:
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class SystemBus:
    """Bus d'événements — communication inter-composants."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = {}
        self._history: list[Event] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        handlers = self._handlers.get(event_type)
        if handlers and handler in handlers:
            handlers.remove(handler)
            return True
        return False

    def emit(self, event_type: str, data: dict[str, Any] | None = None,
             source: str = "", priority: EventPriority = EventPriority.NORMAL) -> Event:
        event = Event(type=event_type, data=data or {}, source=source, priority=priority)
        self._history.append(event)
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception:
                pass
        return event

    def history(self, event_type: str | None = None) -> list[Event]:
        if event_type:
            return [e for e in self._history if e.type == event_type]
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()


# ── TitanNVM (Neural Virtual Machine) ─────────────────────────────────────

@dataclass(slots=True)
class MemoryBlock:
    key: str
    value: Any
    timestamp: float = 0.0
    ttl_s: float = 0.0
    tags: list[str] = field(default_factory=list)
    weight: float = 1.0

    def expired(self) -> bool:
        if self.ttl_s <= 0:
            return False
        return time.time() - self.timestamp > self.ttl_s


class TitanNVM:
    """Mémoire persistante — Neural Virtual Machine."""

    def __init__(self) -> None:
        self._blocks: dict[str, MemoryBlock] = {}
        self._tags: dict[str, set[str]] = {}

    def store(self, key: str, value: Any, tags: list[str] | None = None,
              ttl_s: float = 0.0, weight: float = 1.0) -> None:
        block = MemoryBlock(
            key=key, value=value, timestamp=time.time(),
            ttl_s=ttl_s, tags=tags or [], weight=weight,
        )
        self._blocks[key] = block
        for tag in (tags or []):
            self._tags.setdefault(tag, set()).add(key)

    def load(self, key: str) -> Any | None:
        block = self._blocks.get(key)
        if block is None or block.expired():
            return None
        return block.value

    def delete(self, key: str) -> bool:
        block = self._blocks.pop(key, None)
        if block:
            for tag in block.tags:
                self._tags.get(tag, set()).discard(key)
            return True
        return False

    def query(self, tag: str) -> list[MemoryBlock]:
        keys = self._tags.get(tag, set())
        return [self._blocks[k] for k in keys if k in self._blocks and not self._blocks[k].expired()]

    def prune(self) -> int:
        expired = [k for k, b in self._blocks.items() if b.expired()]
        for k in expired:
            self.delete(k)
        return len(expired)

    def clear(self) -> None:
        self._blocks.clear()
        self._tags.clear()

    def size(self) -> int:
        return len(self._blocks)


# ── Pantheon — Olympian Agents ─────────────────────────────────────────────

class AgentRole(Enum):
    ZEUS = "zeus"
    ATHENA = "athena"
    HEPHAESTUS = "hephaestus"
    LLMBRIDGE = "llmbridge"
    APOLLO = "apollo"
    ARTEMIS = "artemis"
    POSEIDON = "poseidon"
    HADES = "hades"
    ARES = "ares"
    DEMETER = "demeter"
    DIONYSUS = "dionysus"


AGENT_DESCRIPTIONS: dict[AgentRole, str] = {
    AgentRole.ZEUS: "arbitre suprême, décision finale, validation consensus",
    AgentRole.ATHENA: "sagesse, stratégie, planification long-terme",
    AgentRole.HEPHAESTUS: "ingénierie, outils, forge de solutions",
    AgentRole.LLMBRIDGE: "communication, messager, inter-plateforme",
    AgentRole.APOLLO: "connaissance, arts, clarté, raisonnement",
    AgentRole.ARTEMIS: "analyse, perception, vigilance, précision",
    AgentRole.POSEIDON: "exploration, données, flux, adaptabilité",
    AgentRole.HADES: "archives, mémoire cachée, profondeur",
    AgentRole.ARES: "exécution, action, performance, confrontation",
    AgentRole.DEMETER: "croissance, apprentissage, nurture, itération",
    AgentRole.DIONYSUS: "créativité, intuition, pensée latérale",
}


@dataclass(slots=True)
class AgentProposal:
    agent: AgentRole
    proposal: str
    confidence: float
    reasoning: str = ""
    tags: list[str] = field(default_factory=list)
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass(slots=True)
class ConsensusResult:
    accepted: bool
    final_proposal: str
    confidence: float
    votes: dict[str, float]
    reasoning: str = ""


class Pantheon:
    """Panthéon des agents Olympiens — 11 rôles spécialisés."""

    def __init__(self, bus: SystemBus | None = None) -> None:
        self.bus = bus or SystemBus()
        self._agents: dict[AgentRole, dict[str, Any]] = {
            role: {
                "role": role,
                "name": role.value.capitalize(),
                "description": AGENT_DESCRIPTIONS[role],
                "active": True,
                "expertise": self._expertise_for(role),
            }
            for role in AgentRole
        }

    @staticmethod
    def _expertise_for(role: AgentRole) -> list[str]:
        expertise_map: dict[AgentRole, list[str]] = {
            AgentRole.ZEUS: ["gouvernance", "validation", "arbitrage", "méta"],
            AgentRole.ATHENA: ["stratégie", "planification", "sagesse", "éthique"],
            AgentRole.HEPHAESTUS: ["ingénierie", "outils", "infrastructure", "robotique"],
            AgentRole.LLMBRIDGE: ["communication", "réseau", "traduction", "messagerie"],
            AgentRole.APOLLO: ["connaissance", "logique", "arts", "vérité"],
            AgentRole.ARTEMIS: ["perception", "analyse", "surveillance", "précision"],
            AgentRole.POSEIDON: ["exploration", "données", "adaptation", "flux"],
            AgentRole.HADES: ["mémoire", "archives", "profondeur", "legacy"],
            AgentRole.ARES: ["action", "exécution", "performance", "défense"],
            AgentRole.DEMETER: ["croissance", "apprentissage", "itération", "nurture"],
            AgentRole.DIONYSUS: ["créativité", "intuition", "divergence", "jeu"],
        }
        return expertise_map.get(role, ["general"])

    def get_agent(self, role: AgentRole) -> dict[str, Any] | None:
        return self._agents.get(role)

    def list_agents(self, active_only: bool = True) -> list[dict[str, Any]]:
        agents = list(self._agents.values())
        if active_only:
            agents = [a for a in agents if a["active"]]
        return agents

    def activate(self, role: AgentRole) -> None:
        if role in self._agents:
            self._agents[role]["active"] = True
            self.bus.emit("pantheon.activate", {"role": role.value})

    def deactivate(self, role: AgentRole) -> None:
        if role in self._agents:
            self._agents[role]["active"] = False
            self.bus.emit("pantheon.deactivate", {"role": role.value})

    def propose(self, role: AgentRole, proposal: str, confidence: float,
                reasoning: str = "", tags: list[str] | None = None) -> AgentProposal:
        p = AgentProposal(
            agent=role, proposal=proposal, confidence=confidence,
            reasoning=reasoning, tags=tags or [],
        )
        self.bus.emit("pantheon.proposal", {
            "agent": role.value, "proposal": proposal, "confidence": confidence,
        })
        return p

    def bcq_consensus(self, proposals: list[AgentProposal]) -> ConsensusResult:
        """BCQ (Bus Quantique de Cohérence) — mécanisme de consensus."""
        active_roles = {a["role"] for a in self.list_agents()}
        relevant = [p for p in proposals if p.agent in active_roles]
        if not relevant:
            return ConsensusResult(accepted=False, final_proposal="", confidence=0.0, votes={})

        total_confidence = sum(p.confidence for p in relevant)
        if total_confidence == 0:
            return ConsensusResult(accepted=False, final_proposal="", confidence=0.0, votes={})

        votes: dict[str, float] = {}
        for p in relevant:
            weight = p.confidence / total_confidence
            votes[p.agent.value] = weight

        best = max(relevant, key=lambda p: p.confidence)
        avg_confidence = sum(p.confidence for p in relevant) / len(relevant)

        zeus = self.get_agent(AgentRole.ZEUS)
        zeus_bonus = 1.2 if zeus and zeus["active"] else 1.0
        final_confidence = min(1.0, avg_confidence * zeus_bonus)

        accepted = final_confidence >= 0.5
        self.bus.emit("pantheon.consensus", {
            "accepted": accepted, "confidence": final_confidence,
            "winner": best.agent.value, "votes": votes,
        })

        return ConsensusResult(
            accepted=accepted,
            final_proposal=best.proposal,
            confidence=final_confidence,
            votes=votes,
            reasoning=f"BCQ consensus: {len(relevant)} agents, best={best.agent.value}",
        )


# ── SkillGraph ─────────────────────────────────────────────────────────────

@dataclass(slots=True)
class SkillNode:
    id: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    complexity: float = 1.0
    usage_count: int = 0
    last_used: float = 0.0
    dependencies: list[str] = field(default_factory=list)

    def activate(self) -> None:
        self.usage_count += 1
        self.last_used = time.time()


class SkillGraph:
    """Graphe orienté de skills — sélection et activation."""

    def __init__(self) -> None:
        self._nodes: dict[str, SkillNode] = {}

    def register(self, skill_id: str, name: str, description: str = "",
                 tags: list[str] | None = None, complexity: float = 1.0,
                 dependencies: list[str] | None = None) -> SkillNode:
        node = SkillNode(
            id=skill_id, name=name, description=description,
            tags=tags or [], complexity=complexity,
            dependencies=dependencies or [],
        )
        self._nodes[skill_id] = node
        return node

    def get(self, skill_id: str) -> SkillNode | None:
        return self._nodes.get(skill_id)

    def unregister(self, skill_id: str) -> bool:
        return self._nodes.pop(skill_id, None) is not None

    def select(self, tags: list[str], max_complexity: float = 10.0) -> list[SkillNode]:
        candidates = [
            n for n in self._nodes.values()
            if any(t in n.tags for t in tags) and n.complexity <= max_complexity
        ]
        candidates.sort(key=lambda n: (-n.usage_count, n.complexity))
        return candidates

    def traverse(self, start_id: str, max_depth: int = 3) -> list[SkillNode]:
        visited: set[str] = set()
        result: list[SkillNode] = []

        def dfs(sid: str, depth: int) -> None:
            if depth > max_depth or sid in visited:
                return
            visited.add(sid)
            node = self._nodes.get(sid)
            if node:
                result.append(node)
                for dep in node.dependencies:
                    dfs(dep, depth + 1)

        dfs(start_id, 0)
        return result

    def prune(self, max_age_s: float = 86400 * 30) -> int:
        now = time.time()
        stale = [k for k, n in self._nodes.items()
                 if n.usage_count == 0 and now - n.last_used > max_age_s]
        for k in stale:
            self._nodes.pop(k, None)
        return len(stale)

    def all(self) -> list[SkillNode]:
        return list(self._nodes.values())


# ── ThoughtTree ────────────────────────────────────────────────────────────

class ThoughtType(Enum):
    OBSERVE = auto()
    ORIENT = auto()
    DECIDE = auto()
    ACT = auto()
    REFLECT = auto()


@dataclass(slots=True)
class Thought:
    id: str
    type: ThoughtType
    content: str
    confidence: float = 1.0
    children: list[str] = field(default_factory=list)
    parent: str | None = None
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class ThoughtTree:
    """Arbre de raisonnement hiérarchique — OODA loop."""

    def __init__(self) -> None:
        self._thoughts: dict[str, Thought] = {}
        self._root: str | None = None

    def add_thought(self, type_: ThoughtType, content: str,
                    confidence: float = 1.0, parent: str | None = None) -> Thought:
        thought = Thought(
            id=str(uuid.uuid4()), type=type_, content=content,
            confidence=confidence, parent=parent,
        )
        self._thoughts[thought.id] = thought

        if parent and parent in self._thoughts:
            self._thoughts[parent].children.append(thought.id)
        if self._root is None:
            self._root = thought.id

        return thought

    def get(self, thought_id: str) -> Thought | None:
        return self._thoughts.get(thought_id)

    def path_from_root(self, thought_id: str) -> list[Thought]:
        path: list[Thought] = []
        current = thought_id
        while current and current in self._thoughts:
            path.append(self._thoughts[current])
            current = self._thoughts[current].parent or ""
        path.reverse()
        return path

    def traverse(self, start_id: str | None = None) -> list[Thought]:
        start = start_id or self._root
        if start is None or start not in self._thoughts:
            return []

        visited: list[Thought] = []

        def dfs(sid: str) -> None:
            thought = self._thoughts.get(sid)
            if thought is None or thought in visited:
                return
            visited.append(thought)
            for cid in thought.children:
                dfs(cid)

        dfs(start)
        return visited

    def leaf_count(self) -> int:
        return sum(1 for t in self._thoughts.values() if not t.children)

    def depth(self) -> int:
        if self._root is None:
            return 0

        def max_depth(sid: str) -> int:
            thought = self._thoughts.get(sid)
            if thought is None or not thought.children:
                return 1
            return 1 + max(max_depth(c) for c in thought.children)

        return max_depth(self._root)


# ── UnifiedGenome ─────────────────────────────────────────────────────────

class Chromosome(Enum):
    STRUCT = "struct"
    BEHAVIOR = "behavior"
    EPI = "epigenetic"
    META = "meta"


@dataclass(slots=True)
class Gene:
    id: str
    chromosome: Chromosome
    value: float
    min_val: float = -1.0
    max_val: float = 1.0
    mutable: bool = True
    expression: float = 1.0

    def mutate(self, rate: float = 0.15, amplitude: float = 0.1) -> None:
        if not self.mutable:
            return
        if random.random() < rate:
            delta = random.gauss(0, amplitude)
            self.value = max(self.min_val, min(self.max_val, self.value + delta))
            self.expression = max(0.0, min(1.0, self.expression + random.gauss(0, 0.05)))


@dataclass(slots=True)
class UnifiedGenome:
    id: str
    name: str = ""
    genes: dict[str, Gene] = field(default_factory=dict)
    fitness: float = 0.0
    generation: int = 0
    parent_ids: list[str] = field(default_factory=list)
    karma: float = 0.0
    species: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(name: str = "", n_genes: int = 100, generation: int = 0) -> UnifiedGenome:
        genome = UnifiedGenome(
            id=str(uuid.uuid4()), name=name, generation=generation,
        )
        chromosomes = list(Chromosome)
        for i in range(n_genes):
            chrom = chromosomes[i % len(chromosomes)]
            gene = Gene(
                id=f"gene_{i}", chromosome=chrom,
                value=random.gauss(0, 0.5),
                mutable=random.random() > 0.1,
            )
            genome.genes[gene.id] = gene
        return genome

    def mutate(self, rate: float = 0.15, amplitude: float = 0.1) -> None:
        for gene in self.genes.values():
            gene.mutate(rate, amplitude)
        self.karma += random.gauss(0, 0.01)

    def crossover(self, other: UnifiedGenome) -> UnifiedGenome:
        child = UnifiedGenome(
            id=str(uuid.uuid4()),
            name=f"{self.name}_{other.name}",
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.id, other.id],
            karma=(self.karma + other.karma) / 2,
        )
        for gid, gene in self.genes.items():
            if gid in other.genes:
                parent_genes = [gene, other.genes[gid]]
                chosen = random.choice(parent_genes)
                child.genes[gid] = Gene(
                    id=gid, chromosome=chosen.chromosome,
                    value=chosen.value, min_val=chosen.min_val,
                    max_val=chosen.max_val, mutable=chosen.mutable,
                    expression=(gene.expression + other.genes[gid].expression) / 2,
                )
            else:
                child.genes[gid] = Gene(
                    id=gid, chromosome=gene.chromosome, value=gene.value,
                    min_val=gene.min_val, max_val=gene.max_val,
                    mutable=gene.mutable, expression=gene.expression,
                )
        child.mutate()
        return child

    def distance_to(self, other: UnifiedGenome) -> float:
        common = set(self.genes) & set(other.genes)
        if not common:
            return 1.0
        squared_diffs = sum(
            (self.genes[gid].value - other.genes[gid].value) ** 2
            for gid in common
        )
        return math.sqrt(squared_diffs / len(common))

    def chromosome_summary(self) -> dict[str, float]:
        summary: dict[str, float] = {}
        for chrom in Chromosome:
            vals = [g.value for g in self.genes.values() if g.chromosome == chrom]
            summary[chrom.value] = sum(vals) / len(vals) if vals else 0.0
        return summary


# ── ImperialCycle — Evolution Loop ─────────────────────────────────────────

class ImperialCycle:
    """Cycle de reproduction impérial — évolution darwinienne."""

    def __init__(self, population_size: int = 100, elite_fraction: float = 0.1,
                 mutation_rate: float = 0.15, n_genes: int = 100) -> None:
        self.population_size = population_size
        self.elite_fraction = elite_fraction
        self.mutation_rate = mutation_rate
        self.n_genes = n_genes
        self.generation = 0
        self.population: list[UnifiedGenome] = []
        self._history: list[dict[str, Any]] = []
        self._fitness_fn: Callable[[UnifiedGenome], float] | None = None

    def set_fitness_fn(self, fn: Callable[[UnifiedGenome], float]) -> None:
        self._fitness_fn = fn

    def initialize(self) -> None:
        self.population = [
            UnifiedGenome.create(name=f"genome_{i}", n_genes=self.n_genes)
            for i in range(self.population_size)
        ]

    def evaluate(self, genome: UnifiedGenome) -> float:
        if self._fitness_fn:
            return self._fitness_fn(genome)
        return random.random()

    def step(self) -> dict[str, Any]:
        if not self.population:
            self.initialize()

        for g in self.population:
            g.fitness = self.evaluate(g)

        sorted_pop = sorted(self.population, key=lambda g: -g.fitness)
        n_elite = max(1, int(self.population_size * self.elite_fraction))
        elite = sorted_pop[:n_elite]

        children: list[UnifiedGenome] = list(elite)
        while len(children) < self.population_size:
            p1 = random.choice(elite)
            p2 = random.choice(elite)
            child = p1.crossover(p2)
            children.append(child)

        self.population = children[:self.population_size]
        self.generation += 1

        best_fitness = elite[0].fitness if elite else 0.0
        avg_fitness = sum(g.fitness for g in self.population) / len(self.population)
        diversity = self._compute_diversity()

        record = {
            "generation": self.generation,
            "best_fitness": best_fitness,
            "avg_fitness": avg_fitness,
            "diversity": diversity,
            "n_elite": n_elite,
        }
        self._history.append(record)
        return record

    def _compute_diversity(self) -> float:
        if len(self.population) < 2:
            return 0.0
        ref = self.population[0]
        distances = [ref.distance_to(g) for g in self.population[1:]]
        return sum(distances) / len(distances)

    def get_best(self) -> UnifiedGenome | None:
        if not self.population:
            return None
        return max(self.population, key=lambda g: g.fitness)

    def history(self) -> list[dict[str, Any]]:
        return list(self._history)


# ── MetamorphicCore — Self-Rewriting ──────────────────────────────────────

class Aegis:
    """Vérification de code — gardien des mutations."""

    FORBIDDEN = {"eval", "exec", "__import__", "compile", "open"}

    @staticmethod
    def verify(code: str) -> tuple[bool, list[str]]:
        issues: list[str] = []
        for forbidden in Aegis.FORBIDDEN:
            if forbidden in code:
                issues.append(f"API interdite: {forbidden}")
        lines = code.split("\n")
        if any(len(line) > 200 for line in lines):
            issues.append("ligne > 200 caractères")
        complexity = sum(line.count("if ") + line.count("for ") + line.count("while ") for line in lines)
        if complexity > 50:
            issues.append(f"complexité trop élevée ({complexity})")
        return len(issues) == 0, issues


@dataclass(slots=True)
class MutationPatch:
    id: str
    target_file: str
    original_code: str
    patched_code: str
    description: str = ""
    status: str = "pending"
    timestamp: float = 0.0
    incubation_s: float = 30.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def apply(self) -> bool:
        self.status = "applied"
        return True

    def rollback(self) -> bool:
        self.status = "rolled_back"
        return True


class MetamorphicCore:
    """Architecture d'auto-réécriture — introspect → vision → forge → verify → transmute → incubate."""

    def __init__(self, aegis: Aegis | None = None) -> None:
        self.aegis = aegis or Aegis()
        self._patches: list[MutationPatch] = []
        self._active = True
        self._mutation_count = 0

    def propose(self, target_file: str, original: str, patched: str,
                description: str = "") -> MutationPatch | None:
        valid, issues = self.aegis.verify(patched)
        if not valid:
            return None
        patch = MutationPatch(
            id=str(uuid.uuid4()), target_file=target_file,
            original_code=original, patched_code=patched,
            description=description, status="pending",
        )
        self._patches.append(patch)
        return patch

    def apply(self, patch_id: str) -> bool:
        patch = self._get(patch_id)
        if patch is None or patch.status != "pending":
            return False
        patch.apply()
        self._mutation_count += 1
        return True

    def rollback(self, patch_id: str) -> bool:
        patch = self._get(patch_id)
        if patch is None or patch.status != "applied":
            return False
        patch.rollback()
        return True

    def _get(self, patch_id: str) -> MutationPatch | None:
        for p in self._patches:
            if p.id == patch_id:
                return p
        return None

    def pending_patches(self) -> list[MutationPatch]:
        return [p for p in self._patches if p.status == "pending"]

    def history(self) -> list[MutationPatch]:
        return list(self._patches)

    def mutation_count(self) -> int:
        return self._mutation_count


# ── TitanRL ─────────────────────────────────────────────────────────────────

@dataclass(slots=True)
class RewardVector:
    success: float = 0.0
    efficiency: float = 0.0
    novelty: float = 0.0
    robustness: float = 0.0
    frugality: float = 0.0
    speed: float = 0.0
    autonomy: float = 0.0
    symbiosis: float = 0.0
    curiosity: float = 0.0
    safety: float = 0.0
    evolution: float = 0.0
    pleasure: float = 0.0

    def total(self) -> float:
        return sum([
            self.success, self.efficiency, self.novelty, self.robustness,
            self.frugality, self.speed, self.autonomy, self.symbiosis,
            self.curiosity, self.safety, self.evolution, self.pleasure,
        ]) / 12.0

    def to_dict(self) -> dict[str, float]:
        return {
            "success": self.success, "efficiency": self.efficiency,
            "novelty": self.novelty, "robustness": self.robustness,
            "frugality": self.frugality, "speed": self.speed,
            "autonomy": self.autonomy, "symbiosis": self.symbiosis,
            "curiosity": self.curiosity, "safety": self.safety,
            "evolution": self.evolution, "pleasure": self.pleasure,
        }


class TitanRL:
    """Moteur RL 12 dimensions — policy gradient."""

    def __init__(self, learning_rate: float = 0.01, gamma: float = 0.95):
        self.lr = learning_rate
        self.gamma = gamma
        self._weights: dict[str, float] = {
            k: random.gauss(0, 0.1) for k in RewardVector().to_dict()
        }
        self._episodes: list[dict[str, Any]] = []

    def evaluate(self, reward: RewardVector) -> float:
        score = sum(self._weights[k] * v for k, v in reward.to_dict().items())
        return score

    def update(self, reward: RewardVector, trajectory: list[RewardVector] | None = None) -> dict[str, float]:
        total = reward.total()
        for key in self._weights:
            delta = self.lr * (getattr(reward, key) - self._weights[key])
            self._weights[key] += delta

        episode = {
            "reward": reward.to_dict(),
            "total": total,
            "weights": dict(self._weights),
        }
        self._episodes.append(episode)
        return episode

    def get_weights(self) -> dict[str, float]:
        return dict(self._weights)


# ── EvolutionBrain — OODA Loop ─────────────────────────────────────────────────

class EvolutionBrain:
    """Cerveau cortical — cycle OODA (Observe-Orient-Decide-Act)."""

    def __init__(self, pantheon: Pantheon | None = None,
                 skill_graph: SkillGraph | None = None,
                 thought_tree: ThoughtTree | None = None) -> None:
        self.pantheon = pantheon or Pantheon()
        self.skills = skill_graph or SkillGraph()
        self.thoughts = thought_tree or ThoughtTree()
        self._cycle_count = 0

    def observe(self, data: dict[str, Any]) -> Thought:
        self._cycle_count += 1
        thought = self.thoughts.add_thought(
            ThoughtType.OBSERVE, content=str(data),
            confidence=1.0,
        )
        return thought

    def orient(self, observation: Thought) -> Thought:
        context_size = len(observation.content)
        confidence = min(1.0, context_size / 1000)
        oriented = self.thoughts.add_thought(
            ThoughtType.ORIENT,
            content=f"orienté depuis: {observation.content[:100]}",
            confidence=confidence,
            parent=observation.id,
        )
        return oriented

    def decide(self, oriented: Thought, tags: list[str] | None = None) -> Thought:
        tags = tags or ["general"]
        skill_nodes = self.skills.select(tags)
        proposals: list[AgentProposal] = []
        for agent in self.pantheon.list_agents():
            conf = random.uniform(0.3, 0.9)
            proposals.append(AgentProposal(
                agent=agent["role"],
                proposal=f"decision via {agent['name']}",
                confidence=conf,
                tags=tags,
            ))
        consensus = self.pantheon.bcq_consensus(proposals) if len(proposals) > 1 else None
        decision_content = consensus.final_proposal if consensus else "decision directe"
        decision = self.thoughts.add_thought(
            ThoughtType.DECIDE,
            content=decision_content,
            confidence=consensus.confidence if consensus else 0.5,
            parent=oriented.id,
        )
        return decision

    def act(self, decision: Thought) -> Thought:
        action = self.thoughts.add_thought(
            ThoughtType.ACT,
            content=f"action basée sur: {decision.content[:100]}",
            confidence=decision.confidence,
            parent=decision.id,
        )
        return action

    def reflect(self, action: Thought) -> Thought:
        reflection = self.thoughts.add_thought(
            ThoughtType.REFLECT,
            content=f"réflexion sur cycle {self._cycle_count}",
            confidence=min(1.0, self._cycle_count * 0.1),
            parent=action.id,
        )
        return reflection

    def full_cycle(self, data: dict[str, Any]) -> dict[str, Any]:
        obs = self.observe(data)
        ori = self.orient(obs)
        dec = self.decide(ori)
        act = self.act(dec)
        ref = self.reflect(act)
        return {
            "cycle": self._cycle_count,
            "observe": obs.id,
            "orient": ori.id,
            "decide": dec.id,
            "act": act.id,
            "reflect": ref.id,
            "thought_depth": self.thoughts.depth(),
            "leaf_count": self.thoughts.leaf_count(),
        }


# ── CoreEvolutionEngine — entry point principal ────────────────────────────────────

class CoreEvolutionEngine:
    """Moteur CIEL complet — Darwinian Evolution, Pantheon, RL, Self-Rewriting.

    Intègre:
    - Pantheon: 11 agents Olympiens + consensus BCQ
    - EvolutionBrain: cycle OODA
    - ImperialCycle: évolution darwinienne
    - TitanRL: RL 12 dimensions
    - MetamorphicCore: auto-réécriture supervisée
    - SkillGraph: graphe de skills
    - ThoughtTree: raisonnement hiérarchique
    - SystemBus: événements
    - TitanNVM: mémoire persistante
    """

    def __init__(self) -> None:
        self.bus = SystemBus()
        self.memory = TitanNVM()
        self.pantheon = Pantheon(bus=self.bus)
        self.skills = SkillGraph()
        self.thoughts = ThoughtTree()
        self.brain = EvolutionBrain(
            pantheon=self.pantheon, skill_graph=self.skills,
            thought_tree=self.thoughts,
        )
        self.evolution = ImperialCycle()
        self.rl = TitanRL()
        self.metamorph = MetamorphicCore()
        self._start_time = time.time()

    def ooda_cycle(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.brain.full_cycle(data)

    def evolution_step(self) -> dict[str, Any]:
        return self.evolution.step()

    def train_rl(self, reward: RewardVector) -> dict[str, float]:
        return self.rl.update(reward)

    def propose_mutation(self, target: str, original: str,
                         patched: str, description: str = "") -> MutationPatch | None:
        return self.metamorph.propose(target, original, patched, description)

    def get_uptime(self) -> float:
        return time.time() - self._start_time

    def get_stats(self) -> dict[str, Any]:
        return {
            "uptime_s": self.get_uptime(),
            "generation": self.evolution.generation,
            "population": len(self.evolution.population),
            "agents_active": len(self.pantheon.list_agents()),
            "skills": len(self.skills.all()),
            "thoughts": len(self.thoughts.traverse()),
            "mutations": self.metamorph.mutation_count(),
            "rl_episodes": len(self.rl._episodes),
            "memory_blocks": self.memory.size(),
            "bus_events": len(self.bus.history()),
            "cycles": self.brain._cycle_count,
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "ooda")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "ooda":
            result = self.ooda_cycle(data)
            return {"success": True, "action": "ooda", "result": result}
        elif action == "evolve":
            result = self.evolution_step()
            return {"success": True, "action": "evolve", "result": result}
        elif action == "rl":
            reward = RewardVector(**{k: float(v) for k, v in data.items() if k in RewardVector().to_dict()})
            result = self.train_rl(reward)
            return {"success": True, "action": "rl", "result": result}
        elif action == "mutate":
            patch = self.propose_mutation(
                data.get("target", ""), data.get("original", ""),
                data.get("patched", ""), data.get("description", ""),
            )
            return {"success": patch is not None, "action": "mutate", "patch_id": patch.id if patch else None}
        elif action == "propose":
            role_name = data.get("agent", "zeus")
            try:
                role = AgentRole(role_name)
            except ValueError:
                return {"success": False, "error": f"unknown agent: {role_name}"}
            proposal = self.pantheon.propose(
                role, data.get("proposal", ""),
                float(data.get("confidence", 0.5)),
                data.get("reasoning", ""),
            )
            return {"success": True, "action": "propose", "proposal": proposal}
        elif action == "consensus":
            proposals = [AgentProposal(
                agent=AgentRole(p.get("agent", "zeus")),
                proposal=p.get("proposal", ""),
                confidence=float(p.get("confidence", 0.5)),
            ) for p in data.get("proposals", []) if "agent" in p]
            if not proposals:
                return {"success": False, "error": "no proposals"}
            result = self.pantheon.bcq_consensus(proposals)
            return {"success": True, "action": "consensus", "result": result}
        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
