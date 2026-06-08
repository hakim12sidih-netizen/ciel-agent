from __future__ import annotations

import pytest
from ciel.hydra_core.core import (
    SystemBus, Event, EventPriority,
    TitanNVM,
    AgentRole, AgentProposal, ConsensusResult, Pantheon,
    SkillGraph, SkillNode,
    ThoughtType, Thought, ThoughtTree,
    Chromosome, Gene, UnifiedGenome,
    ImperialCycle,
    Aegis, MutationPatch, MetamorphicCore,
    RewardVector, TitanRL,
    HydraBrain, HydraEngine,
)


class TestSystemBus:
    def test_emit_and_subscribe(self):
        bus = SystemBus()
        received = []
        bus.subscribe("test", lambda e: received.append(e.type))
        bus.emit("test")
        assert "test" in received

    def test_unsubscribe(self):
        bus = SystemBus()
        def handler(e): pass
        bus.subscribe("x", handler)
        assert bus.unsubscribe("x", handler) is True
        assert bus.unsubscribe("x", handler) is False

    def test_history(self):
        bus = SystemBus()
        bus.emit("a")
        bus.emit("b")
        bus.emit("a")
        assert len(bus.history()) == 3
        assert len(bus.history("a")) == 2

    def test_clear(self):
        bus = SystemBus()
        bus.emit("x")
        bus.clear()
        assert len(bus.history()) == 0

    def test_event_priority(self):
        bus = SystemBus()
        e = bus.emit("test", priority=EventPriority.HIGH)
        assert e.priority == EventPriority.HIGH


class TestTitanNVM:
    def test_store_and_load(self):
        nvm = TitanNVM()
        nvm.store("key1", "value1")
        assert nvm.load("key1") == "value1"

    def test_load_missing(self):
        nvm = TitanNVM()
        assert nvm.load("nonexistent") is None

    def test_delete(self):
        nvm = TitanNVM()
        nvm.store("k", "v")
        assert nvm.delete("k") is True
        assert nvm.load("k") is None

    def test_query_by_tag(self):
        nvm = TitanNVM()
        nvm.store("a", 1, tags=["math"])
        nvm.store("b", 2, tags=["math"])
        nvm.store("c", 3, tags=["science"])
        assert len(nvm.query("math")) == 2
        assert len(nvm.query("science")) == 1

    def test_prune(self):
        nvm = TitanNVM()
        nvm.store("temp", "data", ttl_s=-1)
        assert nvm.prune() >= 0

    def test_size(self):
        nvm = TitanNVM()
        assert nvm.size() == 0
        nvm.store("k", "v")
        assert nvm.size() == 1

    def test_clear(self):
        nvm = TitanNVM()
        nvm.store("k", "v")
        nvm.clear()
        assert nvm.size() == 0

    def test_expired(self):
        nvm = TitanNVM()
        nvm.store("temp", "x", ttl_s=0.001)
        import time; time.sleep(0.002)
        assert nvm.load("temp") is None


class TestPantheon:
    def test_list_agents(self):
        p = Pantheon()
        agents = p.list_agents()
        assert len(agents) == 11

    def test_get_agent(self):
        p = Pantheon()
        zeus = p.get_agent(AgentRole.ZEUS)
        assert zeus is not None
        assert zeus["name"] == "Zeus"

    def test_activate_deactivate(self):
        p = Pantheon()
        p.deactivate(AgentRole.ARES)
        assert len(p.list_agents()) == 10
        p.activate(AgentRole.ARES)
        assert len(p.list_agents()) == 11

    def test_propose(self):
        p = Pantheon()
        prop = p.propose(AgentRole.ATHENA, "attack plan", 0.85)
        assert prop.agent == AgentRole.ATHENA
        assert prop.proposal == "attack plan"

    def test_consensus_empty(self):
        p = Pantheon()
        result = p.bcq_consensus([])
        assert result.accepted is False

    def test_consensus_single(self):
        p = Pantheon()
        props = [AgentProposal(AgentRole.ZEUS, "yes", 0.9)]
        result = p.bcq_consensus(props)
        assert result.accepted is True

    def test_consensus_multiple(self):
        p = Pantheon()
        props = [
            AgentProposal(AgentRole.ZEUS, "plan A", 0.8),
            AgentProposal(AgentRole.ATHENA, "plan B", 0.6),
            AgentProposal(AgentRole.HERMES, "plan C", 0.4),
        ]
        result = p.bcq_consensus(props)
        assert result.final_proposal == "plan A"


class TestSkillGraph:
    def test_register_and_get(self):
        g = SkillGraph()
        g.register("s1", "scan", "scanning tool", tags=["perception"])
        assert g.get("s1") is not None
        assert g.get("s1").name == "scan"

    def test_unregister(self):
        g = SkillGraph()
        g.register("s1", "x")
        assert g.unregister("s1") is True
        assert g.get("s1") is None

    def test_select_by_tags(self):
        g = SkillGraph()
        g.register("s1", "scan", tags=["perception"])
        g.register("s2", "think", tags=["reasoning"])
        g.register("s3", "move", tags=["action"])
        assert len(g.select(["perception"])) == 1
        assert len(g.select(["action", "reasoning"])) == 2

    def test_traverse(self):
        g = SkillGraph()
        g.register("root", "root", dependencies=["a", "b"])
        g.register("a", "a", dependencies=["c"])
        g.register("b", "b")
        g.register("c", "c")
        assert len(g.traverse("root")) == 4

    def test_prune(self):
        g = SkillGraph()
        g.register("old", "old")
        g.prune(max_age_s=-1)
        assert g.get("old") is None


class TestThoughtTree:
    def test_add_thought(self):
        t = ThoughtTree()
        thought = t.add_thought(ThoughtType.OBSERVE, "seeing something")
        assert thought.type == ThoughtType.OBSERVE
        assert thought.content == "seeing something"

    def test_path_from_root(self):
        t = ThoughtTree()
        r = t.add_thought(ThoughtType.OBSERVE, "root")
        c = t.add_thought(ThoughtType.DECIDE, "child", parent=r.id)
        path = t.path_from_root(c.id)
        assert len(path) == 2
        assert path[0].id == r.id

    def test_traverse(self):
        t = ThoughtTree()
        r = t.add_thought(ThoughtType.OBSERVE, "root")
        t.add_thought(ThoughtType.DECIDE, "c1", parent=r.id)
        t.add_thought(ThoughtType.ACT, "c2", parent=r.id)
        assert len(t.traverse()) == 3

    def test_depth(self):
        t = ThoughtTree()
        r = t.add_thought(ThoughtType.OBSERVE, "r")
        c = t.add_thought(ThoughtType.DECIDE, "c", parent=r.id)
        t.add_thought(ThoughtType.ACT, "gc", parent=c.id)
        assert t.depth() == 3

    def test_leaf_count(self):
        t = ThoughtTree()
        r = t.add_thought(ThoughtType.OBSERVE, "r")
        t.add_thought(ThoughtType.DECIDE, "c1", parent=r.id)
        t.add_thought(ThoughtType.ACT, "c2", parent=r.id)
        assert t.leaf_count() == 2


class TestUnifiedGenome:
    def test_create(self):
        g = UnifiedGenome.create("test", n_genes=10)
        assert g.name == "test"
        assert len(g.genes) == 10

    def test_mutate(self):
        g = UnifiedGenome.create("test", n_genes=50)
        old_values = {k: v.value for k, v in g.genes.items()}
        g.mutate(rate=1.0, amplitude=0.5)
        new_values = {k: v.value for k, v in g.genes.items()}
        assert old_values != new_values

    def test_crossover(self):
        a = UnifiedGenome.create("A", n_genes=20)
        b = UnifiedGenome.create("B", n_genes=20)
        child = a.crossover(b)
        assert child.name == "A_B"
        assert len(child.genes) == 20
        assert len(child.parent_ids) == 2

    def test_distance(self):
        a = UnifiedGenome.create("A", n_genes=10)
        b = UnifiedGenome.create("B", n_genes=10)
        d = a.distance_to(b)
        assert d >= 0

    def test_chromosome_summary(self):
        g = UnifiedGenome.create("test", n_genes=40)
        summary = g.chromosome_summary()
        assert set(summary.keys()) == {"struct", "behavior", "epigenetic", "meta"}


class TestImperialCycle:
    def test_initialize(self):
        cycle = ImperialCycle(population_size=20)
        cycle.initialize()
        assert len(cycle.population) == 20

    def test_step(self):
        cycle = ImperialCycle(population_size=20, n_genes=10)
        cycle.initialize()
        result = cycle.step()
        assert result["generation"] == 1
        assert "best_fitness" in result

    def test_get_best(self):
        cycle = ImperialCycle(population_size=10)
        cycle.initialize()
        cycle.step()
        assert cycle.get_best() is not None

    def test_custom_fitness(self):
        cycle = ImperialCycle(population_size=10)
        cycle.set_fitness_fn(lambda g: g.karma)
        cycle.initialize()
        cycle.step()
        assert cycle.generation == 1


class TestAegis:
    def test_verify_clean(self):
        aegis = Aegis()
        valid, issues = aegis.verify("x = 1 + 2")
        assert valid is True
        assert issues == []

    def test_verify_forbidden(self):
        aegis = Aegis()
        valid, issues = aegis.verify("eval('x')")
        assert valid is False
        assert any("eval" in i for i in issues)


class TestMetamorphicCore:
    def test_propose(self):
        meta = MetamorphicCore()
        patch = meta.propose("file.py", "old", "new", "fix bug")
        assert patch is not None
        assert patch.description == "fix bug"
        assert patch.status == "pending"

    def test_propose_rejected(self):
        meta = MetamorphicCore()
        patch = meta.propose("file.py", "old", "eval('bad')")
        assert patch is None

    def test_apply_and_rollback(self):
        meta = MetamorphicCore()
        patch = meta.propose("f.py", "old", "new")
        assert patch is not None
        assert meta.apply(patch.id) is True
        assert meta.rollback(patch.id) is True
        assert meta.rollback(patch.id) is False


class TestTitanRL:
    def test_evaluate(self):
        rl = TitanRL()
        reward = RewardVector(success=1.0, efficiency=0.5)
        score = rl.evaluate(reward)
        assert isinstance(score, float)

    def test_update(self):
        rl = TitanRL()
        reward = RewardVector(success=1.0, efficiency=0.8, novelty=0.3)
        episode = rl.update(reward)
        assert "total" in episode
        assert episode["total"] > 0

    def test_get_weights(self):
        rl = TitanRL()
        w = rl.get_weights()
        assert len(w) == 12


class TestHydraBrain:
    def test_observe(self):
        brain = HydraBrain()
        t = brain.observe({"temp": 25})
        assert t.type == ThoughtType.OBSERVE

    def test_orient(self):
        brain = HydraBrain()
        obs = brain.observe({"x": 1})
        ori = brain.orient(obs)
        assert ori.type == ThoughtType.ORIENT

    def test_decide(self):
        brain = HydraBrain()
        obs = brain.observe({"x": 1})
        ori = brain.orient(obs)
        dec = brain.decide(ori)
        assert dec.type == ThoughtType.DECIDE

    def test_act(self):
        brain = HydraBrain()
        obs = brain.observe({"x": 1})
        ori = brain.orient(obs)
        dec = brain.decide(ori)
        act = brain.act(dec)
        assert act.type == ThoughtType.ACT

    def test_reflect(self):
        brain = HydraBrain()
        obs = brain.observe({"x": 1})
        ori = brain.orient(obs)
        dec = brain.decide(ori)
        act = brain.act(dec)
        ref = brain.reflect(act)
        assert ref.type == ThoughtType.REFLECT

    def test_full_cycle(self):
        brain = HydraBrain()
        result = brain.full_cycle({"input": "test"})
        assert result["cycle"] == 1
        assert "observe" in result
        assert "reflect" in result


class TestHydraEngine:
    def test_create(self):
        engine = HydraEngine()
        assert engine.pantheon is not None
        assert engine.brain is not None
        assert engine.evolution is not None

    def test_ooda_cycle(self):
        engine = HydraEngine()
        result = engine.ooda_cycle({"input": "hello"})
        assert result["cycle"] == 1

    def test_evolution_step(self):
        engine = HydraEngine()
        result = engine.evolution_step()
        assert result["generation"] == 1

    def test_train_rl(self):
        engine = HydraEngine()
        reward = RewardVector(success=1.0)
        result = engine.train_rl(reward)
        assert "total" in result

    def test_propose_mutation(self):
        engine = HydraEngine()
        patch = engine.propose_mutation("f.py", "old", "new")
        if patch:
            assert patch.status == "pending"

    def test_get_stats(self):
        engine = HydraEngine()
        stats = engine.get_stats()
        assert "uptime_s" in stats
        assert "generation" in stats
        assert "agents_active" in stats

    def test_process_ooda(self):
        engine = HydraEngine()
        result = engine.process({"action": "ooda", "input": "hello"})
        assert result["success"] is True
        assert result["action"] == "ooda"

    def test_process_evolve(self):
        engine = HydraEngine()
        result = engine.process({"action": "evolve"})
        assert result["success"] is True

    def test_process_rl(self):
        engine = HydraEngine()
        result = engine.process({"action": "rl", "success": 1.0})
        assert result["success"] is True

    def test_process_stats(self):
        engine = HydraEngine()
        result = engine.process({"action": "stats"})
        assert result["success"] is True
        assert "stats" in result

    def test_process_bad_action(self):
        engine = HydraEngine()
        result = engine.process({"action": "unknown"})
        assert result["success"] is False

    def test_process_bad_input(self):
        engine = HydraEngine()
        result = engine.process("bad")
        assert result["success"] is False

    def test_process_propose(self):
        engine = HydraEngine()
        result = engine.process({"action": "propose", "agent": "zeus", "proposal": "do x", "confidence": 0.9})
        assert result["success"] is True

    def test_process_propose_bad_agent(self):
        engine = HydraEngine()
        result = engine.process({"action": "propose", "agent": "nope", "proposal": "x"})
        assert result["success"] is False

    def test_process_consensus(self):
        engine = HydraEngine()
        result = engine.process({
            "action": "consensus",
            "proposals": [
                {"agent": "zeus", "proposal": "A", "confidence": 0.8},
                {"agent": "athena", "proposal": "B", "confidence": 0.6},
            ],
        })
        assert result["success"] is True

    def test_process_consensus_empty(self):
        engine = HydraEngine()
        result = engine.process({"action": "consensus", "proposals": []})
        assert result["success"] is False
