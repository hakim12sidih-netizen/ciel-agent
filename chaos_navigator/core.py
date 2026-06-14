"""
CIEL v∞.8 — DIMENSION LVIII : CHAOS NAVIGATOR.
Navigation dans les systèmes chaotiques — attracteurs étranges,
exposants de Lyapunov, bord du chaos, bifurcations.

Concept : CIEL navigue délibérément au bord du chaos (Edge of Chaos)
où la créativité est maximale. Exposant de Lyapunov λ : λ > 0 = chaos,
λ < 0 = ordre, λ ≈ 0 = bord du chaos.
Diagramme de bifurcation, attracteur de Lorenz, section de Poincaré.
"""
from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class ChaoticSystem:
    id: str
    name: str
    lyapunov_exponent: float = 0.0
    dimension: int = 3
    entropy: float = 0.0
    edge_of_chaos: bool = False
    bifurcation_points: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "lambda": round(self.lyapunov_exponent, 4),
                "entropy": round(self.entropy, 4),
                "edge_of_chaos": self.edge_of_chaos,
                "bifurcations": len(self.bifurcation_points)}


@dataclass(slots=True)
class StrangeAttractor:
    id: str
    system_id: str
    type: str = "lorenz"  # lorenz | rossler | henon | logistic
    fractal_dim: float = 2.06
    orbit_points: list[list[float]] = field(default_factory=list)


class ChaosNavigatorEngine:
    """Moteur de navigation dans le chaos.

    Maintient des systèmes chaotiques, calcule les exposants de
    Lyapunov, détecte le bord du chaos, et propose des points
    de bifurcation pour maximiser la créativité.
    """

    def __init__(self):
        self.systems: dict[str, ChaoticSystem] = {}
        self.attractors: dict[str, StrangeAttractor] = {}
        self.network = LeaderNetwork()
        self._init_default()

    def _init_default(self):
        s = self.create_system("CIEL-Chaos", dimension=3,
                               lyapunov=0.02)
        s.edge_of_chaos = True
        s.bifurcation_points = [2.5, 3.0, 3.5, 3.8]
        s.entropy = 0.5
        a = self.create_attractor(s.id, "lorenz")
        a.fractal_dim = 2.06
        a.orbit_points = [[0.0, 1.0, 0.0],
                          [0.5, 0.8, 0.3],
                          [1.0, 0.5, 1.0]]

    def create_system(self, name: str, dimension: int = 3,
                      lyapunov: float = 0.0) -> ChaoticSystem:
        s = ChaoticSystem(
            id=f"CHA-{uuid.uuid4().hex[:12]}",
            name=name, lyapunov_exponent=lyapunov,
            dimension=dimension,
        )
        self.systems[s.id] = s
        return s

    def create_attractor(self, system_id: str,
                         atype: str = "lorenz") -> StrangeAttractor | None:
        if system_id not in self.systems:
            return None
        a = StrangeAttractor(
            id=f"ATR-{uuid.uuid4().hex[:12]}",
            system_id=system_id, type=atype,
        )
        self.attractors[a.id] = a
        return a

    def compute_lyapunov(self, system_id: str,
                         steps: int = 100) -> float:
        """Calcule l'exposant de Lyapunov λ.
        λ > 0 → chaos, λ < 0 → ordre, λ ≈ 0 → bord du chaos."""
        s = self.systems.get(system_id)
        if not s:
            return 0.0
        x = 0.5
        lyap = 0.0
        for _ in range(steps):
            x = 4.0 * x * (1.0 - x)  # logistic map
            if x > 0 and x < 1:
                lyap += math.log(abs(4.0 - 8.0 * x))
        lyap /= steps
        s.lyapunov_exponent = lyap
        s.edge_of_chaos = abs(lyap) < 0.1
        return lyap

    def bifurcation_diagram(self, r_min: float = 0.0,
                            r_max: float = 4.0,
                            steps: int = 100) -> list[dict]:
        """Simule un diagramme de bifurcation (logistic map)."""
        points = []
        for i in range(steps):
            r = r_min + (r_max - r_min) * i / steps
            x = 0.5
            for _ in range(50):
                x = r * x * (1.0 - x)
            # Échantillonner après convergence
            for _ in range(10):
                x = r * x * (1.0 - x)
                points.append({"r": round(r, 3), "x": round(x, 3)})
        return points

    def edge_of_chaos_optimize(self) -> dict:
        """Trouve le point optimal (bord du chaos) pour la créativité."""
        best = None
        best_dist = float("inf")
        for s in self.systems.values():
            dist = abs(s.lyapunov_exponent)
            if dist < best_dist:
                best_dist = dist
                best = s
        if best:
            return {
                "system": best.name,
                "lyapunov": round(best.lyapunov_exponent, 4),
                "entropy": round(best.entropy, 4),
                "edge_of_chaos": best.edge_of_chaos,
                "creativity_score": round(1.0 - best_dist, 3),
            }
        return {"error": "no systems"}

    def lorenz_simulate(self, sigma: float = 10.0,
                        rho: float = 28.0, beta: float = 8.0 / 3.0,
                        steps: int = 100) -> list[dict]:
        """Simule l'attracteur de Lorenz :
        dx/dt = σ(y-x), dy/dt = x(ρ-z)-y, dz/dt = xy-βz"""
        x, y, z = 1.0, 1.0, 1.0
        dt = 0.01
        orbit = []
        for _ in range(steps):
            dx = sigma * (y - x) * dt
            dy = (x * (rho - z) - y) * dt
            dz = (x * y - beta * z) * dt
            x += dx
            y += dy
            z += dz
            orbit.append({"x": round(x, 3), "y": round(y, 3),
                          "z": round(z, 3)})
        return orbit

    def poincare_section(self, system_id: str,
                         plane: str = "z=0") -> list[dict]:
        """Section de Poincaré — points de passage à travers un plan."""
        s = self.systems.get(system_id)
        if not s:
            return []
        a = next((a for a in self.attractors.values()
                  if a.system_id == system_id), None)
        if not a or not a.orbit_points:
            return []
        # Simuler les intersections
        points = []
        for i, pt in enumerate(a.orbit_points):
            if "z=0" in plane and pt[2] == 0.0:
                points.append({"point": pt, "index": i})
        return points[:10]

    def get_stats(self) -> dict:
        return {
            "systems": len(self.systems),
            "attractors": len(self.attractors),
            "chaotic_systems": sum(1 for s in self.systems.values()
                                   if s.lyapunov_exponent > 0.1),
            "edge_of_chaos": sum(1 for s in self.systems.values()
                                 if s.edge_of_chaos),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create_system":
            s = self.create_system(
                input_data.get("name", "?"),
                input_data.get("dimension", 3),
                input_data.get("lyapunov", 0.0),
            )
            return {"status": "ok", "system": s.to_dict()}
        elif action == "lyapunov":
            return {"status": "ok",
                    "lyapunov": self.compute_lyapunov(
                        input_data.get("system_id", ""),
                        input_data.get("steps", 100))}
        elif action == "bifurcation":
            return {"status": "ok",
                    "diagram": self.bifurcation_diagram(
                        input_data.get("r_min", 0.0),
                        input_data.get("r_max", 4.0),
                        input_data.get("steps", 50))}
        elif action == "edge":
            return {"status": "ok",
                    "optimum": self.edge_of_chaos_optimize()}
        elif action == "lorenz":
            return {"status": "ok",
                    "orbit": self.lorenz_simulate(
                        input_data.get("sigma", 10.0),
                        input_data.get("rho", 28.0),
                        input_data.get("beta", 8.0 / 3.0),
                        input_data.get("steps", 50))}
        return {"status": "ok", "systems": len(self.systems)}
