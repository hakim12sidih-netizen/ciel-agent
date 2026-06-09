from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable

from ciel.evolution.fitness_evaluator import DefaultFitnessEvaluator, HydraContext


@dataclass(slots=True)
class ImperialCycleResult:
    generation: int
    survivors: list[Any]
    dead: list[Any]
    clusters: dict[str, list[Any]]
    best_fitness: float
    median_fitness: float
    super_organisms_added: int


class ImperialCycle:
    def __init__(
        self,
        genetic_optimizer: Any | None = None,
        evaluator: DefaultFitnessEvaluator | None = None,
        population_size: int = 100,
        elite_size: int = 10,
        genome_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._genetic = genetic_optimizer
        self._evaluator = evaluator or DefaultFitnessEvaluator()
        self._population_size = population_size
        self._elite_size = elite_size
        self._genome_factory = genome_factory
        self.population: list[Any] = []
        self._generation = 0
        self._elites: list[Any] = []
        self._last_context: HydraContext | None = None
        self._super_organisms_added = 0
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable) -> None:
        self._listeners.setdefault(event, []).append(callback)

    def _emit(self, event: str, data: Any) -> None:
        for cb in self._listeners.get(event, []):
            cb(data)

    def get_population(self) -> list[Any]:
        return list(self.population)

    def set_context(self, context: HydraContext) -> None:
        self._last_context = context

    async def run_generation(self, context: HydraContext | None = None) -> ImperialCycleResult:
        self._generation += 1
        if context is not None:
            self._last_context = context
        self._super_organisms_added = 0
        self._spawn_population(self._population_size)
        survivors = self._evaluate_and_select(self._elite_size)
        dead = [g for g in self.population if g not in survivors]

        best_fit = survivors[0].fitness_score() if survivors else 0.0
        median_fit = self._compute_median_fitness()

        if self._genetic is not None:
            for survivor in survivors:
                victims = self._pick_random(dead, 7)
                for victim in victims:
                    if hasattr(self._genetic, "absorb_into"):
                        await self._genetic.absorb_into(survivor, victim)

        clusters = self._detect_emergent_factions(survivors)
        for members in clusters.values():
            if len(members) >= 2 and self._genetic is not None:
                if hasattr(self._genetic, "generate_heirs_from"):
                    self._genetic.generate_heirs_from(members[0], members[1])

        self._elites = survivors
        new_population = list(survivors)
        slots = self._population_size - len(survivors)
        for i in range(slots):
            p1 = self._pick_random(survivors, 1)[0]
            p2 = self._pick_random(survivors, 1)[0]
            if hasattr(p1, "crossover"):
                child = p1.crossover(p2)
                child.agent_name = f"agent_g{self._generation}_offspring_{i}"
                if hasattr(child, "mutate"):
                    child.mutate(0.15)
                new_population.append(child)
        self.population = new_population

        result = ImperialCycleResult(
            generation=self._generation,
            survivors=survivors,
            dead=dead,
            clusters=clusters,
            best_fitness=best_fit,
            median_fitness=median_fit,
            super_organisms_added=self._super_organisms_added,
        )
        self._emit("generation.complete", result)
        return result

    def _spawn_population(self, count: int) -> None:
        new_genomes: list[Any] = []
        for i in range(count):
            if self._elites and self._genome_factory is None:
                parent = random.choice(self._elites)
                if hasattr(parent, "clone"):
                    child = parent.clone()
                    child.agent_name = f"agent_g{self._generation}_{i}"
                    if hasattr(child, "mutate"):
                        child.mutate(0.1)
                    new_genomes.append(child)
            elif self._genome_factory is not None:
                g = self._genome_factory()
                new_genomes.append(g)
        self.population = new_genomes

    def _evaluate_and_select(self, count: int) -> list[Any]:
        scored = [(g, self._evaluator.evaluate(g, self._last_context)) for g in self.population]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored[:count]]

    def _compute_median_fitness(self) -> float:
        if not self.population:
            return 0.0
        fits = sorted(g.fitness_score() for g in self.population)
        mid = len(fits) // 2
        return fits[mid]

    def _detect_emergent_factions(self, survivors: list[Any]) -> dict[str, list[Any]]:
        clusters: dict[str, list[Any]] = {}
        for g in survivors:
            specialties = getattr(g, "specialties", [])
            key = specialties[0] if specialties else "Alpha"
            clusters.setdefault(key, []).append(g)
        return clusters

    @staticmethod
    def _pick_random(array: list[Any], n: int) -> list[Any]:
        copy = list(array)
        result: list[Any] = []
        for _ in range(min(n, len(copy))):
            idx = random.randrange(len(copy))
            result.append(copy.pop(idx))
        return result

    def get_elites(self) -> list[Any]:
        return list(self._elites)

    def get_current_generation(self) -> int:
        return self._generation

    def process(self, input_data: Any) -> dict[str, Any]:
        return {
            "generation": self._generation,
            "population_size": len(self.population),
            "elite_size": len(self._elites),
        }
