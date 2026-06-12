"""Tests pour les 10 dimensions cosmologiques CIEL v∞.8 (XXXI–XL)."""
from __future__ import annotations

import pytest
from ciel.hott import HoTTEngine, HLevel
from ciel.topos import ToposEngine, ToposType, TruthValue
from ciel.langlands import LanglandsEngine
from ciel.noncommutative import NonCommutativeEngine
from ciel.amplituhedron import AmplituhedronEngine, AmplituhedronConfig
from ciel.cobordism import CobordismEngine
from ciel.surreal import SurrealEngine, SurrealNumber, zero, one, omega, epsilon
from ciel.perfectoid import PerfectoidEngine
from ciel.trinity import TrinityEngine, Sort, TrinityFace
from ciel.metafoundation import MetaFoundationEngine, Foundation


# ───── DIMENSION XXXI — HoTT ─────

class TestHoTT:
    def test_create_cell(self):
        e = HoTTEngine()
        c = e.create_cell("TestType", HLevel.SET)
        assert c.id.startswith("CELL-")
        assert c.label == "TestType"
        assert c.level == HLevel.SET

    def test_create_path(self):
        e = HoTTEngine()
        a = e.create_cell("A")
        b = e.create_cell("B")
        p = e.create_path(a.id, b.id)
        assert p is not None
        assert p.source_id == a.id
        assert p.target_id == b.id

    def test_create_homotopy(self):
        e = HoTTEngine()
        a = e.create_cell("A")
        p1 = e.create_path(a.id, a.id)
        p2 = e.create_path(a.id, a.id)
        h = e.create_homotopy(p1.id, p2.id)
        assert h is not None
        assert h.path_a_id == p1.id

    def test_compose_paths(self):
        e = HoTTEngine()
        a = e.create_cell("A"); b = e.create_cell("B"); c = e.create_cell("C")
        p1 = e.create_path(a.id, b.id)
        p2 = e.create_path(b.id, c.id)
        p3 = e.compose_paths(p1.id, p2.id)
        assert p3 is not None
        assert p3.source_id == a.id
        assert p3.target_id == c.id

    def test_search_equivalences(self):
        e = HoTTEngine()
        e.create_cell("code review")
        e.create_cell("code lint")
        eq = e.search_equivalences(threshold=0.3)
        assert len(eq) >= 1

    def test_process(self):
        e = HoTTEngine()
        r = e.process({"action": "create_cell", "label": "Test", "level": 0})
        assert r["status"] == "ok"
        assert r["cell"]["label"] == "Test"


# ───── DIMENSION XXXII — Topos ─────

class TestTopos:
    def test_evaluate_science(self):
        e = ToposEngine()
        tv = e.evaluate(0.7, ToposType.SCIENCE)
        assert tv.value == 1.0  # classifié

    def test_evaluate_incertitude(self):
        e = ToposEngine()
        tv = e.evaluate(0.7, ToposType.INCERTITUDE)
        assert 0.5 <= tv.value <= 1.0

    def test_translate(self):
        e = ToposEngine()
        tv = TruthValue(0.8, 1.0)
        t = e.translate(tv, ToposType.SCIENCE, ToposType.INCERTITUDE)
        assert t.value == 0.8  # no morphism yet, identity

    def test_select_topos(self):
        e = ToposEngine()
        assert e.select_topos("proof of theorem") == ToposType.SCIENCE
        assert e.select_topos("probability risk") == ToposType.INCERTITUDE
        assert e.select_topos("create art") == ToposType.CREATIF

    def test_create_morphism(self):
        e = ToposEngine()
        m = e.create_morphism(ToposType.SCIENCE, ToposType.SOCIAL, fidelity=0.9)
        assert m.source_topos == ToposType.SCIENCE
        assert m.target_topos == ToposType.SOCIAL

    def test_truth_value_operations(self):
        a = TruthValue(0.8); b = TruthValue(0.3)
        assert (a & b).value == 0.3
        assert (a | b).value == 0.8
        assert abs((~a).value - 0.2) < 1e-10


# ───── DIMENSION XXXIII — Langlands ─────

class TestLanglands:
    def test_register_domain(self):
        e = LanglandsEngine()
        lf = e.register_domain("physics")
        assert lf.domain == "physics"
        assert len(lf.coefficients) == 30

    def test_find_correspondences(self):
        e = LanglandsEngine()
        e.register_domain("finance")
        e.register_domain("thermodynamics")
        corrs = e.find_correspondences(threshold=1.0)
        assert len(corrs) >= 1

    def test_suggest_transfer(self):
        e = LanglandsEngine()
        e.register_domain("A")
        e.register_domain("B")
        t = e.suggest_transfer("A", "B")
        assert "transferable" in t

    def test_find_isomorphic(self):
        e = LanglandsEngine()
        e.register_domain("code")
        e.register_domain("topology")
        results = e.find_isomorphic_domain("code")
        assert isinstance(results, list)


# ───── DIMENSION XXXIV — Non-Commutative ─────

class TestNonCommutative:
    def test_create_operator(self):
        e = NonCommutativeEngine()
        op = e.create_operator("Test", [[1.0, 0.0], [0.0, 1.0]])
        assert op.name == "Test"
        assert op.dimension == 2

    def test_base_operators(self):
        e = NonCommutativeEngine()
        assert len(e.operators) >= 3

    def test_measure_commutation(self):
        e = NonCommutativeEngine()
        ids = list(e.operators.keys())
        r = e.measure_commutation(ids[0], ids[1])
        assert "commutator_norm" in r

    def test_uncertainty(self):
        e = NonCommutativeEngine()
        ids = list(e.operators.keys())
        u = e.uncertainty(ids[0], ids[1])
        assert u >= 0

    def test_connes_distance(self):
        e = NonCommutativeEngine()
        d = e.measure_state_distance([0.0, 1.0], [0.5, 0.5])
        assert d >= 0


# ───── DIMENSION XXXV — Amplituhedron ─────

class TestAmplituhedron:
    def test_create(self):
        e = AmplituhedronEngine()
        amp = e.create_amplituhedron(4, 2)
        assert amp.config.n == 4
        assert amp.config.k == 2

    def test_compute_interaction(self):
        e = AmplituhedronEngine()
        r = e.compute_interaction([[1.0, 0.0], [0.0, 1.0]], n=2, k=1)
        assert "amplitude" in r

    def test_bcfw_recursion(self):
        e = AmplituhedronEngine()
        r = e.bcfw_recursion(["A", "B", "C", "D"])
        assert len(r) > 0

    def test_positivity(self):
        e = AmplituhedronEngine()
        assert e.positivity_check(0.5)
        assert e.positivity_check(0.0)


# ───── DIMENSION XXXVI — Cobordism ─────

class TestCobordism:
    def test_create_state(self):
        e = CobordismEngine()
        s = e.create_state("Test")
        assert s.name == "Test"
        assert s.id.startswith("STATE-")

    def test_init_states(self):
        e = CobordismEngine()
        assert len(e.states) >= 6

    def test_create_cobordism(self):
        e = CobordismEngine()
        ids = list(e.states.keys())
        c = e.create_cobordism(ids[0], ids[1], "évolution")
        assert c is not None
        assert c.source_id == ids[0]
        assert c.target_id == ids[1]

    def test_compose(self):
        e = CobordismEngine()
        ids = list(e.states.keys())
        a = e.create_cobordism(ids[0], ids[1], "step1")
        b = e.create_cobordism(ids[1], ids[2], "step2")
        c = e.compose(a.id, b.id)
        assert c is not None
        assert c.process_name == "step1→step2"

    def test_evolution_graph(self):
        e = CobordismEngine()
        g = e.get_evolution_graph()
        assert "nodes" in g
        assert "edges" in g


# ───── DIMENSION XXXVII — Surreal ─────

class TestSurreal:
    def test_zero_one(self):
        z = zero()
        assert z.value == 0.0
        o = one()
        assert o.value == 1.0

    def test_omega(self):
        w = omega()
        assert w.value >= 99

    def test_epsilon(self):
        e = epsilon()
        assert 0 < e.value < 1

    def test_create(self):
        engine = SurrealEngine()
        s = engine.create([0.0], [2.0], "test")
        assert s.value == 1.0
        assert s.label == "test"

    def test_compare(self):
        engine = SurrealEngine()
        z = zero(); o = one()
        engine.numbers[z.id] = z
        engine.numbers[o.id] = o
        c = engine.compare(z.id, o.id)
        assert c["a_lt_b"]

    def test_game_analysis(self):
        engine = SurrealEngine()
        r = engine.game_analysis(1.0, 0.0)
        assert r["verdict"] == "CIEL en avant"

    def test_backward_induction(self):
        engine = SurrealEngine()
        tree = {
            "turn": "ciel",
            "children": [
                {"terminal": 3.0},
                {"terminal": 1.0},
            ],
        }
        r = engine.backward_induction(tree)
        assert r.value == 3.0

    def test_surreal_arithmetic(self):
        a = SurrealNumber([0.0], [], "a")   # = 1
        b = SurrealNumber([], [2.0], "b")   # = 1
        c = a + b
        assert c is not None


# ───── DIMENSION XXXVIII — Perfectoid ─────

class TestPerfectoid:
    def test_create_space(self):
        e = PerfectoidEngine()
        s = e.create_space("test_problem", 0, 1)
        assert s.name == "test_problem"
        assert s.characteristic == 0

    def test_perfectoidize(self):
        e = PerfectoidEngine()
        ids = list(e.spaces.keys())
        t = e.perfectoidize(ids[0], 3)
        assert "tower" in t
        assert len(t["tower"]) == 3

    def test_create_tilt(self):
        e = PerfectoidEngine()
        ids = list(e.spaces.keys())
        t = e.create_tilt(ids[0], ids[1], 0.85)
        assert t is not None
        assert t.fidelity == 0.85

    def test_solve_and_untilt(self):
        e = PerfectoidEngine()
        ids = list(e.spaces.keys())
        t = e.create_tilt(ids[0], ids[1], 0.9)
        ok = e.solve_in_tilt(t.id, {"result": 42.0})
        assert ok
        u = e.untilt(t.id)
        assert u is not None
        assert u["untilted_solution"]["result"] == 42.0 * 0.9

    def test_find_closest_tilt(self):
        e = PerfectoidEngine()
        results = e.find_closest_tilt("consciousness problem")
        assert len(results) >= 0


# ───── DIMENSION XXXIX — Trinity ─────

class TestTrinity:
    def test_create_proposition(self):
        e = TrinityEngine()
        p = e.create_proposition("forall x, P x", conclusion="P 0")
        assert p.name == "forall x, P x"
        assert p.conclusion == "P 0"

    def test_create_program(self):
        e = TrinityEngine()
        g = e.create_program("identity", "A → A", code="λx.x")
        assert g.name == "identity"
        assert g.type_signature == "A → A"

    def test_create_morphism(self):
        e = TrinityEngine()
        o1 = e.create_object("A")
        o2 = e.create_object("B")
        m = e.create_morphism("f", o1, o2)
        assert m.source_id == o1
        assert m.target_id == o2

    def test_link_triple(self):
        e = TrinityEngine()
        p = e.create_proposition("id", conclusion="A → A")
        g = e.create_program("id", "A → A", "λx.x")
        o1 = e.create_object("A"); o2 = e.create_object("B")
        m = e.create_morphism("id", o1, o2)
        t = e.link_triple(p.id, g.id, m.id)
        assert t is not None

    def test_extract_coq(self):
        e = TrinityEngine()
        p = e.create_proposition("test", conclusion="True")
        g = e.create_program("test", "True", "I")
        o1 = e.create_object("⊤"); o2 = e.create_object("⊤")
        m = e.create_morphism("triv", o1, o2)
        e.link_triple(p.id, g.id, m.id)
        coq = e.extract_coq(-1)
        assert coq is not None
        assert "Theorem" in coq


# ───── DIMENSION XL — MetaFoundation ─────

class TestMetaFoundation:
    def test_select_zfc_for_sets(self):
        e = MetaFoundationEngine()
        f = e.select_foundation("ensemble theory and cardinals")
        assert f is not None

    def test_select_hott_for_proof(self):
        e = MetaFoundationEngine()
        f = e.select_foundation("theorem proof with types")
        # HoTT or MLTT or CZF
        assert f in (Foundation.HOTT, Foundation.MLTT, Foundation.CZF)

    def test_list_available(self):
        e = MetaFoundationEngine()
        l = e.list_available()
        assert len(l) >= 9

    def test_create_custom(self):
        e = MetaFoundationEngine()
        cf = e.create_custom_foundation("CIEL-Foundation",
                                          axioms=["ax1", "ax2"])
        assert cf.name == "CIEL-Foundation"
        assert len(cf.axioms) == 2
        assert cf.is_active

    def test_independence_result(self):
        e = MetaFoundationEngine()
        r = e.independence_result("continuum hypothesis")
        assert "indépendant" in r["results"].get("Zermelo-Fraenkel + Choix", "")

    def test_compare_foundations(self):
        e = MetaFoundationEngine()
        c = e.compare_foundations("zfc", "hott")
        assert "metrics" in c
        assert "expressiveness_diff" in c["metrics"]
