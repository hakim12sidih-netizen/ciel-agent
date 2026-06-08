from __future__ import annotations

import pytest
from ciel.skills.core import (
    SkillLevel, SkillPhase, Skill, SkillRegistry,
    SkillExecutor, SkillGenerator, SkillOptimizer, ForgeronEngine,
)


class TestSkillLevel:
    def test_values(self):
        assert SkillLevel.REFLEXE.value == 0
        assert SkillLevel.TRANSCENDANT.value == 7
        assert len(SkillLevel) == 8

    def test_descriptions(self):
        assert "précompilé" in SkillLevel.REFLEXE.description
        assert "crée" in SkillLevel.GENERATIF.description
        assert "native" in SkillLevel.TRANSCENDANT.description

    def test_response_time(self):
        assert SkillLevel.REFLEXE.response_time_ms < 1.0
        assert SkillLevel.GENERATIF.response_time_ms > SkillLevel.REFLEXE.response_time_ms


class TestSkillPhase:
    def test_values(self):
        assert len(SkillPhase) == 12
        assert SkillPhase.GERMINATION.value == "germination"
        assert SkillPhase.TRANSCENDANCE.value == "transcendance"

    def test_ordinal(self):
        assert SkillPhase.GERMINATION.ordinal == 0
        assert SkillPhase.TRANSCENDANCE.ordinal == 11


class TestSkill:
    def test_create(self):
        s = Skill.create("test_skill", SkillLevel.ADAPTATIF)
        assert s.name == "test_skill"
        assert s.level == SkillLevel.ADAPTATIF
        assert s.phase == SkillPhase.GERMINATION
        assert s.id is not None

    def test_create_with_description(self):
        s = Skill.create("foo", SkillLevel.REFLEXE, description="bar")
        assert s.description == "bar"

    def test_create_default_description(self):
        s = Skill.create("foo", SkillLevel.GENERATIF)
        assert "foo" in s.description

    def test_advance_phase(self):
        s = Skill.create("x", SkillLevel.REFLEXE)
        assert s.phase == SkillPhase.GERMINATION
        s.advance_phase()
        assert s.phase == SkillPhase.INCUBATION

    def test_advance_phase_full_cycle(self):
        s = Skill.create("x", SkillLevel.REFLEXE)
        phases = list(SkillPhase)
        for i in range(len(phases) - 1):
            assert s.advance_phase() is not None
        assert s.phase == SkillPhase.TRANSCENDANCE
        assert s.advance_phase() is None

    def test_execute(self):
        s = Skill.create("scan", SkillLevel.REACTIF)
        result = s.execute({"target": "file"})
        assert result["skill_name"] == "scan"
        assert result["level"] == 1
        assert "target" in result["context_keys"]
        assert result["usage_count"] == 1

    def test_execute_increments_usage(self):
        s = Skill.create("x", SkillLevel.REFLEXE)
        s.execute()
        s.execute()
        assert s.usage_count == 2

    def test_train_success(self):
        s = Skill.create("x", SkillLevel.ADAPTATIF)
        s.train(True)
        assert s.accuracy > 0

    def test_train_failure(self):
        s = Skill.create("x", SkillLevel.ADAPTATIF, description="test")
        s.accuracy = 0.5
        s.train(False)
        assert s.accuracy < 0.5

    def test_train_advances_phase(self):
        s = Skill.create("x", SkillLevel.REFLEXE)
        for _ in range(20):
            s.train(True)
        assert s.phase != SkillPhase.GERMINATION

    def test_similar_to_same_level(self):
        a = Skill.create("a", SkillLevel.REACTIF)
        b = Skill.create("b", SkillLevel.REACTIF)
        b.dependencies = ["dep1"]
        a.dependencies = ["dep1"]
        assert a.similar_to(b) > 0

    def test_similar_to_different_level(self):
        a = Skill.create("a", SkillLevel.REFLEXE)
        b = Skill.create("b", SkillLevel.REACTIF)
        assert a.similar_to(b) == 0.0

    def test_latency_default(self):
        s = Skill.create("x", SkillLevel.REFLEXE)
        assert s.latency_ms == SkillLevel.REFLEXE.response_time_ms


class TestSkillRegistry:
    def test_register_and_get(self):
        reg = SkillRegistry()
        s = Skill.create("scan", SkillLevel.REFLEXE)
        reg.register(s)
        assert reg.get(s.id) is s

    def test_get_by_name(self):
        reg = SkillRegistry()
        s = Skill.create("ping", SkillLevel.REFLEXE)
        reg.register(s)
        assert reg.get_by_name("ping") is s

    def test_get_by_name_missing(self):
        reg = SkillRegistry()
        assert reg.get_by_name("nonexistent") is None

    def test_unregister(self):
        reg = SkillRegistry()
        s = Skill.create("x", SkillLevel.REFLEXE)
        reg.register(s)
        assert reg.unregister(s.id) is True
        assert reg.get(s.id) is None

    def test_unregister_missing(self):
        reg = SkillRegistry()
        assert reg.unregister("nonexistent") is False

    def test_list_by_level(self):
        reg = SkillRegistry()
        r1 = Skill.create("r1", SkillLevel.REFLEXE)
        r2 = Skill.create("r2", SkillLevel.REFLEXE)
        a1 = Skill.create("a1", SkillLevel.ADAPTATIF)
        reg.register(r1)
        reg.register(r2)
        reg.register(a1)
        assert len(reg.list_by_level(SkillLevel.REFLEXE)) == 2
        assert len(reg.list_by_level(SkillLevel.ADAPTATIF)) == 1

    def test_list_by_phase(self):
        reg = SkillRegistry()
        s = Skill.create("x", SkillLevel.REFLEXE)
        reg.register(s)
        assert len(reg.list_by_phase(SkillPhase.GERMINATION)) == 1

    def test_list_by_category(self):
        reg = SkillRegistry()
        s = Skill.create("vision", SkillLevel.REFLEXE)
        reg.register(s, category="perception")
        assert len(reg.list_by_category("perception")) == 1
        assert len(reg.list_by_category("nonexistent")) == 0

    def test_all(self):
        reg = SkillRegistry()
        reg.register(Skill.create("a", SkillLevel.REFLEXE))
        reg.register(Skill.create("b", SkillLevel.REACTIF))
        assert len(reg.all()) == 2

    def test_count(self):
        reg = SkillRegistry()
        assert reg.count() == 0
        reg.register(Skill.create("x", SkillLevel.REFLEXE))
        assert reg.count() == 1

    def test_categories(self):
        reg = SkillRegistry()
        reg.register(Skill.create("x", SkillLevel.REFLEXE), category="a")
        reg.register(Skill.create("y", SkillLevel.REACTIF), category="b")
        assert set(reg.categories()) == {"a", "b"}

    def test_clear(self):
        reg = SkillRegistry()
        reg.register(Skill.create("x", SkillLevel.REFLEXE))
        reg.clear()
        assert reg.count() == 0


class TestSkillExecutor:
    def test_execute(self):
        reg = SkillRegistry()
        s = Skill.create("scan", SkillLevel.REACTIF)
        reg.register(s)
        exec_ = SkillExecutor(reg)
        result = exec_.execute(s.id)
        assert result is not None
        assert result["skill_name"] == "scan"

    def test_execute_missing(self):
        exec_ = SkillExecutor(SkillRegistry())
        assert exec_.execute("nonexistent") is None

    def test_execute_by_name(self):
        reg = SkillRegistry()
        s = Skill.create("ping", SkillLevel.REFLEXE)
        reg.register(s)
        exec_ = SkillExecutor(reg)
        result = exec_.execute_by_name("ping")
        assert result is not None

    def test_execute_by_name_missing(self):
        exec_ = SkillExecutor(SkillRegistry())
        assert exec_.execute_by_name("nope") is None

    def test_execute_all(self):
        reg = SkillRegistry()
        reg.register(Skill.create("a", SkillLevel.REFLEXE))
        reg.register(Skill.create("b", SkillLevel.REACTIF))
        exec_ = SkillExecutor(reg)
        results = exec_.execute_all()
        assert len(results) == 2

    def test_execute_all_by_level(self):
        reg = SkillRegistry()
        reg.register(Skill.create("a", SkillLevel.REFLEXE))
        reg.register(Skill.create("b", SkillLevel.ADAPTATIF))
        exec_ = SkillExecutor(reg)
        results = exec_.execute_all(level=SkillLevel.REFLEXE)
        assert len(results) == 1

    def test_history(self):
        reg = SkillRegistry()
        s = Skill.create("x", SkillLevel.REFLEXE)
        reg.register(s)
        exec_ = SkillExecutor(reg)
        exec_.execute(s.id)
        exec_.execute(s.id)
        assert len(exec_.history()) == 2

    def test_clear_history(self):
        reg = SkillRegistry()
        s = Skill.create("x", SkillLevel.REFLEXE)
        reg.register(s)
        exec_ = SkillExecutor(reg)
        exec_.execute(s.id)
        exec_.clear_history()
        assert len(exec_.history()) == 0

    def test_pre_hook(self):
        reg = SkillRegistry()
        s = Skill.create("x", SkillLevel.REFLEXE)
        reg.register(s)
        exec_ = SkillExecutor(reg)
        results = []

        def hook(skill: Skill, ctx: dict) -> dict:
            results.append(skill.name)
            return ctx

        exec_.add_pre_hook(hook)
        exec_.execute(s.id)
        assert "x" in results

    def test_post_hook(self):
        reg = SkillRegistry()
        s = Skill.create("x", SkillLevel.REFLEXE)
        reg.register(s)
        exec_ = SkillExecutor(reg)
        results = []

        def hook(skill: Skill, result: dict) -> None:
            results.append(result["skill_name"])

        exec_.add_post_hook(hook)
        exec_.execute(s.id)
        assert "x" in results


class TestSkillGenerator:
    def test_generate(self):
        reg = SkillRegistry()
        gen = SkillGenerator(reg)
        s = gen.generate("new_skill", "test")
        assert s.name == "new_skill"
        assert s.level == SkillLevel.GENERATIF
        assert s.accuracy > 0

    def test_generate_with_parents(self):
        reg = SkillRegistry()
        parent = Skill.create("parent", SkillLevel.REFLEXE)
        reg.register(parent)
        gen = SkillGenerator(reg)
        child = gen.generate("child", "desc", SkillLevel.ADAPTATIF, parent_ids=[parent.id])
        assert parent.id in child.dependencies

    def test_generate_from_existing(self):
        reg = SkillRegistry()
        template = Skill.create("template", SkillLevel.PREDICTIF)
        reg.register(template)
        gen = SkillGenerator(reg)
        child = gen.generate_from_existing(template.id, "child")
        assert child is not None
        assert child.name == "child"
        assert child.level == template.level

    def test_generate_from_existing_missing(self):
        gen = SkillGenerator(SkillRegistry())
        assert gen.generate_from_existing("nonexistent", "x") is None

    def test_total_generated(self):
        reg = SkillRegistry()
        gen = SkillGenerator(reg)
        assert gen.total_generated() == 0
        gen.generate("a")
        gen.generate("b")
        assert gen.total_generated() == 2


class TestSkillOptimizer:
    def test_optimize(self):
        reg = SkillRegistry()
        s = Skill.create("x", SkillLevel.META_META)
        reg.register(s)
        opt = SkillOptimizer(reg)
        assert opt.optimize(s.id) is True
        assert s.metadata.get("optimized") is True

    def test_optimize_low_level(self):
        reg = SkillRegistry()
        s = Skill.create("x", SkillLevel.REFLEXE)
        reg.register(s)
        opt = SkillOptimizer(reg)
        assert opt.optimize(s.id) is False

    def test_optimize_missing(self):
        opt = SkillOptimizer(SkillRegistry())
        assert opt.optimize("nonexistent") is False

    def test_prune(self):
        reg = SkillRegistry()
        s1 = Skill.create("used", SkillLevel.REFLEXE)
        s1.usage_count = 10
        s2 = Skill.create("unused", SkillLevel.REFLEXE)
        reg.register(s1)
        reg.register(s2)
        opt = SkillOptimizer(reg)
        pruned = opt.prune(5)
        assert pruned == 1
        assert reg.get(s1.id) is not None
        assert reg.get(s2.id) is None

    def test_rebalance(self):
        reg = SkillRegistry()
        s1 = Skill.create("a", SkillLevel.REFLEXE)
        s1.accuracy = 0.8
        s2 = Skill.create("b", SkillLevel.REACTIF)
        s2.accuracy = 0.6
        reg.register(s1)
        reg.register(s2)
        opt = SkillOptimizer(reg)
        stats = opt.rebalance()
        assert stats["n_skills"] == 2
        assert stats["mean_accuracy"] == 0.7


class TestForgeronEngine:
    def test_create(self):
        fg = ForgeronEngine()
        assert fg.registry.count() > 0

    def test_innate_skills(self):
        fg = ForgeronEngine()
        innate = fg.registry.list_by_category("innate")
        assert len(innate) >= 3

    def test_create_skill(self):
        fg = ForgeronEngine()
        s = fg.create_skill("dodge", SkillLevel.REACTIF, "esquive automatique")
        assert s.name == "dodge"
        assert fg.registry.get(s.id) is s

    def test_generate_skill(self):
        fg = ForgeronEngine()
        s = fg.generate_skill("synth", SkillLevel.GENERATIF)
        assert s is not None
        assert fg.registry.get(s.id) is s

    def test_train_skill(self):
        fg = ForgeronEngine()
        s = fg.create_skill("aim", SkillLevel.ADAPTATIF)
        assert fg.train_skill(s.id, True) is True
        assert s.accuracy > 0

    def test_train_skill_missing(self):
        fg = ForgeronEngine()
        assert fg.train_skill("nonexistent", True) is False

    def test_execute_skill(self):
        fg = ForgeronEngine()
        s = fg.create_skill("ping", SkillLevel.REFLEXE)
        result = fg.execute_skill(s.id)
        assert result is not None
        assert result["skill_name"] == "ping"

    def test_get_stats(self):
        fg = ForgeronEngine()
        fg.create_skill("a", SkillLevel.REFLEXE)
        fg.create_skill("b", SkillLevel.REACTIF)
        stats = fg.get_stats()
        assert stats["total_skills"] >= 5
        assert "innate" in stats["categories"]
        assert "by_level" in stats

    def test_process_with_skill(self):
        fg = ForgeronEngine()
        s = fg.create_skill("scan", SkillLevel.REACTIF)
        result = fg.process({"skill": "scan", "target": "file"})
        assert result["success"] is True

    def test_process_no_skill(self):
        fg = ForgeronEngine()
        result = fg.process({"data": 1})
        assert result["success"] is False
        assert "no skill" in result["error"]

    def test_process_bad_input(self):
        fg = ForgeronEngine()
        result = fg.process("invalid")
        assert result["success"] is False
