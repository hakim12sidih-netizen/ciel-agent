from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class Category:
    name: str
    objects: frozenset = field(default_factory=frozenset)
    morphisms: dict[tuple[Any, Any], list[Callable[[Any], Any]]] = field(default_factory=dict)

    def compose(self, f: Callable, g: Callable) -> Callable:
        return lambda x: f(g(x))

    def identity(self, obj: Any) -> Callable:
        return lambda x: x


@dataclass(slots=True)
class Functor:
    source: Category
    target: Category
    obj_map: Callable[[Any], Any] = field(default=lambda x: x)
    morph_map: Callable[[Callable], Callable] = field(default=lambda f: f)

    def apply_obj(self, obj: Any) -> Any:
        return self.obj_map(obj)

    def apply_morph(self, f: Callable[[Any], Any]) -> Callable:
        return self.morph_map(f)


@dataclass(slots=True)
class NaturalTransformation:
    source: Functor
    target: Functor
    components: dict[Any, Callable[[Any], Any]] = field(default_factory=dict)

    def component_at(self, obj: Any) -> Callable | None:
        return self.components.get(obj)


class Simplex:
    """Simplexe pour homologie persistante."""

    def __init__(self, vertices: tuple[int, ...], dim: int = 0):
        self.vertices = tuple(sorted(vertices))
        self.dim = len(self.vertices) - 1

    def __hash__(self) -> int:
        return hash(self.vertices)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Simplex) and self.vertices == other.vertices

    def __repr__(self) -> str:
        return f"[{','.join(str(v) for v in self.vertices)}]"


class SimplicialComplex:
    """Complexe simplicial — triangles, arêtes, sommets, homologie."""

    def __init__(self):
        self.simplices: dict[int, set[Simplex]] = {}

    def add_simplex(self, vertices: tuple[int, ...]) -> Simplex:
        if len(vertices) == 0:
            return Simplex(())
        s = Simplex(vertices)
        dim = s.dim
        if dim not in self.simplices:
            self.simplices[dim] = set()
        self.simplices[dim].add(s)
        for i in range(len(vertices)):
            sub = vertices[:i] + vertices[i + 1:]
            self.add_simplex(sub)
        return s

    def betti(self, dim: int = 0) -> int:
        if dim not in self.simplices:
            return 0
        if dim == 0:
            return len(self.simplices.get(0, set()))
        faces = self.simplices.get(dim, set())
        boundaries = self.simplices.get(dim - 1, set())
        n_faces = len(faces)
        n_bound = len(boundaries)
        return max(0, n_faces - n_bound)

    def betti_numbers(self, max_dim: int = 3) -> dict[int, int]:
        return {d: self.betti(d) for d in range(max_dim + 1)}

    def euler_characteristic(self) -> int:
        total = 0
        for dim, simplices in self.simplices.items():
            total += (-1) ** dim * len(simplices)
        return total


class PersistentHomology:
    """Homologie persistante — Vietoris-Rips simplifié."""

    def __init__(self, points: list[list[float]]):
        self.points = np.array(points)
        self.n = len(points)
        self._distances: dict[tuple[int, int], float] = {}

    def _dist(self, i: int, j: int) -> float:
        key = (min(i, j), max(i, j))
        if key not in self._distances:
            self._distances[key] = np.linalg.norm(self.points[i] - self.points[j])
        return self._distances[key]

    def vietoris_rips(self, threshold: float) -> SimplicialComplex:
        sc = SimplicialComplex()
        for i in range(self.n):
            sc.add_simplex((i,))
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if self._dist(i, j) <= threshold:
                    sc.add_simplex((i, j))
                    for k in range(j + 1, self.n):
                        if self._dist(i, k) <= threshold and self._dist(j, k) <= threshold:
                            sc.add_simplex((i, j, k))
        return sc

    def persistence_diagram(self, max_threshold: float = 1.0, steps: int = 10) -> dict[int, list[tuple[float, float]]]:
        diagrams: dict[int, list[tuple[float, float]]] = {0: [], 1: []}
        prev_betti: dict[int, int] = {0: 0, 1: 0}
        prev_thresh = 0.0
        for step in range(1, steps + 1):
            thresh = max_threshold * step / steps
            sc = self.vietoris_rips(thresh)
            curr_betti = sc.betti_numbers(max_dim=2)
            for dim in (0, 1):
                b = curr_betti.get(dim, 0)
                pb = prev_betti.get(dim, 0)
                if b > pb:
                    diagrams[dim].append((thresh, float("inf")))
                elif b < pb:
                    if diagrams[dim]:
                        last = diagrams[dim][-1]
                        if last[1] == float("inf"):
                            diagrams[dim][-1] = (last[0], thresh)
            prev_betti = curr_betti
            prev_thresh = thresh
        return diagrams


class CliffordAlgebra:
    """Algèbre géométrique Cl(3,0) — multivecteurs 3D."""

    def __init__(self, grade: int = 0, scalar: float = 0.0,
                 vector: np.ndarray | None = None,
                 bivector: np.ndarray | None = None,
                 trivector: float = 0.0):
        self.grade = grade
        self.scalar = scalar
        self.vector = vector if vector is not None else np.zeros(3)
        self.bivector = bivector if bivector is not None else np.zeros(3)
        self.trivector = trivector

    @staticmethod
    def e1() -> CliffordAlgebra:
        return CliffordAlgebra(grade=1, vector=np.array([1.0, 0.0, 0.0]))

    @staticmethod
    def e2() -> CliffordAlgebra:
        return CliffordAlgebra(grade=1, vector=np.array([0.0, 1.0, 0.0]))

    @staticmethod
    def e3() -> CliffordAlgebra:
        return CliffordAlgebra(grade=1, vector=np.array([0.0, 0.0, 1.0]))

    @staticmethod
    def scalar_val(s: float) -> CliffordAlgebra:
        return CliffordAlgebra(grade=0, scalar=s)

    def geometric_product(self, other: CliffordAlgebra) -> CliffordAlgebra:
        a = self
        b = other
        s = a.scalar * b.scalar + np.dot(a.vector, b.vector) - np.dot(a.bivector, b.bivector) - a.trivector * b.trivector
        v = a.scalar * b.vector + b.scalar * a.vector + np.cross(a.vector, b.bivector) + np.cross(a.bivector, b.vector) - a.trivector * np.cross(b.bivector, np.array([1., 0., 0.]))  # noqa: E501
        return CliffordAlgebra(scalar=s, vector=v)

    def norm(self) -> float:
        return math.sqrt(self.scalar ** 2 + np.sum(self.vector ** 2) + np.sum(self.bivector ** 2) + self.trivector ** 2)

    def rotor(self, angle: float, axis: np.ndarray) -> CliffordAlgebra:
        axis = axis / np.linalg.norm(axis)
        half = angle / 2
        b = axis * math.sin(half)
        return CliffordAlgebra(scalar=math.cos(half), bivector=b)


class OptimalTransport:
    """Transport optimal — Wasserstein, Sinkhorn."""

    def __init__(self):
        self._cost_matrix: np.ndarray | None = None

    def wasserstein_1d(self, a: list[float], b: list[float]) -> float:
        sa = sorted(a)
        sb = sorted(b)
        return sum(abs(x - y) for x, y in zip(sa, sb)) / len(sa)

    def sinkhorn(self, a: np.ndarray, b: np.ndarray, M: np.ndarray,
                 reg: float = 0.1, max_iter: int = 100) -> np.ndarray:
        n, m = M.shape
        K = np.exp(-M / reg)
        K[np.isinf(K)] = 1e10
        K[np.isnan(K)] = 0.0
        v = np.ones(m)
        for _ in range(max_iter):
            u = a / (K @ v)
            v = b / (K.T @ u)
        P = np.diag(u) @ K @ np.diag(v)
        return P

    def wasserstein_2d(self, a: np.ndarray, b: np.ndarray, reg: float = 0.1) -> float:
        n = len(a)
        m = len(b)
        M = np.zeros((n, m))
        for i in range(n):
            for j in range(m):
                M[i, j] = np.linalg.norm(a[i] - b[j])
        P = self.sinkhorn(np.ones(n) / n, np.ones(m) / m, M, reg)
        return float(np.sum(P * M))


class FisherMetric:
    """Métrique de Fisher-Rao — géométrie de l'information."""

    @staticmethod
    def metric_tensor(theta: np.ndarray, score_func: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
        eps = 1e-8
        n = len(theta)
        F = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dt_i = np.zeros(n)
                dt_j = np.zeros(n)
                dt_i[i] = eps
                dt_j[j] = eps
                s_plus_i = score_func(theta + dt_i)
                s_minus_i = score_func(theta - dt_i)
                s_plus_j = score_func(theta + dt_j)
                s_minus_j = score_func(theta - dt_j)
                di = (s_plus_i - s_minus_i) / (2 * eps)
                dj = (s_plus_j - s_minus_j) / (2 * eps)
                F[i, j] = np.mean(di * dj)
        return F

    @staticmethod
    def geodesic_distance(theta1: np.ndarray, theta2: np.ndarray,
                          score_func: Callable[[np.ndarray], np.ndarray]) -> float:
        t = np.linspace(0, 1, 50)
        total = 0.0
        for i in range(1, len(t)):
            tau = theta1 + t[i] * (theta2 - theta1)
            dtau = theta2 - theta1
            F = FisherMetric.metric_tensor(tau, score_func)
            ds = math.sqrt(max(0, dtau @ F @ dtau)) / len(t)
            total += ds
        return total


class HoTT:
    """Homotopy Type Theory — types comme espaces topologiques."""

    def __init__(self):
        self._identity_types: dict[tuple[int, int], list[list[int]]] = {}
        self._paths: dict[tuple[int, int], list[list[int]]] = {}

    def identity_type(self, a: int, b: int) -> list[list[int]]:
        key = (a, b)
        if key not in self._identity_types:
            paths = [[a, b]]
            if a == b:
                paths.append([a])
            self._identity_types[key] = paths
        return self._identity_types[key]

    def is_univalent(self, f: Callable[[int], int], g: Callable[[int], int], domain: range) -> bool:
        for x in domain:
            for y in domain:
                if f(x) == f(y) and x != y:
                    continue
                if f(x) == g(x):
                    continue
                return False
        return True

    def transport(self, path: list[int], x: int) -> int:
        if not path:
            return x
        return path[-1]

    def loop_space(self, base: int, dim: int = 1) -> list[list[int]]:
        loops: list[list[int]] = []
        if dim >= 1:
            loops.append([base, base])
        return loops


class MathEngine:
    """Point d'entrée principal — MATH : mathématiques des profondeurs."""

    def __init__(self):
        self._categories: dict[str, Category] = {}
        self._complexes: list[SimplicialComplex] = []
        self._transport_count = 0

    def category(self, name: str, objs: frozenset | None = None) -> Category:
        cat = Category(name=name, objects=objs or frozenset())
        self._categories[name] = cat
        return cat

    def functor(self, source: str, target: str,
                obj_map: Callable[[Any], Any],
                morph_map: Callable[[Callable], Callable]) -> Functor:
        src = self._categories.get(source, Category(source))
        tgt = self._categories.get(target, Category(target))
        return Functor(source=src, target=tgt, obj_map=obj_map, morph_map=morph_map)

    def betti(self, points: list[list[float]], threshold: float = 0.5) -> dict[int, int]:
        ph = PersistentHomology(points)
        sc = ph.vietoris_rips(threshold)
        self._complexes.append(sc)
        return sc.betti_numbers()

    def persistence(self, points: list[list[float]], max_threshold: float = 1.0, steps: int = 10) -> dict[int, list[tuple[float, float]]]:
        ph = PersistentHomology(points)
        return ph.persistence_diagram(max_threshold, steps)

    def clifford_mul(self, a: CliffordAlgebra, b: CliffordAlgebra) -> CliffordAlgebra:
        return a.geometric_product(b)

    def clifford_rotor(self, angle: float, axis: list[float]) -> CliffordAlgebra:
        return CliffordAlgebra().rotor(angle, np.array(axis))

    def wasserstein(self, a: list[float], b: list[float]) -> float:
        self._transport_count += 1
        return OptimalTransport().wasserstein_1d(a, b)

    def sinkhorn(self, a: list[float], b: list[float], cost: list[list[float]]) -> float:
        self._transport_count += 1
        ot = OptimalTransport()
        P = ot.sinkhorn(np.array(a), np.array(b), np.array(cost))
        return float(np.sum(P * np.array(cost)))

    def fisher_metric(self, theta: list[float], score_func: Callable | None = None) -> np.ndarray:
        sf = score_func or (lambda t: np.array([math.sin(ti) for ti in t]))
        return FisherMetric.metric_tensor(np.array(theta), sf)

    def hott_identity(self, a: int, b: int) -> list[list[int]]:
        return HoTT().identity_type(a, b)

    def get_stats(self) -> dict[str, Any]:
        return {
            "categories": len(self._categories),
            "simplicial_complexes": len(self._complexes),
            "transport_computations": self._transport_count,
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "category":
            cat = self.category(str(data.get("name", "C")))
            return {"success": True, "action": "category", "name": cat.name}

        elif action == "betti":
            points = data.get("points", [[0.0, 0.0], [0.0, 1.0]])
            threshold = float(data.get("threshold", 0.5))
            betti = self.betti(points, threshold)
            return {"success": True, "action": "betti", "betti_numbers": betti}

        elif action == "persistence":
            points = data.get("points", [[0.0, 0.0], [1.0, 0.0]])
            diagram = self.persistence(points, float(data.get("max_threshold", 1.0)))
            return {"success": True, "action": "persistence", "diagram": diagram}

        elif action == "clifford_mul":
            a = CliffordAlgebra(scalar=float(data.get("a_scalar", 1.0)))
            b = CliffordAlgebra(scalar=float(data.get("b_scalar", 1.0)))
            c = self.clifford_mul(a, b)
            return {"success": True, "action": "clifford_mul", "scalar": c.scalar}

        elif action == "wasserstein":
            a = data.get("a", [0.0, 1.0])
            b = data.get("b", [0.5, 1.5])
            dist = self.wasserstein(a, b)
            return {"success": True, "action": "wasserstein", "distance": dist}

        elif action == "sinkhorn":
            a = data.get("a", [0.5, 0.5])
            b = data.get("b", [0.5, 0.5])
            cost = data.get("cost", [[0.0, 1.0], [1.0, 0.0]])
            cost_val = self.sinkhorn(a, b, cost)
            return {"success": True, "action": "sinkhorn", "cost": cost_val}

        elif action == "fisher":
            theta = data.get("theta", [0.5, 0.5])
            F = self.fisher_metric(theta)
            return {"success": True, "action": "fisher", "metric": F.tolist()}

        elif action == "hott":
            a = int(data.get("a", 0))
            b = int(data.get("b", 1))
            paths = self.hott_identity(a, b)
            return {"success": True, "action": "hott", "paths": paths}

        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
