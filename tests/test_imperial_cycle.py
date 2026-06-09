from __future__ import annotations

import pytest

from ciel.evolution.imperial_cycle import ImperialCycle, ImperialCycleResult
from ciel.evolution.fitness_evaluator import DefaultFitnessEvaluator, HydraContext


class TestImperialCycleResult:
    def test_create(self):
        r = ImperialCycleResult(
            generation=0, survivors=[], dead=[], clusters={},
            best_fitness=0.0, median_fitness=0.0, super_organisms_added=0,
        )
        assert r.generation == 0


class TestImperialCycle:
    def test_instantiate(self):
        ic = ImperialCycle()
        assert ic is not None

    def test_get_population_empty(self):
        ic = ImperialCycle()
        assert ic.get_population() == []

    def test_get_current_generation(self):
        ic = ImperialCycle()
        assert ic.get_current_generation() == 0

    def test_get_elites_empty(self):
        ic = ImperialCycle()
        assert ic.get_elites() == []

    def test_set_context(self):
        ic = ImperialCycle()
        ctx = HydraContext(task_success=0.5)
        ic.set_context(ctx)
        assert ic._last_context is not None

    def test_on_and_emit(self):
        ic = ImperialCycle()
        calls = []
        ic.on("test_event", lambda d: calls.append(d))
        ic._emit("test_event", {"key": "val"})
        assert len(calls) == 1
        assert calls[0] == {"key": "val"}

    def test_pick_random(self):
        picks = ImperialCycle._pick_random([1, 2, 3, 4, 5], 3)
        assert len(picks) == 3

    def test_pick_random_more_than_available(self):
        picks = ImperialCycle._pick_random([1, 2], 5)
        assert len(picks) == 2

    def test_run_generation_with_genome_factory(self):
        class MockGenome:
            def __init__(self, name="test"):
                self.id = "g1"
                self.agent_name = name
                self.generation = 0
                self.fac = "mock"
                self.fitness_history = []
            def fitness_score(self):
                return 0.5
            def clone(self):
                return MockGenome(self.agent_name + "_clone")
            def mutate(self, rate):
                pass
            def crossover(self, other):
                c = MockGenome(f"{self.agent_name}_x_{other.agent_name}")
                c.generation = max(self.generation, other.generation) + 1
                return c

        ic = ImperialCycle(population_size=5, elite_size=2, genome_factory=lambda: MockGenome())
        import asyncio
        result = asyncio.run(ic.run_generation())
        assert result.generation == 1
        assert ic.get_current_generation() == 1

    def test_process_state(self):
        ic = ImperialCycle()
        r = ic.process({"action": "state"})
        assert "generation" in r
        assert "population_size" in r

    def test_process_bad_input(self):
        ic = ImperialCycle()
        r = ic.process("bad")
        assert "generation" in r

    def test_process_unknown_action(self):
        ic = ImperialCycle()
        r = ic.process({"action": "nonexistent"})
        assert "generation" in r
