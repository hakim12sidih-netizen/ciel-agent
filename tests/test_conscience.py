from __future__ import annotations

import pytest
from ciel.conscience.core import (
    AwarenessLevel, Qualia, PhenomenalState,
    AccessConsciousness, GlobalWorkspace, AttentionSchema,
    SelfModel, Metacognition, Introspection,
    IntegratedInformation, BindingProblem, ConsciousState,
    ConsciousnessModel, ConsciousnessEngine,
)


class TestAwarenessLevel:
    def test_values(self):
        assert len(AwarenessLevel) == 5
        assert AwarenessLevel.NONE.value == 0
        assert AwarenessLevel.FOCAL.value == 3
        assert AwarenessLevel.META.value == 4


class TestQualia:
    def test_create(self):
        q = Qualia(modality="visual", intensity=0.8, valence=0.5, arousal=0.3, content="red")
        assert q.modality == "visual"
        assert q.intensity == 0.8
        assert q.valence == 0.5

    def test_normalize_clamps(self):
        q = Qualia(modality="audio", intensity=2.0, valence=-2.0, arousal=-0.5)
        q.normalize()
        assert q.intensity == 1.0
        assert q.valence == -1.0
        assert q.arousal == 0.0

    def test_normalize_ok(self):
        q = Qualia(modality="cognitive", intensity=0.5, valence=0.3, arousal=0.7)
        q.normalize()
        assert q.intensity == 0.5
        assert q.valence == 0.3
        assert q.arousal == 0.7


class TestPhenomenalState:
    def test_empty(self):
        p = PhenomenalState()
        assert p.coherence == 0.0
        assert p.binding_vector == []

    def test_add_qualia(self):
        p = PhenomenalState()
        p.add_qualia(Qualia(modality="visual", intensity=0.8))
        assert len(p.qualia) == 1
        assert p.coherence > 0

    def test_coherence(self):
        p = PhenomenalState()
        p.add_qualia(Qualia(modality="vis", intensity=0.9))
        p.add_qualia(Qualia(modality="aud", intensity=0.8))
        assert p.coherence > 0.8


class TestAccessConsciousness:
    def test_default(self):
        ac = AccessConsciousness()
        assert ac.reportable is True
        assert ac.available_content == {}
        assert ac.working_memory == []


class TestGlobalWorkspace:
    def test_broadcast(self):
        gw = GlobalWorkspace(capacity=3)
        gw.broadcast({"salience": 0.9, "data": "hello"})
        assert len(gw.contents) == 1
        assert len(gw.broadcast_history) == 1

    def test_capacity(self):
        gw = GlobalWorkspace(capacity=2)
        for i in range(5):
            gw.broadcast({"salience": 0.5, "data": i})
        assert len(gw.contents) == 2

    def test_compete(self):
        gw = GlobalWorkspace()
        winner = gw.compete([
            {"salience": 0.3, "data": "a"},
            {"salience": 0.9, "data": "b"},
            {"salience": 0.5, "data": "c"},
        ])
        assert winner["data"] == "b"

    def test_compete_empty(self):
        gw = GlobalWorkspace()
        assert gw.compete([]) is None

    def test_global_availability(self):
        gw = GlobalWorkspace()
        gw.broadcast({"data": 1})
        gw.broadcast({"data": 2})
        av = gw.global_availability()
        assert av[0]["data"] == 2

    def test_register_processor(self):
        gw = GlobalWorkspace()
        calls = []
        gw.register_processor(lambda c: calls.append(c))
        gw.broadcast({"salience": 1.0})
        assert len(calls) == 1


class TestAttentionSchema:
    def test_allocate(self):
        attn = AttentionSchema(capacity=1.0)
        attn.allocate("task_a", 0.6)
        assert attn.focus["task_a"] == 0.6

    def test_capacity_limit(self):
        attn = AttentionSchema(capacity=1.0)
        attn.allocate("a", 0.7)
        attn.allocate("b", 0.7)
        assert attn.focus.get("b", 0) < 0.4

    def test_tick_decay(self):
        attn = AttentionSchema(capacity=1.0)
        attn.allocate("x", 0.8)
        attn.tick()
        assert attn.focus["x"] < 0.8

    def test_current_focus(self):
        attn = AttentionSchema()
        assert attn.current_focus() is None
        attn.allocate("main", 0.5)
        assert attn.current_focus() == "main"

    def test_salience(self):
        attn = AttentionSchema(capacity=2.0)
        attn.allocate("a", 1.0)
        assert attn.salience("a") == 0.5
        assert attn.salience("b") == 0.0


class TestSelfModel:
    def test_defaults(self):
        sm = SelfModel()
        assert sm.agency_score == 0.5
        assert sm.ownership_score == 0.5
        assert sm.beliefs == {}
        assert sm.narrative == []

    def test_update_belief(self):
        sm = SelfModel()
        sm.update_belief("name", "CIEL")
        assert sm.beliefs["name"] == "CIEL"

    def test_add_narrative(self):
        sm = SelfModel()
        sm.add_narrative("awoke")
        assert "awoke" in sm.narrative

    def test_self_awareness_empty(self):
        sm = SelfModel()
        assert sm.self_awareness() == 0.0

    def test_self_awareness(self):
        sm = SelfModel()
        for i in range(8):
            sm.update_belief(f"k{i}", i)
        sm.agency_score = 1.0
        assert sm.self_awareness() > 0.5


class TestMetacognition:
    def test_monitor_default(self):
        m = Metacognition()
        report = m.monitor()
        assert "confidence" in report

    def test_judge(self):
        m = Metacognition()
        conf = m.judge("math", "correct")
        assert 0 <= conf <= 1
        assert len(m.judgments) == 1

    def test_calibration_perfect(self):
        m = Metacognition()
        assert m.calibration() == 1.0

    def test_calibration(self):
        m = Metacognition()
        m.confidence_scores = [0.7, 0.7, 0.7]
        assert m.calibration() == pytest.approx(1.0)


class TestIntrospection:
    def test_examine(self):
        i = Introspection()
        report = i.examine(PhenomenalState())
        assert report["type"] == "PhenomenalState"
        assert "n_qualia" in report
        assert "coherence" in report

    def test_examine_simple(self):
        i = Introspection()
        report = i.examine(42)
        assert report["type"] == "int"

    def test_accuracy(self):
        i = Introspection()
        assert i.introspective_accuracy() < 0.5
        for _ in range(10):
            i.examine(Qualia(modality="x"))
        assert i.introspective_accuracy() == 1.0


class TestIntegratedInformation:
    def test_empty(self):
        ii = IntegratedInformation()
        assert ii.phi == 0.0

    def test_compute_single(self):
        ii = IntegratedInformation.compute([[1.0]])
        assert ii.phi == 0.0

    def test_compute_phi_nonzero(self):
        tm = [
            [0.8, 0.2],
            [0.3, 0.7],
        ]
        ii = IntegratedInformation.compute(tm)
        assert ii.phi > 0

    def test_compute_phi_capped(self):
        tm = [
            [1.0, 0.0],
            [0.0, 1.0],
        ]
        ii = IntegratedInformation.compute(tm)
        assert ii.phi <= 1.0


class TestBindingProblem:
    def test_bind(self):
        bp = BindingProblem()
        bp.bind("obj1", "visual")
        assert "visual" in bp.bindings["obj1"]

    def test_bind_idempotent(self):
        bp = BindingProblem()
        bp.bind("o", "audio")
        bp.bind("o", "audio")
        assert len(bp.bindings["o"]) == 1

    def test_is_bound(self):
        bp = BindingProblem()
        bp.bind("o", "vis")
        bp.bind("o", "aud")
        assert bp.is_bound("o", ["vis", "aud"])
        assert not bp.is_bound("o", ["tactile"])

    def test_coherence_score(self):
        bp = BindingProblem()
        assert bp.coherence_score() == 1.0
        bp.bind("o1", "vis")
        bp.bind("o1", "aud")
        bp.bind("o2", "vis")
        score = bp.coherence_score()
        assert 0 < score <= 1.0


class TestConsciousState:
    def test_default(self):
        cs = ConsciousState()
        assert cs.awareness_level == AwarenessLevel.NONE
        assert cs.level_of_consciousness() >= 0

    def test_level_of_consciousness(self):
        cs = ConsciousState()
        cs.integrated_info.phi = 0.5
        cs.awareness_level = AwarenessLevel.FOCAL
        score = cs.level_of_consciousness()
        assert 0 <= score <= 1


class TestConsciousnessModel:
    def test_create(self):
        m = ConsciousnessModel()
        assert m.state is not None
        assert m.introspection is not None

    def test_perceive(self):
        m = ConsciousnessModel()
        m.perceive(Qualia(modality="vis", intensity=0.8, content="light"))
        assert len(m.state.phenomenal.qualia) == 1

    def test_attend(self):
        m = ConsciousnessModel()
        m.attend("target_a", 0.5)
        assert m.state.attention.current_focus() == "target_a"

    def test_tick(self):
        m = ConsciousnessModel()
        m.state.integrated_info.phi = 0.5
        state = m.tick()
        assert state.awareness_level in (AwarenessLevel.FOCAL, AwarenessLevel.META)

    def test_tick_low_phi(self):
        m = ConsciousnessModel()
        state = m.tick()
        assert state.awareness_level in (AwarenessLevel.NONE, AwarenessLevel.MINIMAL)

    def test_reflect(self):
        m = ConsciousnessModel()
        report = m.reflect()
        assert "type" in report
        assert "id" in report
        assert "repr" in report

    def test_bind(self):
        m = ConsciousnessModel()
        m.bind("obj", "visual")
        assert m.state.binding.is_bound("obj", ["visual"])

    def test_compute_phi(self):
        m = ConsciousnessModel()
        m.compute_phi([[0.8, 0.2], [0.3, 0.7]])
        assert m.state.integrated_info.phi > 0


class TestConsciousnessEngine:
    def test_create(self):
        e = ConsciousnessEngine()
        assert e.model is not None
        assert e._cycle_count == 0

    def test_perceive(self):
        e = ConsciousnessEngine()
        q = e.perceive("visual", "red light", intensity=0.9)
        assert q.modality == "visual"
        assert q.content == "red light"
        assert e._cycle_count == 1

    def test_attend(self):
        e = ConsciousnessEngine()
        e.attend("task", 0.8)
        assert e.model.state.attention.current_focus() == "task"

    def test_tick(self):
        e = ConsciousnessEngine()
        state = e.tick()
        assert isinstance(state, ConsciousState)

    def test_reflect(self):
        e = ConsciousnessEngine()
        report = e.reflect()
        assert "type" in report

    def test_bind(self):
        e = ConsciousnessEngine()
        e.bind("obj", "visual")
        assert e.model.state.binding.is_bound("obj", ["visual"])

    def test_compute_phi(self):
        e = ConsciousnessEngine()
        phi = e.compute_phi([[0.7, 0.3], [0.4, 0.6]])
        assert phi > 0

    def test_get_awareness_level(self):
        e = ConsciousnessEngine()
        assert isinstance(e.get_awareness_level(), AwarenessLevel)

    def test_get_consciousness_score(self):
        e = ConsciousnessEngine()
        score = e.get_consciousness_score()
        assert 0 <= score <= 1

    def test_get_stats(self):
        e = ConsciousnessEngine()
        e.perceive("vis", "hello")
        e.bind("o", "vis")
        stats = e.get_stats()
        assert "awareness_level" in stats
        assert "consciousness_score" in stats
        assert "phi" in stats
        assert "n_qualia" in stats
        assert "n_bindings" in stats
        assert "cycles" in stats

    def test_process_perceive(self):
        e = ConsciousnessEngine()
        r = e.process({"action": "perceive", "modality": "auditory", "content": "beep"})
        assert r["success"] is True

    def test_process_attend(self):
        e = ConsciousnessEngine()
        r = e.process({"action": "attend", "target": "focus", "amount": 0.5})
        assert r["success"] is True

    def test_process_tick(self):
        e = ConsciousnessEngine()
        r = e.process({"action": "tick"})
        assert r["success"] is True
        assert "state" in r

    def test_process_reflect(self):
        e = ConsciousnessEngine()
        r = e.process({"action": "reflect"})
        assert r["success"] is True
        assert "report" in r

    def test_process_bind(self):
        e = ConsciousnessEngine()
        r = e.process({"action": "bind", "object_id": "obj", "modality": "vis"})
        assert r["success"] is True

    def test_process_phi(self):
        e = ConsciousnessEngine()
        r = e.process({"action": "phi", "matrix": [[0.8, 0.2], [0.3, 0.7]]})
        assert r["success"] is True
        assert r["phi"] > 0

    def test_process_stats(self):
        e = ConsciousnessEngine()
        r = e.process({"action": "stats"})
        assert r["success"] is True
        assert "stats" in r

    def test_process_bad_action(self):
        e = ConsciousnessEngine()
        r = e.process({"action": "bogus"})
        assert r["success"] is False

    def test_process_bad_input(self):
        e = ConsciousnessEngine()
        r = e.process("bad")
        assert r["success"] is False
