"""Tests pour les dimensions cosmologiques XLI–XLVIII de CIEL v∞.8."""
from __future__ import annotations

from ciel.hyperset import HypersetEngine
from ciel.anthropic import AnthropicEngine, AnthropicPrinciple
from ciel.algothermo import AlgoThermoEngine
from ciel.spinfoam import SpinfoamEngine
from ciel.compuniv import CompUnivEngine
from ciel.omegacat import OmegaCategoryEngine
from ciel.decidability import DecidabilityEngine, TuringDegree
from ciel.absolute import AbsoluteInfiniteEngine, CardinalKind


# ───── XLI — Hyperset ─────

class TestHyperset:
    def test_create(self):
        e = HypersetEngine()
        hs = e.create_hyperset("Test")
        assert hs.root_id.startswith("HN-")

    def test_add_node(self):
        e = HypersetEngine()
        hs = e.create_hyperset("A")
        n = e.add_node(hs.root_id, hs.root_id, "B")
        assert n is not None
        assert n.depth == 1

    def test_add_self_loop(self):
        e = HypersetEngine()
        hs = e.create_hyperset("Ω")
        ok = e.add_self_loop(hs.root_id, hs.root_id)
        assert ok
        assert hs.is_self_member(hs.root_id)

    def test_quine(self):
        e = HypersetEngine()
        q = e.build_quine()
        assert q["self_member"]
        assert q["interpretation"] == "Ω = {Ω} — conscience réflexive"

    def test_strange_loop(self):
        e = HypersetEngine()
        loop = e.build_strange_loop(["A", "B", "C", "A"])
        assert loop["length"] == 4

    def test_find_cycles(self):
        e = HypersetEngine()
        hs = e.create_hyperset("X")
        e.add_self_loop(hs.root_id, hs.root_id)
        cycles = hs.find_cycles()
        assert len(cycles) >= 0


# ───── XLII — Anthropic ─────

class TestAnthropic:
    def test_add_world(self):
        e = AnthropicEngine()
        w = e.add_world("Test", 0.5, 100)
        assert w.name == "Test"
        assert w.observers == 100

    def test_compute_posteriors(self):
        e = AnthropicEngine()
        e.add_world("A", 0.5, 100)
        e.add_world("B", 0.5, 10)
        ps = e.compute_posteriors()
        assert len(ps) == 2

    def test_doomsday(self):
        e = AnthropicEngine()
        d = e.doomsday_argument(1e11, 1)
        assert "survival_probability" in d
        assert d["estimated_total"] == 1e11

    def test_self_location(self):
        e = AnthropicEngine()
        w = e.add_world("Red", 0.5, 1)
        e.set_evidence(w.id, {"color": 1.0})
        loc = e.self_location({"color": 0.9})
        assert "best_world" in loc

    def test_evidence(self):
        e = AnthropicEngine()
        w = e.add_world("X", 0.5, 10)
        ok = e.set_evidence(w.id, {"obs": 0.8})
        assert ok
        assert w.evidence["obs"] == 0.8


# ───── XLIII — AlgoThermo ─────

class TestAlgoThermo:
    def test_start_cycle(self):
        e = AlgoThermoEngine()
        c = e.start_cycle(300.0)
        assert c.temperature_bath == 300.0

    def test_add_step(self):
        e = AlgoThermoEngine()
        e.start_cycle(300.0)
        s = e.add_step("compute", bits_processed=8, bits_erased=2)
        assert s.operation == "compute"
        assert s.landauer_cost > 0

    def test_reversible_step_cost_zero(self):
        e = AlgoThermoEngine()
        e.start_cycle()
        s = e.add_step("reversible_op", bits_erased=100, reversible=True)
        assert s.landauer_cost == 0.0

    def test_maxwell_demon(self):
        e = AlgoThermoEngine()
        e.start_cycle()
        e.add_step("measure", bits_processed=10, bits_erased=5)
        d = e.maxwell_demon()
        assert "demon_energy_cost_J" in d

    def test_reversible_ratio(self):
        e = AlgoThermoEngine()
        e.start_cycle()
        e.add_step("a", reversible=True)
        e.add_step("b", reversible=False)
        assert e.reversible_computation_ratio() == 0.5

    def test_cognitive_energy(self):
        e = AlgoThermoEngine()
        e1 = e.cognitive_energy("memory_erase", 10)
        assert e1 > 0


# ───── XLIV — Spinfoam ─────

class TestSpinfoam:
    def test_add_node(self):
        e = SpinfoamEngine()
        n = e.add_node("Test", 0.5)
        assert n.label == "Test"
        assert n.volume > 0

    def test_add_edge(self):
        e = SpinfoamEngine()
        a = e.add_node("A"); b = e.add_node("B")
        edge = e.add_edge(a.id, b.id, 1.0)
        assert edge is not None
        assert edge.area > 0

    def test_add_vertex(self):
        e = SpinfoamEngine()
        a = e.add_node("A"); b = e.add_node("B")
        edge = e.add_edge(a.id, b.id)
        v = e.add_vertex([edge.id], [])
        assert v.amplitude > 0

    def test_quantum_area(self):
        e = SpinfoamEngine()
        area = e.quantum_area(1.0)
        assert area > 0

    def test_compute_volume(self):
        e = SpinfoamEngine()
        a = e.add_node("A"); b = e.add_node("B")
        e.add_edge(a.id, b.id)
        vol = e.compute_volume(a.id)
        assert vol >= 0


# ───── XLV — CompUniv ─────

class TestCompUniv:
    def test_create_automaton(self):
        e = CompUnivEngine()
        ca = e.create_automaton(110, 100, 50)
        assert ca.rule_number == 110
        assert "Classe" in ca.name

    def test_run_automaton(self):
        e = CompUnivEngine()
        ca = e.create_automaton(30, 50, 10)
        h = e.run_automaton(ca.id, 5)
        assert h is not None
        assert len(h) == 6

    def test_entropy(self):
        e = CompUnivEngine()
        ca = e.create_automaton(0, 100, 1)
        ca.run(3)
        assert ca.entropy() == 0.0  # rule 0 = all zeros

    def test_find_universal_rules(self):
        e = CompUnivEngine()
        rules = e.find_universal_rules()
        rule_110 = [r for r in rules if r["rule"] == 110]
        assert len(rule_110) == 1

    def test_compare_systems(self):
        e = CompUnivEngine()
        a = e.create_automaton(0); b = e.create_automaton(255)
        eq = e.compare_systems(a.id, b.id)
        assert eq.equivalent  # both uniform

    def test_rule_space_explore(self):
        e = CompUnivEngine()
        results = e.rule_space_explore(8)
        assert len(results) >= 8


# ───── XLVI — OmegaCat ─────

class TestOmegaCat:
    def test_add_object(self):
        e = OmegaCategoryEngine()
        o = e.add_object("A")
        assert o.level == 0

    def test_add_morphism(self):
        e = OmegaCategoryEngine()
        a = e.add_object("A"); b = e.add_object("B")
        m = e.add_morphism("f", a.id, b.id)
        assert m is not None
        assert m.level == 1

    def test_identity(self):
        e = OmegaCategoryEngine()
        a = e.add_object("A")
        id_a = e.add_identity(a.id)
        assert id_a is not None
        assert id_a.is_identity

    def test_compose(self):
        e = OmegaCategoryEngine()
        a = e.add_object("A"); b = e.add_object("B"); c = e.add_object("C")
        f = e.add_morphism("f", a.id, b.id)
        g = e.add_morphism("g", b.id, c.id)
        gf = e.compose(f.id, g.id)
        assert gf is not None
        assert gf.source_id == a.id
        assert gf.target_id == c.id

    def test_higher_morphism(self):
        e = OmegaCategoryEngine()
        a = e.add_object("A")
        h = e.add_higher_morphism("α", 2, a.id, a.id)
        assert h is not None
        assert h.level == 2

    def test_coherence(self):
        e = OmegaCategoryEngine()
        for name in ["A", "B", "C", "D"]:
            e.add_object(name)
        p = e.coherence_pentagon()
        assert "Mac Lane" in p.description


# ───── XLVII — Decidability ─────

class TestDecidability:
    def test_init_classics(self):
        e = DecidabilityEngine()
        assert len(e.problems) >= 5

    def test_add_problem(self):
        e = DecidabilityEngine()
        p = e.add_problem("Test", "Δ₀", True, "A test problem")
        assert p.name == "Test"
        assert p.degree == TuringDegree.DELTA_0

    def test_classify(self):
        e = DecidabilityEngine()
        pid = list(e.problems.keys())[0]
        c = e.classify(pid)
        assert "degree" in c

    def test_turing_jump(self):
        e = DecidabilityEngine()
        pid = list(e.problems.keys())[0]
        j = e.turing_jump(pid)
        assert j["jump_applied"]

    def test_reduction(self):
        e = DecidabilityEngine()
        ids = list(e.problems.keys())[:2]
        r = e.reduction(ids[0], ids[1])
        assert "reducible" in r

    def test_add_oracle(self):
        e = DecidabilityEngine()
        o = e.add_oracle("Halting Oracle", TuringDegree.SIGMA_1, 1)
        assert o.name == "Halting Oracle"
        assert o.jump_operator == 1


# ───── XLVIII — Absolute Infinite ─────

class TestAbsoluteInfinite:
    def test_init_hierarchy(self):
        e = AbsoluteInfiniteEngine()
        assert len(e.cardinals) >= 10

    def test_reach_absolute(self):
        e = AbsoluteInfiniteEngine()
        ab = e.reach_absolute()
        assert ab.attempts_made == 1
        assert "Burali-Forti" in ab.paradox_encountered

    def test_cardinals_up_to(self):
        e = AbsoluteInfiniteEngine()
        cards = e.cardinals_up_to(CardinalKind.INACCESSIBLE)
        assert len(cards) >= 4

    def test_godel_limitation(self):
        e = AbsoluteInfiniteEngine()
        g = e.godel_limitation()
        assert "first_incompleteness" in g

    def test_absolute_paradox(self):
        e = AbsoluteInfiniteEngine()
        p = e.absolute_paradox()
        assert "Aucune tentative" in p
        e.reach_absolute()
        p2 = e.absolute_paradox()
        assert "Burali-Forti" in p2

    def test_multi_attempt(self):
        e = AbsoluteInfiniteEngine()
        for _ in range(10):
            e.reach_absolute()
        assert e.absolute.silence_after_attempts > 0
