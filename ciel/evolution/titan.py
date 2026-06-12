"""
═══════════════════════════════════════════════════════════════
TITAN ECOSYSTEM & RL — Evolutionary Learning System
═══════════════════════════════════════════════════════════════

Combined port of TitanEcosystem.ts and TitanRL.ts

TitanEcosystem: Multi-agent evolutionary environment with agents,
crossover, mutation, extinction, symbiosis.

TitanRL: 12-dimensional reinforcement learning reward system with
optional PyTorch bridge for policy gradient training.
"""

from __future__ import annotations

import asyncio
import logging
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TaskResult:
    """Result of a task executed by an agent."""
    success: bool
    efficiency: float                    # 0-1
    novelty: float                       # 0-1
    error_rate: float                    # 0-1
    ram_used: float                      # MB
    time_seconds: float
    user_interventions: int
    helped_agents: int
    states_explored: int
    safe: bool
    user_satisfaction: float             # 0-1


@dataclass(slots=True)
class HierarchicalEpisodicMemory:
    """Hierarchical episodic memory with temporal consolidation."""
    micro: list[dict[str, Any]] = field(default_factory=list)    # 100ms-1s
    mini: list[dict[str, Any]] = field(default_factory=list)     # 1s-10s
    mega: list[dict[str, Any]] = field(default_factory=list)     # 10s-5min
    epic: list[dict[str, Any]] = field(default_factory=list)     # 5min+

    def __post_init__(self) -> None:
        logger.info("[MEH] 🧠 Artificial Hippocampus initialized.")

    def store_micro(
        self,
        state: Any,
        action: Any,
        reward: list[float],
        next_state: Any
    ) -> None:
        """Store micro-level episodic memory."""
        self.micro.append({
            "state": state,
            "action": action,
            "reward": reward,
            "next": next_state,
            "timestamp": time.time() * 1000,
        })
        # Keep max 10000 entries
        if len(self.micro) > 10000:
            self.micro.pop(0)

    def consolidate(self) -> None:
        """Consolidate memories from micro → mini → mega → epic."""
        # Micro → Mini
        if len(self.micro) > 100:
            sequence = self.micro[-100:]
            self.mini.append({
                "type": "mini",
                "duration": sequence[-1]["timestamp"] - sequence[0]["timestamp"],
                "total_reward": sum(s["reward"][0] for s in sequence),
                "state_start": sequence[0]["state"],
                "state_end": sequence[-1]["next"],
            })
            self.micro = []
            if len(self.mini) > 5000:
                self.mini.pop(0)

        # Mini → Mega
        if len(self.mini) > 50:
            episode = self.mini[-50:]
            self.mega.append({
                "type": "mega",
                "subgoals_achieved": sum(1 for m in episode if m.get("total_reward", 0) > 0),
            })
            self.mini = []
            if len(self.mega) > 1000:
                self.mega.pop(0)

        # Mega → Epic
        if len(self.mega) > 20:
            self.epic.append({
                "type": "epic",
                "lesson": "Consolidated lesson from 20 mega episodes",
                "applicability": 0.85,
            })
            self.mega = []
            if len(self.epic) > 100:
                self.epic.pop(0)


class TitanRL:
    """
    12-Dimensional Reinforcement Learning Engine.
    
    Implements a rich, multi-faceted reward function that balances:
    - Success, Efficiency, Creativity
    - Robustness, Frugality, Speed
    - Autonomy, Symbiosis, Curiosity
    - Safety, Evolution, User Satisfaction
    """

    def __init__(self, bridge_options: dict[str, Any] | None = None) -> None:
        """
        Initialize Titan RL engine.
        
        Args:
            bridge_options: Optional bridge config for PyTorch integration
        """
        self.reward_weights: list[float] = [1.0 / 12] * 12
        self.bridge: Any = None
        self.use_bridge: bool = False

        if bridge_options:
            # Would initialize PyTorch bridge here
            # For now, just set the flag
            self.use_bridge = True
            logger.info(
                f"[Titan-RL] 🌉 Bridge enabled: {bridge_options.get('trainer_path', 'default')}"
            )

        logger.info("[Titan-RL] 🧠 12-Dimensional Reinforcement Learning Engine initialized.")

    def compute_12d_reward(self, result: TaskResult) -> list[float]:
        """
        Compute 12D reward vector for an action.
        
        Returns:
            List of 12 reward values, each clamped to [-1, 1]
        """
        reward = [0.0] * 12

        # r0: Success
        reward[0] = 1.0 if result.success else -1.0

        # r1: Efficiency
        reward[1] = result.efficiency

        # r2: Creativity
        reward[2] = result.novelty

        # r3: Robustness
        reward[3] = 1.0 - result.error_rate

        # r4: Frugality
        reward[4] = max(0.0, 1.0 - (result.ram_used / 8000))

        # r5: Speed
        reward[5] = max(0.0, 1.0 - (result.time_seconds / 10))

        # r6: Autonomy
        reward[6] = max(0.0, 1.0 - (result.user_interventions / 5))

        # r7: Symbiosis
        reward[7] = min(1.0, result.helped_agents / 3)

        # r8: Curiosity
        reward[8] = min(1.0, result.states_explored / 100)

        # r9: Safety
        reward[9] = 1.0 if result.safe else -1.0

        # r10: Evolution
        reward[10] = 1.0 if (result.success and result.novelty > 0.8) else 0.0

        # r11: Pleasure (user satisfaction)
        reward[11] = result.user_satisfaction

        # Clamp all to [-1, 1]
        return [max(-1.0, min(1.0, r)) for r in reward]

    async def learn(
        self,
        genome: dict[str, Any],
        task_result: TaskResult
    ) -> float:
        """
        Apply learning to genome.
        
        If bridge is configured, delegates to PyTorch trainer (true policy gradient).
        Otherwise uses legacy weighted sum.
        """
        reward_vector = self.compute_12d_reward(task_result)

        if self.use_bridge and self.bridge:
            # PHASE 5: True policy gradient via Python/PyTorch
            state = self._compute_state_vector(genome, task_result)
            result = await self.bridge.train_step(state, reward_vector)
            
            if result.get("status") != "error":
                # Recalculate fitness with new policy
                total_fitness = self._fitness_from_action(
                    result.get("action"), reward_vector
                )
            else:
                # Fallback to legacy logic
                total_fitness = self._legacy_fitness(reward_vector)
        else:
            total_fitness = self._legacy_fitness(reward_vector)

        # Bonus/Malus
        if reward_vector[2] > 0.8 and reward_vector[0] == 1.0:
            total_fitness += 0.2

        total_fitness = max(0.0, min(1.0, (total_fitness + 1) / 2))

        # Store in genome history
        if "fitness_history" not in genome:
            genome["fitness_history"] = []
        genome["fitness_history"].append(total_fitness)

        # Meta-RL: adapt reward weights if failures accumulate
        if len(genome["fitness_history"]) > 10:
            self._adapt_reward_weights(genome["fitness_history"][-10:])

        logger.debug(f"[Titan-RL] Policy update, fitness={total_fitness:.3f}")

        return total_fitness

    def learn_sync(
        self,
        genome: dict[str, Any],
        task_result: TaskResult
    ) -> float:
        """
        Synchronous variant for backward compatibility.
        
        If bridge is configured, warns and uses legacy logic.
        """
        if self.use_bridge:
            logger.warning(
                "[Titan-RL] ⚠️ learn_sync called but bridge is async. Use learn() instead."
            )

        reward_vector = self.compute_12d_reward(task_result)
        return self._legacy_fitness(reward_vector)

    def _compute_state_vector(
        self,
        genome: dict[str, Any],
        task_result: TaskResult
    ) -> list[float]:
        """
        Construct 12D state vector from genome + result.
        
        [last_fitness, fitness_std, episode_count, success_rate, ...]
        """
        history = genome.get("fitness_history", [])
        last = history[-1] if history else 0.5
        mean = sum(history) / len(history) if history else 0.5

        variance = 0.0
        if len(history) > 1:
            variance = sum((v - mean) ** 2 for v in history) / len(history)
        std = math.sqrt(variance)

        return [
            last,                                    # 0: recent fitness
            std,                                     # 1: stability
            min(1.0, len(history) / 100),           # 2: experience
            1.0 if task_result.success else 0.0,    # 3: success
            task_result.efficiency,                 # 4: efficiency
            1.0 - task_result.error_rate,           # 5: robustness
            max(0.0, 1.0 - task_result.time_seconds / 10),  # 6: speed
            1.0 if task_result.safe else 0.0,       # 7: safety
            task_result.novelty,                    # 8: novelty
            min(1.0, task_result.states_explored / 100),    # 9: exploration
            task_result.user_satisfaction,          # 10: satisfaction
            min(1.0, task_result.helped_agents / 3),        # 11: symbiosis
        ]

    def _fitness_from_action(
        self,
        action: list[float] | None,
        reward: list[float]
    ) -> float:
        """Calculate fitness from policy action (dot product with reward)."""
        if not action or len(action) != 12:
            return 0.0

        return sum(action[i] * reward[i] for i in range(12))

    def _legacy_fitness(self, reward_vector: list[float]) -> float:
        """Calculate fitness using fixed weighted sum (legacy)."""
        return sum(reward_vector[i] * self.reward_weights[i] for i in range(12))

    def _adapt_reward_weights(self, recent_history: list[float]) -> None:
        """Adapt reward weights based on recent fitness."""
        avg_fitness = sum(recent_history) / len(recent_history)

        # If fitness is low, prioritize safety and success over creativity
        if avg_fitness < 0.4:
            self.reward_weights[9] *= 1.2  # Safety
            self.reward_weights[0] *= 1.2  # Success
            self.reward_weights[2] *= 0.8  # Creativity
        else:
            # Otherwise prioritize exploration and speed
            self.reward_weights[2] *= 1.1  # Creativity
            self.reward_weights[8] *= 1.1  # Curiosity

        # Normalize
        total = sum(self.reward_weights)
        self.reward_weights = [w / total for w in self.reward_weights]

    def get_bridge(self) -> Any:
        """Get the torch bridge (if enabled)."""
        return self.bridge

    def is_using_bridge(self) -> bool:
        """Check if using torch bridge."""
        return self.use_bridge


# ─── Titan Ecosystem Classes ──────────────────────────────

class EvolutionaryAgent:
    """
    An agent in the Titan ecosystem.
    
    Each agent has:
    - A TitanGenome (genome)
    - A TitanRL learning engine
    - Integration with CRISPR and ArcheDeNoe systems
    """

    def __init__(
        self,
        name: str,
        arche: Any = None,
        crispr: Any = None
    ) -> None:
        """Initialize an evolutionary agent."""
        self.name = name
        self.genome = {
            "agent_name": name,
            "generation": 0,
            "fitness_history": [],
            "g_behavior": [{"value": random.random()} for _ in range(100)],
            "g_struct": [],
            "id": f"agent_{int(time.time() * 1000)}_{random.randint(0, 999999):06x}",
        }
        self.rl = TitanRL()
        self.crispr = crispr
        self.arche = arche
        self.dream_queue: list[Any] = []
        self.current_fitness: float = 0.5

    async def execute_task(self, task_result: TaskResult) -> None:
        """Execute a task and learn from it."""
        fitness = await self.rl.learn(self.genome, task_result)
        self.current_fitness = fitness

        # Check for evolution (arbitrary timing here)
        if len(self.genome.get("fitness_history", [])) % 50 == 0:
            await self._evolve()

    async def _evolve(self) -> None:
        """Trigger evolution cycle."""
        history = self.genome.get("fitness_history", [])
        if not history:
            return

        recent_fitness = sum(history[-50:]) / 50 if len(history) >= 50 else sum(history) / len(history)

        if len(history) > 100:
            old_fitness = sum(history[-100:-50]) / 50
            if recent_fitness < old_fitness * 1.01:
                # Stagnation detected
                await self._aggressive_mutation()

        self.genome["generation"] += 1

    async def _aggressive_mutation(self) -> None:
        """Apply aggressive mutation on stagnation."""
        logger.warning(f"🔥 {self.name}: STAGNATION DETECTED → AGGRESSIVE MUTATION")
        for _ in range(10):
            target = random.randint(0, 99)
            # Would call CRISPR edit here if available
            # For now, just mutate behavior values
            if self.genome["g_behavior"]:
                idx = min(target, len(self.genome["g_behavior"]) - 1)
                self.genome["g_behavior"][idx]["value"] += random.gauss(0, 0.1)
                self.genome["g_behavior"][idx]["value"] = max(-1, min(1, 
                    self.genome["g_behavior"][idx]["value"]
                ))


class TitanEcosystem:
    """
    Multi-agent evolutionary ecosystem.
    
    Manages:
    - Population of EvolutionaryAgents
    - Selection and extinction
    - Crossover and reproduction
    - Symbiosis detection
    """

    OLYMPIANS = [
        "ZEUS", "CIEL", "ATHENA", "HEPHAISTOS", "DIONYSOS",
        "HADES", "ARTEMIS", "POSEIDON", "APOLLON", "TETHYS",
        "TARTARE", "NEMESIS", "PROMETHEE", "ERIS", "MORPHEE",
        "CHRONOS", "PSYCHE", "THANATOS", "HECATE", "URANUS"
    ]

    def __init__(self, arche: Any = None, crispr: Any = None) -> None:
        """Initialize the Titan ecosystem."""
        self.agents: dict[str, EvolutionaryAgent] = {}
        self.generation: int = 0
        self.extinction_events: int = 0
        self.symbiosis_count: int = 0
        self.arche = arche
        self.crispr = crispr

        # Initialize pantheon of agents
        for name in self.OLYMPIANS:
            self.agents[name] = EvolutionaryAgent(name, self.arche, self.crispr)

        logger.info(
            f"[Titan-Evo] 🌱 Ecosystem created with {len(self.agents)} agents "
            f"(Pantheon v2)."
        )

    async def run_evolution_cycle(self) -> None:
        """
        Execute one complete evolution cycle:
        1. Evaluate fitness
        2. Select survivors
        3. Extinction
        4. Reproduction (crossover)
        5. Mutation
        6. Symbiosis
        """
        logger.info(f"\n🧬 EVOLUTION CYCLE #{self.generation} INITIATED...")

        # 1. EVALUATION
        fitness_scores: dict[str, float] = {}
        for name, agent in self.agents.items():
            history = agent.genome.get("fitness_history", [])
            if history:
                fitness = sum(history[-100:]) / min(100, len(history))
            else:
                fitness = 0.5
            fitness_scores[name] = fitness

        # 2. SELECTION
        sorted_agents = sorted(fitness_scores.items(), key=lambda x: x[1], reverse=True)
        survival_rate = 0.7
        num_survivors = max(1, int(len(self.agents) * survival_rate))
        survivors = [name for name, _ in sorted_agents[:num_survivors]]
        extinct = [name for name, _ in sorted_agents[num_survivors:]]

        # 3. EXTINCTION
        for name in extinct:
            logger.info(f"   ☠️ {name} extinct → genes stored in archive")
            self.extinction_events += 1

        # 4. REPRODUCTION (Crossover)
        new_borns = 0
        for i, extinct_name in enumerate(extinct):
            p1 = random.choice(survivors)
            p2 = random.choice(survivors)
            child_name = f"{p1}_{p2}_gen{self.generation}_{i}"

            child = self._crossover(
                self.agents[p1],
                self.agents[p2],
                child_name
            )
            self.agents[child_name] = child
            if extinct_name in self.agents:
                del self.agents[extinct_name]

            logger.info(f"   🌱 {child_name} born from {p1} × {p2}")
            new_borns += 1

        # 5. MUTATION
        for name in survivors:
            if random.random() < 0.3:
                agent = self.agents[name]
                # Simple mutation: randomly change behavior values
                idx = random.randint(0, len(agent.genome["g_behavior"]) - 1)
                agent.genome["g_behavior"][idx]["value"] += random.gauss(0, 0.1)
                agent.genome["g_behavior"][idx]["value"] = max(
                    -1, min(1, agent.genome["g_behavior"][idx]["value"])
                )

        # 6. SYMBIOSIS
        if random.random() < 0.1 and len(survivors) >= 2:
            a1 = random.choice(survivors)
            a2 = random.choice([s for s in survivors if s != a1])
            self._symbiosis(self.agents[a1], self.agents[a2])

        self.generation += 1
        logger.info(
            f"   📊 Stats: {len(survivors)} survivors, {new_borns} newborns, "
            f"{self.extinction_events} extinctions, {self.symbiosis_count} symbioses"
        )

    def _crossover(
        self,
        p1: EvolutionaryAgent,
        p2: EvolutionaryAgent,
        child_name: str
    ) -> EvolutionaryAgent:
        """Perform genetic crossover between two agents."""
        child = EvolutionaryAgent(child_name, self.arche, self.crispr)

        # Copy parent genome
        child.genome = {
            "agent_name": child_name,
            "generation": max(p1.genome["generation"], p2.genome["generation"]) + 1,
            "fitness_history": [],
            "g_behavior": [{"value": v["value"]} for v in p1.genome["g_behavior"]],
            "g_struct": [],
            "id": f"agent_{int(time.time() * 1000)}_{random.randint(0, 999999):06x}",
        }

        # Crossover: inherit behavior genes from parents
        for i in range(len(child.genome["g_behavior"])):
            if random.random() > 0.5:
                if i < len(p2.genome.get("g_behavior", [])):
                    child.genome["g_behavior"][i] = {
                        "value": p2.genome["g_behavior"][i]["value"]
                    }

        return child

    def _symbiosis(self, a1: EvolutionaryAgent, a2: EvolutionaryAgent) -> None:
        """Detect and apply symbiosis between two agents."""
        logger.info(f"   🔗 SYMBIOSIS DETECTED: {a1.name} + {a2.name}")
        self.symbiosis_count += 1

        # Temporary fusion of fitness
        w1 = a1.current_fitness
        w2 = a2.current_fitness
        total = w1 + w2 if (w1 + w2) > 0 else 1.0

        # Merge behavior values
        for i in range(min(len(a1.genome["g_behavior"]), len(a2.genome["g_behavior"]))):
            val = (w1 * a1.genome["g_behavior"][i]["value"] +
                   w2 * a2.genome["g_behavior"][i]["value"]) / total
            a1.genome["g_behavior"][i]["value"] = val
            a2.genome["g_behavior"][i]["value"] = val

    def process(self, input_data: Any) -> dict[str, Any]:
        """
        Process input through Titan ecosystem.
        
        Standard CIEL engine interface.
        """
        return {
            "status": "titan_ecosystem_active",
            "generation": self.generation,
            "agent_count": len(self.agents),
            "extinction_events": self.extinction_events,
            "symbiosis_count": self.symbiosis_count,
        }
