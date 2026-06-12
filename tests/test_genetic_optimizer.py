from __future__ import annotations

import pytest

from ciel.evolution.genetic_optimizer import GeneticOptimizer


class TestSkill:
    def test_create(self):
        s = Skill(id="skill_1", power=0.9, is_sealed=False)
        assert s.id == "skill_1"
        assert s.power == 0.9


class TestPersonalityProfile:
    def test_create(self):
        p = PersonalityProfile(id="p1", velocity=0.8, precision=0.7, dominance=0.5, empathy=0.6, stealth=0.4)
        assert p.id == "p1"
        assert p.velocity == 0.8

    def test_defaults(self):
        p = PersonalityProfile()
        assert p.velocity == 0.5


class TestGeneticOptimizer:
    def test_instantiate(self):
        go = GeneticOptimizer()
        assert go is not None

    def test_initial_genomes(self):
        go = GeneticOptimizer()
        assert "zeus" in go._agent_genomes
        assert "athena" in go._agent_genomes
        assert "erebus" in go._agent_genomes

    def test_elect_patron(self):
        go = GeneticOptimizer()
        avg = PersonalityProfile(velocity=0.5, precision=0.9, dominance=0.3, empathy=0.4, stealth=0.5)
        elected = go.elect_patron(FactionType.SAGES, avg)
        assert elected in ("athena", "hermes", "zeus")

    def test_generate_heirs(self):
        go = GeneticOptimizer()
        heirs = go.generate_heirs("zeus", "athena")
        assert len(heirs) == 2
        for h in heirs:
            assert isinstance(h, PersonalityProfile)
            assert h.generation == 1

    def test_generate_heirs_unknown(self):
        go = GeneticOptimizer()
        heirs = go.generate_heirs("unknown", "athena")
        assert heirs == []

    def test_process_state(self):
        go = GeneticOptimizer()
        r = go.process({"action": "state"})
        assert r["optimizer"] == "GeneticOptimizer"
        assert "profiles" in r

    def test_process_bad_input(self):
        go = GeneticOptimizer()
        r = go.process("bad")
        assert r["optimizer"] == "GeneticOptimizer"

    def test_process_unknown_action(self):
        go = GeneticOptimizer()
        r = go.process({"action": "nonexistent"})
        assert r["optimizer"] == "GeneticOptimizer"

    def test_unified_to_personality(self):
        class MockGenome:
            id = "g1"
            generation = 5
            def get_phenotype(self):
                return {"exploration_rate": 0.7, "risk_tolerance": 0.3, "creativity_index": 0.6, "collaboration_drive": 0.4}
        p = unified_to_personality(MockGenome())
        assert p.id == "g1"
        assert p.velocity == 0.7
        assert p.precision == 0.7

    def test_absorb_into(self):
        go = GeneticOptimizer()
        import asyncio

        class MockGene:
            id = "s1"
            value = 0.5

        class MockGenome:
            id = "g"
            g_behavior = [MockGene()]
            def mutate(self, rate):
                pass

        survivor = MockGenome()
        victim = MockGenome()
        asyncio.run(go.absorb_into(survivor, victim))
        assert survivor is not None
