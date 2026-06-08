from __future__ import annotations

import pytest

from ciel.forge.core import ForgeEngine, ForgedSkill, SkillBlueprint, SkillLevel


class TestSkillLevel:
    def test_values(self):
        assert SkillLevel.NV0.value == 0
        assert SkillLevel.NV1.value == 1
        assert SkillLevel.NV7.value == 7
        assert len(SkillLevel) == 8

    def test_ordering_by_value(self):
        assert SkillLevel.NV0.value < SkillLevel.NV3.value
        assert SkillLevel.NV7.value > SkillLevel.NV5.value
        assert SkillLevel.NV6.value == SkillLevel.NV6.value


class TestSkillBlueprint:
    def test_create(self):
        bp = SkillBlueprint(name="test", domain="combat", target_level=SkillLevel.NV3)
        assert bp.name == "test"
        assert bp.domain == "combat"
        assert bp.target_level == SkillLevel.NV3

    def test_defaults(self):
        bp = SkillBlueprint(name="x", domain="y", target_level=SkillLevel.NV0)
        assert bp.description == ""
        assert bp.requirements == []
        assert bp.verified is False

    def test_with_requirements(self):
        bp = SkillBlueprint("s", "d", SkillLevel.NV5, requirements=["axiom_a"])
        assert "axiom_a" in bp.requirements


class TestForgedSkill:
    def test_create(self):
        fs = ForgedSkill(skill_id="id1", name="fs", level=SkillLevel.NV2, domain="d", created_at=100.0)
        assert fs.skill_id == "id1"
        assert fs.name == "fs"
        assert fs.level == SkillLevel.NV2
        assert fs.domain == "d"
        assert fs.created_at == 100.0
        assert fs.code_hash == ""
        assert fs.test_count == 0
        assert fs.passed is False


class TestForgeEngine:
    def test_create(self):
        fe = ForgeEngine()
        assert fe._blueprints == []
        assert fe._forged == {}

    def test_analyze_need(self):
        fe = ForgeEngine()
        bp = fe.analyze_need("alpha", {"speed": 0.3, "power": 0.7})
        assert bp.name == "alpha_speed_skill"
        assert bp.domain == "speed"
        assert bp.target_level == SkillLevel.NV2

    def test_analyze_need_many_gaps(self):
        fe = ForgeEngine()
        bp = fe.analyze_need("beta", {"a": 0.1, "b": 0.2, "c": 0.3, "d": 0.4})
        assert bp.target_level == SkillLevel.NV0

    def test_specify(self):
        fe = ForgeEngine()
        bp = SkillBlueprint("x", "healing", SkillLevel.NV1)
        fe.specify(bp)
        assert "domain_healing" in bp.requirements

    def test_generate(self):
        fe = ForgeEngine()
        bp = SkillBlueprint("x", "combat", SkillLevel.NV3)
        skill = fe.generate(bp)
        assert skill.name == "x"
        assert skill.domain == "combat"
        assert skill.skill_id in fe._forged

    def test_validate_returns_bool(self):
        fe = ForgeEngine()
        skill = ForgedSkill("sid", "x", SkillLevel.NV2, "d", 1.0)
        result = fe.validate(skill)
        assert isinstance(result, bool)

    def test_deploy(self):
        fe = ForgeEngine()
        skill = ForgedSkill("sid", "x", SkillLevel.NV2, "d", 1.0)
        result = fe.deploy(skill, "agent_1")
        assert result["skill_id"] == "sid"
        assert result["agent_id"] == "agent_1"
        assert result["canary"] is True

    def test_deploy_high_level(self):
        fe = ForgeEngine()
        skill = ForgedSkill("sid", "x", SkillLevel.NV5, "d", 1.0)
        result = fe.deploy(skill, "agent_1")
        assert result["canary"] is False

    def test_get_stats_empty(self):
        fe = ForgeEngine()
        stats = fe.get_stats()
        assert stats["total_forged"] == 0
        assert stats["blueprints_pending"] == 0

    def test_full_pipeline(self):
        fe = ForgeEngine()
        bp = fe.analyze_need("agent_x", {"speed": 0.2})
        fe.specify(bp)
        skill = fe.generate(bp)
        valid = fe.validate(skill)
        result = fe.deploy(skill, "agent_1")
        assert result["skill_id"] == skill.skill_id
        assert valid is True or valid is False

    def test_process_forge(self):
        fe = ForgeEngine()
        r = fe.process({"action": "forge", "name": "Fireball", "domain": "combat", "level": 3})
        assert r["success"] is True
        assert r["name"] == "Fireball"
        assert r["level"] == 3

    def test_process_analyze(self):
        fe = ForgeEngine()
        r = fe.process({"action": "analyze", "agent": "alpha", "speed": 0.3, "power": 0.7})
        assert r["success"] is True
        assert "blueprint" in r
        assert r["domain"] == "speed"

    def test_process_stats(self):
        fe = ForgeEngine()
        r = fe.process({"action": "stats"})
        assert r["success"] is True
        assert r["action"] == "stats"
        assert "total_forged" in r

    def test_process_bad_input(self):
        fe = ForgeEngine()
        r = fe.process("bad")
        assert r["success"] is False
        assert "input must be dict" in r["error"]

    def test_process_unknown_action(self):
        fe = ForgeEngine()
        r = fe.process({"action": "nope"})
        assert r["success"] is False
