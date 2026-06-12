from __future__ import annotations

import pytest

from ciel.evolution.fitness_evaluator import FitnessEvaluator, FitnessResult


class TestHydraContext:
    def test_create(self):
        ctx = HydraContext(task_success=0.9, user_satisfaction=0.8, cost_ratio=0.2, latency_ratio=0.1)
        assert ctx.task_success == 0.9
        assert ctx.user_satisfaction == 0.8

    def test_defaults(self):
        ctx = HydraContext()
        assert ctx.task_success == 0.0
        assert ctx.evolutionary_pressure == 0.0


class TestFitnessEvaluator:
    def test_instantiate(self):
        e = FitnessEvaluator()
        assert e is not None

    def test_evaluate_with_context(self):
        e = FitnessEvaluator()
        ctx = HydraContext(task_success=1.0, user_satisfaction=1.0, cost_ratio=0.0, latency_ratio=0.0, evolutionary_pressure=1.0)
        fitness = e.evaluate(None, ctx)
        assert 0.0 <= fitness <= 1.0
        assert fitness > 0.9  # all max

    def test_evaluate_minimal(self):
        e = FitnessEvaluator()
        ctx = HydraContext(task_success=0.0, user_satisfaction=0.0, cost_ratio=1.0, latency_ratio=1.0)
        fitness = e.evaluate(None, ctx)
        assert fitness == 0.0

    def test_evaluate_without_context(self):
        e = FitnessEvaluator()
        class MockGenome:
            fitness_history = [0.5, 0.6, 0.7]
        g = MockGenome()
        fitness = e.evaluate(g)
        assert 0.0 <= fitness <= 1.0

    def test_evaluate_without_context_no_history(self):
        e = FitnessEvaluator()
        class MockGenome:
            pass
        g = MockGenome()
        fitness = e.evaluate(g)
        assert fitness == 0.5

    def test_get_weights(self):
        e = FitnessEvaluator()
        w = e.get_weights()
        assert w == FITNESS_WEIGHTS

    def test_process_with_data(self):
        e = FitnessEvaluator()
        r = e.process({"task_success": 0.9})
        assert "weights" in r
        assert r["evaluator_type"] == "FitnessEvaluator"

    def test_process_state(self):
        e = FitnessEvaluator()
        r = e.process({"action": "state"})
        assert "weights" in r

    def test_process_bad_input(self):
        e = FitnessEvaluator()
        r = e.process("bad")
        assert r == {"error": "No context provided"}

    def test_process_unknown_action(self):
        e = FitnessEvaluator()
        r = e.process({"action": "nonexistent"})
        assert "weights" in r
