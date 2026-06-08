from __future__ import annotations

import math

import numpy as np
import pytest
from ciel.math.core import (
    Category, Functor, NaturalTransformation,
    Simplex, SimplicialComplex, PersistentHomology,
    CliffordAlgebra, OptimalTransport, FisherMetric, HoTT,
    MathEngine,
)


class TestCategory:
    def test_create(self):
        c = Category(name="Set", objects=frozenset({1, 2, 3}))
        assert c.name == "Set"
        assert len(c.objects) == 3

    def test_identity(self):
        c = Category("C")
        ident = c.identity(42)
        assert ident(42) == 42

    def test_compose(self):
        c = Category("C")
        f = lambda x: x * 2
        g = lambda x: x + 1
        h = c.compose(f, g)
        assert h(5) == 12


class TestFunctor:
    def test_create(self):
        c = Category("C")
        d = Category("D")
        f = Functor(source=c, target=d)
        assert f.source.name == "C"
        assert f.target.name == "D"

    def test_apply(self):
        c = Category("C")
        d = Category("D")
        f = Functor(source=c, target=d, obj_map=lambda x: x + 1)
        assert f.apply_obj(5) == 6


class TestNaturalTransformation:
    def test_create(self):
        c = Category("C")
        d = Category("D")
        F = Functor(c, d)
        G = Functor(c, d)
        nt = NaturalTransformation(source=F, target=G)
        assert nt.component_at(1) is None


class TestSimplex:
    def test_create(self):
        s = Simplex((0, 1, 2))
        assert s.dim == 2
        assert s.vertices == (0, 1, 2)

    def test_hash_eq(self):
        a = Simplex((0, 1))
        b = Simplex((1, 0))
        assert a == b
        assert hash(a) == hash(b)

    def test_repr(self):
        s = Simplex((0, 1))
        assert repr(s) == "[0,1]"


class TestSimplicialComplex:
    def test_add_simplex(self):
        sc = SimplicialComplex()
        s = sc.add_simplex((0, 1, 2))
        assert s.dim == 2
        assert 0 in sc.simplices
        assert 1 in sc.simplices

    def test_betti_0(self):
        sc = SimplicialComplex()
        sc.add_simplex((0,))
        sc.add_simplex((1,))
        assert sc.betti(0) == 2

    def test_betti_numbers(self):
        sc = SimplicialComplex()
        sc.add_simplex((0, 1, 2))
        b = sc.betti_numbers()
        assert 0 in b
        assert 1 in b

    def test_euler(self):
        sc = SimplicialComplex()
        sc.add_simplex((0,))
        sc.add_simplex((1,))
        sc.add_simplex((0, 1))
        assert sc.euler_characteristic() == 1


class TestPersistentHomology:
    def test_create(self):
        ph = PersistentHomology([[0.0, 0.0], [0.0, 1.0]])
        assert ph.n == 2

    def test_vietoris_rips(self):
        ph = PersistentHomology([[0.0, 0.0], [1.0, 0.0]])
        sc = ph.vietoris_rips(1.5)
        assert sc.betti(0) <= 2

    def test_persistence_diagram(self):
        points = [[0.0, 0.0], [1.0, 0.0], [0.5, 0.5]]
        ph = PersistentHomology(points)
        diag = ph.persistence_diagram(max_threshold=1.0, steps=5)
        assert 0 in diag
        assert 1 in diag


class TestCliffordAlgebra:
    def test_scalar(self):
        s = CliffordAlgebra.scalar_val(3.0)
        assert s.scalar == 3.0
        assert s.grade == 0

    def test_e1(self):
        e1 = CliffordAlgebra.e1()
        assert e1.vector[0] == 1.0

    def test_geometric_product(self):
        a = CliffordAlgebra(scalar=2.0)
        b = CliffordAlgebra(scalar=3.0)
        c = a.geometric_product(b)
        assert c.scalar == 6.0

    def test_norm(self):
        a = CliffordAlgebra(scalar=3.0)
        assert a.norm() == 3.0

    def test_rotor(self):
        r = CliffordAlgebra().rotor(math.pi / 2, np.array([0.0, 0.0, 1.0]))
        assert abs(r.scalar) > 0


class TestOptimalTransport:
    def test_wasserstein_1d(self):
        ot = OptimalTransport()
        d = ot.wasserstein_1d([0.0, 1.0], [0.5, 1.5])
        assert d > 0

    def test_wasserstein_1d_identical(self):
        ot = OptimalTransport()
        d = ot.wasserstein_1d([1.0, 2.0], [1.0, 2.0])
        assert d == 0.0

    def test_sinkhorn(self):
        ot = OptimalTransport()
        a = np.array([0.5, 0.5])
        b = np.array([0.5, 0.5])
        M = np.array([[0.0, 1.0], [1.0, 0.0]])
        P = ot.sinkhorn(a, b, M, reg=0.5)
        assert P.shape == (2, 2)
        assert np.allclose(P.sum(), 1.0, atol=1e-2)

    def test_wasserstein_2d(self):
        ot = OptimalTransport()
        a = np.array([[0.0, 0.0], [1.0, 0.0]])
        b = np.array([[0.0, 0.0], [0.0, 1.0]])
        d = ot.wasserstein_2d(a, b, reg=0.5)
        assert d > 0


class TestFisherMetric:
    def test_metric_tensor(self):
        theta = np.array([0.5, 0.5])
        F = FisherMetric.metric_tensor(theta, lambda t: np.array([math.sin(ti) for ti in t]))
        assert F.shape == (2, 2)
        assert np.all(F >= 0)

    def test_geodesic_distance(self):
        d = FisherMetric.geodesic_distance(
            np.array([0.1, 0.1]),
            np.array([0.5, 0.5]),
            lambda t: np.array([math.sin(ti) for ti in t]),
        )
        assert d >= 0


class TestHoTT:
    def test_identity_type(self):
        h = HoTT()
        paths = h.identity_type(0, 1)
        assert len(paths) >= 1

    def test_identity_type_same(self):
        h = HoTT()
        paths = h.identity_type(1, 1)
        assert len(paths) >= 2

    def test_loop_space(self):
        h = HoTT()
        loops = h.loop_space(0)
        assert len(loops) == 1

    def test_transport(self):
        h = HoTT()
        assert h.transport([0, 1, 2], 5) == 2


class TestMathEngine:
    def test_create(self):
        e = MathEngine()
        assert e._categories == {}

    def test_category(self):
        e = MathEngine()
        c = e.category("Test")
        assert c.name == "Test"

    def test_betti(self):
        e = MathEngine()
        betti = e.betti([[0.0, 0.0], [1.0, 0.0]], threshold=1.5)
        assert 0 in betti

    def test_persistence(self):
        e = MathEngine()
        diag = e.persistence([[0.0, 0.0], [0.0, 1.0], [0.5, 0.5]])
        assert 0 in diag

    def test_clifford_mul(self):
        e = MathEngine()
        a = CliffordAlgebra(scalar=2.0)
        b = CliffordAlgebra(scalar=3.0)
        c = e.clifford_mul(a, b)
        assert c.scalar == 6.0

    def test_clifford_rotor(self):
        e = MathEngine()
        r = e.clifford_rotor(math.pi / 2, [0.0, 0.0, 1.0])
        assert abs(r.scalar) > 0

    def test_wasserstein(self):
        e = MathEngine()
        d = e.wasserstein([0.0, 1.0], [0.5, 1.5])
        assert d > 0

    def test_sinkhorn(self):
        e = MathEngine()
        cost = e.sinkhorn([0.5, 0.5], [0.5, 0.5], [[0.0, 1.0], [1.0, 0.0]])
        assert cost > 0

    def test_fisher_metric(self):
        e = MathEngine()
        F = e.fisher_metric([0.5, 0.5])
        assert F.shape == (2, 2)

    def test_hott_identity(self):
        e = MathEngine()
        paths = e.hott_identity(0, 1)
        assert len(paths) >= 1

    def test_get_stats(self):
        e = MathEngine()
        stats = e.get_stats()
        assert "categories" in stats
        assert "simplicial_complexes" in stats
        assert stats["categories"] == 0

    def test_process_category(self):
        e = MathEngine()
        r = e.process({"action": "category", "name": "C"})
        assert r["success"] is True
        assert r["name"] == "C"

    def test_process_betti(self):
        e = MathEngine()
        r = e.process({"action": "betti", "points": [[0, 0], [0, 1]], "threshold": 1.5})
        assert r["success"] is True
        assert "betti_numbers" in r

    def test_process_persistence(self):
        e = MathEngine()
        r = e.process({"action": "persistence", "points": [[0, 0], [1, 0]]})
        assert r["success"] is True
        assert "diagram" in r

    def test_process_clifford_mul(self):
        e = MathEngine()
        r = e.process({"action": "clifford_mul", "a_scalar": 2.0, "b_scalar": 3.0})
        assert r["success"] is True
        assert r["scalar"] == 6.0

    def test_process_wasserstein(self):
        e = MathEngine()
        r = e.process({"action": "wasserstein", "a": [0, 1], "b": [0.5, 1.5]})
        assert r["success"] is True
        assert "distance" in r

    def test_process_sinkhorn(self):
        e = MathEngine()
        r = e.process({
            "action": "sinkhorn",
            "a": [0.5, 0.5], "b": [0.5, 0.5],
            "cost": [[0.0, 1.0], [1.0, 0.0]],
        })
        assert r["success"] is True
        assert "cost" in r

    def test_process_fisher(self):
        e = MathEngine()
        r = e.process({"action": "fisher", "theta": [0.5, 0.5]})
        assert r["success"] is True
        assert "metric" in r

    def test_process_hott(self):
        e = MathEngine()
        r = e.process({"action": "hott", "a": 0, "b": 1})
        assert r["success"] is True
        assert "paths" in r

    def test_process_stats(self):
        e = MathEngine()
        r = e.process({"action": "stats"})
        assert r["success"] is True

    def test_process_bad_action(self):
        e = MathEngine()
        r = e.process({"action": "nonexistent"})
        assert r["success"] is False

    def test_process_bad_input(self):
        e = MathEngine()
        r = e.process("bad")
        assert r["success"] is False
