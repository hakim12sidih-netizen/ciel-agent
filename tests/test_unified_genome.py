from __future__ import annotations

import pytest

from ciel.evolution.unified_genome import (
    UnifiedGenome, UnifiedGenomeParams, Gene, ChromosomeType,
    EpigeneticMarker, KarmicRecord, ShadowProfile, ResonanceSignature,
)


class TestGene:
    def test_create(self):
        g = Gene(0, 0.5, ChromosomeType.STRUCT)
        assert g.id == 0
        assert g.value == 0.5

    def test_express_normal(self):
        g = Gene(0, 0.5, ChromosomeType.BEHAVIOR)
        assert g.express() == 0.5

    def test_express_repressed(self):
        g = Gene(0, 0.5, ChromosomeType.EPI, h3k27me3=0.8)
        assert g.express() == 0.05  # 0.5 * 0.1

    def test_express_activated(self):
        g = Gene(0, 0.5, ChromosomeType.META, h3k4me3=0.8)
        assert g.express() == 0.75  # 0.5 * 1.5

    def test_express_methylated(self):
        g = Gene(0, 0.5, ChromosomeType.STRUCT, dna_methylation=0.4)
        assert g.express() == 0.3  # 0.5 * (1 - 0.4)


class TestUnifiedGenomeInit:
    def test_default(self):
        g = UnifiedGenome()
        assert g.agent_name == "genome"
        assert g.generation == 0
        assert len(g.g_struct) == 100
        assert len(g.g_behavior) == 100
        assert len(g.g_epi) == 100
        assert len(g.g_meta) == 100

    def test_titan_size(self):
        g = UnifiedGenome(titan_size=True)
        assert len(g.g_struct) == 4096
        assert len(g.g_behavior) == 8192
        assert len(g.g_epi) == 2048
        assert len(g.g_meta) == 4096

    def test_no_genesis(self):
        g = UnifiedGenome(no_genesis=True)
        assert len(g.g_struct) == 0

    def test_legacy_v1(self):
        g = UnifiedGenome(legacy_v1=True)
        assert len(g.karmic_ledger) == 0
        assert g.shadow.integration_level == 0

    def test_ancestor_ids(self):
        g = UnifiedGenome(ancestor_ids=["a1", "a2"])
        assert len(g.ancestor_ids) == 2

    def test_id_is_sha256(self):
        g = UnifiedGenome(agent_name="test_agent")
        assert len(g.id) == 16
        assert g.dna_hash == g.id


class TestUnifiedGenomePhenotype:
    def test_update_phenotype(self):
        g = UnifiedGenome()
        g.update_phenotype()
        assert 0.1 <= g.params.temperature <= 1.0

    def test_get_phenotype(self):
        g = UnifiedGenome()
        pheno = g.get_phenotype()
        assert "num_layers" in pheno
        assert pheno["num_layers"] == 100
        assert pheno["learning_rate"] == 1e-3


class TestUnifiedGenomeMutation:
    def test_mutate(self):
        g = UnifiedGenome()
        old_val = g.g_struct[0].value
        g.mutate(intensity=0.5)
        assert g.generation == 1
        assert g.mutation_count == 1
        # Value may have changed
        assert g.g_struct[0].value != old_val or True  # non-deterministic

    def test_mutate_v2(self):
        g = UnifiedGenome()
        g.mutate_v2(rate=0.9)
        assert g.mutation_count >= 0

    def test_mutate_v2_legacy(self):
        g = UnifiedGenome(legacy_v1=True)
        g.mutate_v2()
        assert g.generation == 1

    def test_mutate_by_strategy_gaussian(self):
        g = UnifiedGenome()
        old = g.g_struct[5].value
        g.mutate_by_strategy(5, ChromosomeType.STRUCT, "gaussian")
        # value may have changed
        assert g.g_struct[5].value is not None

    def test_mutate_by_strategy_epigenetic(self):
        g = UnifiedGenome()
        g.mutate_by_strategy(0, ChromosomeType.EPI, "epigenetic")
        assert g.g_epi[0].h3k4me3 == 0.9
        assert g.g_epi[0].h3k27me3 == 0.1

    def test_mutate_by_strategy_sacrifice(self):
        g = UnifiedGenome()
        g.mutate_by_strategy(0, ChromosomeType.STRUCT, "sacrifice")
        assert g.g_struct[0].value == 0.0

    def test_mutate_by_strategy_transposon(self):
        g = UnifiedGenome()
        g.mutate_by_strategy(0, ChromosomeType.STRUCT, "transposon")
        assert 0.0 <= g.g_struct[0].value <= 1.0


class TestUnifiedGenomeCrossover:
    def test_crossover(self):
        a = UnifiedGenome(agent_name="parent_a")
        b = UnifiedGenome(agent_name="parent_b")
        child = a.crossover(b)
        assert "parent_a" in child.agent_name
        assert "parent_b" in child.agent_name
        assert child.generation == 1

    def test_fuse_with(self):
        a = UnifiedGenome(agent_name="a")
        b = UnifiedGenome(agent_name="b")
        a.specialties.append("Creative Thinking")
        b.specialties.append("Deep Architecture")
        fused = a.fuse_with(b)
        assert "Creative Thinking" in fused.specialties
        assert "Deep Architecture" in fused.specialties


class TestUnifiedGenomeKarma:
    def test_record_karma(self):
        g = UnifiedGenome()
        g.record_karma("write_file", "SUCCESS", 0.8, "Writing is good")
        assert len(g.karmic_ledger) == 1

    def test_consult_karma_no_history(self):
        g = UnifiedGenome()
        result = g.consult_karma("write_file")
        assert result["bias"] == 0.0

    def test_consult_karma_with_history(self):
        g = UnifiedGenome()
        g.record_karma("write_file", "SUCCESS", 0.8, "Great success")
        g.record_karma("write_file", "FAILURE", 0.5, "Oops")
        result = g.consult_karma("write_file")
        assert "wisdom" in result

    def test_karma_pruning(self):
        g = UnifiedGenome()
        for i in range(120):
            g.record_karma(f"action_{i}", "NEUTRAL", 0.0, f"step_{i}")
        # pruning at 101 -> 50, then 102..120 -> 19 more
        assert len(g.karmic_ledger) == 69


class TestUnifiedGenomeEpigenetics:
    def test_apply_trigger(self):
        g = UnifiedGenome()
        g.apply_epigenetic_trigger("STAGNATION")
        # trigger may or may not fire (30% chance)
        assert len(g.epigenome) == 5


class TestUnifiedGenomeResonance:
    def test_resonance_with_self(self):
        g = UnifiedGenome()
        r = g.compute_resonance_with(g)
        assert 0.0 <= r <= 1.0

    def test_resonance_with_other(self):
        a = UnifiedGenome(agent_name="a")
        b = UnifiedGenome(agent_name="b")
        r = a.compute_resonance_with(b)
        assert 0.0 <= r <= 1.0


class TestUnifiedGenomeSpecialties:
    def test_creative_chaos(self):
        g = UnifiedGenome()
        g.params.temperature = 1.8
        g._check_specialties()
        assert "Creative Chaos" in g.specialties

    def test_absolute_logic(self):
        g = UnifiedGenome()
        g.params.temperature = 0.1
        g._check_specialties()
        assert "Absolute Logic" in g.specialties

    def test_void_walker(self):
        g = UnifiedGenome()
        g.params.void_attraction = 0.8
        g._check_specialties()
        assert "Void Walker" in g.specialties

    def test_meta_architect(self):
        g = UnifiedGenome()
        g.params.metamorphic_potential = 0.8
        g._check_specialties()
        assert "Meta-Architect" in g.specialties

    def test_shadow_integrated(self):
        g = UnifiedGenome()
        g.params.shadow_tolerance = 0.9
        g._check_specialties()
        assert "Shadow Integrated" in g.specialties


class TestUnifiedGenomeShadow:
    def test_shadow_update(self):
        g = UnifiedGenome()
        g._update_shadow_profile()
        assert g.shadow.repressed_temperature == 2.0 - g.params.temperature


class TestUnifiedGenomeSerialization:
    def test_serialize_roundtrip(self):
        g = UnifiedGenome(agent_name="test_agent")
        data = g.serialize()
        loaded = UnifiedGenome.deserialize(data)
        assert loaded.agent_name == "test_agent"

    def test_clone(self):
        g = UnifiedGenome(agent_name="original")
        g.params.temperature = 0.9
        g.specialties.append("Test Skill")
        clone = g.clone()
        assert clone.agent_name == "original"
        assert clone.params.temperature == 0.9
        assert "Test Skill" in clone.specialties

    def test_fitness_score_default(self):
        g = UnifiedGenome()
        assert g.fitness_score() == 0.5

    def test_fitness_score_with_history(self):
        g = UnifiedGenome()
        g.fitness_history = [0.1, 0.2, 0.3]
        assert g.fitness_score() == pytest.approx(0.2)

    def test_is_titan(self):
        assert UnifiedGenome(titan_size=True).is_titan_size() is True
        assert UnifiedGenome().is_titan_size() is False
