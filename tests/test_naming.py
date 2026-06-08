from __future__ import annotations

import pytest

from ciel.naming.core import Agent, AgentTier, Skill, Grimoire, SoulCore, NamingEngine
from ciel.naming.agents import (
    PREDEFINED_AGENTS, RAPHAEL, CHRONOS, FORGE,
    SOEI, BENIMARU, SHION, SHUNA, KUROBE, DIABLO,
    TIER_S_AGENTS, TIER_A_AGENTS, bootstrap_naming_engine,
)


class TestAgent:
    def test_create(self):
        a = Agent("test", AgentTier.A, "test")
        assert a.soul.name == "test"
        assert a.soul.tier == AgentTier.A

    def test_learn_skill(self):
        a = Agent("test", AgentTier.B)
        s = Skill("Test Skill", 3, "A test", "test")
        a.learn_skill(s)
        assert a.grimoire.has("Test Skill")
        assert a.grimoire.max_level() == 3

    def test_unique_skill_limit(self):
        a = Agent("test", AgentTier.S)
        a.learn_skill(Skill("Unique1", 7, "", unique=True))
        a.learn_skill(Skill("Unique2", 7, "", unique=True))
        assert a.grimoire.has("Unique1")
        assert not a.grimoire.has("Unique2")

    def test_record_task(self):
        a = Agent("test", AgentTier.C)
        a.record_task(True)
        a.record_task(True)
        a.record_task(False)
        assert a.stats["tasks_done"] == 3
        assert a.stats["success_rate"] == pytest.approx(2 / 3)

    def test_harvest_festival(self):
        a = Agent("test", AgentTier.C)
        a.transcendence_gauge = 1.0
        result = a.harvest_festival()
        assert a.soul.tier == AgentTier.B
        assert a.generation == 1
        assert a.transcendence_gauge == 0.0
        assert result["from"] == "C"
        assert result["to"] == "B"

    def test_harvest_festival_max_tier(self):
        a = Agent("test", AgentTier.S)
        a.harvest_festival()
        assert a.soul.tier == AgentTier.S  # stays S

    def test_nominate_sub_agent(self):
        a = Agent("parent", AgentTier.A)
        child = a.nominate("child", AgentTier.B)
        assert child.soul.name == "child"
        assert child.soul.tier == AgentTier.B
        assert child.soul.nomination_signature != a.soul.nomination_signature

    def test_collect_data(self):
        a = Agent("test", AgentTier.B)
        a.collect_data({"key": "value" * 100})
        assert a.stats["data_collected"] > 0


class TestGrimoire:
    def test_add_skill(self):
        g = Grimoire()
        g.add(Skill("S1", 1))
        g.add(Skill("S2", 3))
        assert g.max_level() == 3

    def test_potential(self):
        g = Grimoire()
        g.potential.append(Skill("Future", 5))
        assert len(g.potential) == 1


class TestNamingEngine:
    def test_nominate(self):
        ne = NamingEngine()
        a = ne.nominate("test", AgentTier.B, "domain")
        assert a.soul.name == "test"
        assert len(ne.all_agents()) == 1

    def test_get_by_id(self):
        ne = NamingEngine()
        a = ne.nominate("test", AgentTier.A)
        assert ne.get(a.soul.agent_id) is a

    def test_get_by_name(self):
        ne = NamingEngine()
        ne.nominate("RAPHAEL", AgentTier.S)
        assert ne.find("RAPHAEL") is not None

    def test_children_of(self):
        ne = NamingEngine()
        p = ne.nominate("parent", AgentTier.A)
        ne.nominate("child", AgentTier.B, parent_id=p.soul.agent_id)
        children = ne.children_of(p.soul.agent_id)
        assert len(children) == 1
        assert children[0].soul.name == "child"

    def test_stats(self):
        ne = NamingEngine()
        ne.nominate("a", AgentTier.S)
        ne.nominate("b", AgentTier.A)
        ne.nominate("c", AgentTier.B)
        stats = ne.get_stats()
        assert stats["total"] == 3
        assert stats["by_tier"]["S"] == 1
        assert stats["by_tier"]["A"] == 1
        assert stats["by_tier"]["B"] == 1

    def test_process_nominate(self):
        ne = NamingEngine()
        r = ne.process({"action": "nominate", "name": "test", "tier": "A"})
        assert r["success"]
        assert r["name"] == "test"

    def test_process_list(self):
        ne = NamingEngine()
        ne.nominate("a", AgentTier.S)
        ne.nominate("b", AgentTier.A)
        r = ne.process({"action": "list"})
        assert r["success"]
        assert len(r["agents"]) == 2

    def test_process_harvest(self):
        ne = NamingEngine()
        a = ne.nominate("test", AgentTier.C)
        a.transcendence_gauge = 1.0
        r = ne.process({"action": "harvest", "name": "test"})
        assert r["success"]
        assert r["to"] == "B"

    def test_process_unknown_action(self):
        ne = NamingEngine()
        r = ne.process({"action": "unknown"})
        assert not r["success"]

    def test_process_bad_input(self):
        ne = NamingEngine()
        r = ne.process("bad")
        assert not r["success"]


class TestPredefinedAgents:
    def test_all_present(self):
        assert len(PREDEFINED_AGENTS) == 9
        assert all(name in PREDEFINED_AGENTS for name in TIER_S_AGENTS + TIER_A_AGENTS)

    def test_raphael_tier(self):
        assert RAPHAEL.soul.tier == AgentTier.S
        assert RAPHAEL.domain == "analyse"

    def test_raphael_unique_skill(self):
        assert RAPHAEL.grimoire.has("Analyse Absolue")
        assert RAPHAEL.grimoire.max_level() == 7

    def test_forge_unique_skill(self):
        assert FORGE.grimoire.has("Création du Néant")

    def test_chronos_unique_skill(self):
        assert CHRONOS.grimoire.has("Mémoire des Âges")

    def test_soei_unique_skill(self):
        assert SOEI.grimoire.has("Ombre Omnisciente")

    def test_benimaru_unique_skill(self):
        assert BENIMARU.grimoire.has("Commandement de Feu")

    def test_shion_unique_skill(self):
        assert SHION.grimoire.has("Symbiose Parfaite")

    def test_shuna_unique_skill(self):
        assert SHUNA.grimoire.has("Purification")

    def test_kurobe_unique_skill(self):
        assert KUROBE.grimoire.has("Frappe de Maître")

    def test_diablo_unique_skill(self):
        assert DIABLO.grimoire.has("Persuasion Absolue")

    def test_tier_s_cannot_have_two_unique(self):
        for name in TIER_S_AGENTS:
            a = PREDEFINED_AGENTS[name]
            uniques = [s for s in a.grimoire.skills if s.unique]
            assert len(uniques) <= 1

    def test_bootstrap(self):
        ne = NamingEngine()
        bootstrap_naming_engine(ne)
        assert ne.find("RAPHAEL") is not None
        assert ne.find("CHRONOS") is not None
        assert ne.find("FORGE") is not None
        assert ne.find("SOEI") is not None
        assert len(ne.all_agents()) == 9
