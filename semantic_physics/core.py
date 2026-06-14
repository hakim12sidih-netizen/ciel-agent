"""
CIEL v∞.8 — DIMENSION LV : SEMANTIC PHYSICS.
Lois physiques émergentes de la structure sémantique.

Concept : L'espace sémantique est un espace-temps courbe où les
concepts sont des particules, les relations sont des forces, et
les significations suivent des géodésiques. Tenseur sémantique
G_μν = 8πG·T_μν (équation d'Einstein sémantique).
Conservation du sens : ∂_μ J^μ = 0.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class SemanticField:
    id: str
    name: str
    field_type: str = "scalaire"  # scalaire | vectoriel | tenseur
    intensity: float = 0.0
    curvature: float = 0.0
    coordinates: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "type": self.field_type, "intensity": self.intensity,
                "curvature": self.curvature}


@dataclass(slots=True)
class SemanticParticle:
    id: str
    concept: str
    mass: float = 1.0
    charge: float = 0.0
    spin: float = 0.5
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    momentum: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])

    def kinetic_energy(self) -> float:
        return 0.5 * self.mass * sum(p**2 for p in self.momentum)

    def to_dict(self) -> dict:
        return {"id": self.id, "concept": self.concept,
                "mass": self.mass, "charge": self.charge,
                "position": [self.x, self.y, self.z],
                "momentum": self.momentum}


class SemanticPhysicsEngine:
    """Moteur de physique sémantique.

    Les concepts sont des particules dans un espace-temps sémantique.
    Les forces sont des gradients du champ sémantique.
    """

    def __init__(self):
        self.fields: dict[str, SemanticField] = {}
        self.particles: dict[str, SemanticParticle] = {}
        self.network = LeaderNetwork()
        self._init_defaults()

    def _init_defaults(self):
        self.fields["sens"] = SemanticField(
            id="SENS-01", name="Champ de Sens",
            field_type="tenseur", intensity=1.0, curvature=0.0,
        )

    def create_field(self, name: str, field_type: str = "scalaire",
                     intensity: float = 0.0) -> SemanticField:
        f = SemanticField(
            id=f"FLD-{uuid.uuid4().hex[:12]}",
            name=name, field_type=field_type, intensity=intensity,
            curvature=0.0,
        )
        self.fields[f.id] = f
        return f

    def create_particle(self, concept: str, mass: float = 1.0,
                        charge: float = 0.0) -> SemanticParticle:
        p = SemanticParticle(
            id=f"PAR-{uuid.uuid4().hex[:12]}",
            concept=concept, mass=mass, charge=charge,
        )
        self.particles[p.id] = p
        return p

    def compute_geodesic(self, particle_id: str,
                         steps: int = 10) -> list[dict]:
        """Calcule la géodésique d'une particule dans l'espace sémantique."""
        p = self.particles.get(particle_id)
        if not p:
            return []
        path = []
        for _ in range(steps):
            total_force = [0.0, 0.0, 0.0]
            for f in self.fields.values():
                grad = f.intensity * 0.1
                total_force[0] += grad * (p.x + 1.0)
                total_force[1] += grad * (p.y + 1.0)
                total_force[2] += grad * (p.z + 1.0)
            for i in range(3):
                p.momentum[i] += total_force[i] / max(p.mass, 0.01)
            p.x += p.momentum[0] * 0.1
            p.y += p.momentum[1] * 0.1
            p.z += p.momentum[2] * 0.1
            path.append({"x": round(p.x, 3), "y": round(p.y, 3),
                         "z": round(p.z, 3)})
        return path

    def semantic_energy(self) -> dict:
        total = 0.0
        for p in self.particles.values():
            total += p.kinetic_energy()
        for f in self.fields.values():
            total += 0.5 * f.intensity**2
        return {"total_energy": round(total, 3),
                "n_particles": len(self.particles),
                "n_fields": len(self.fields)}

    def conservation_laws(self) -> dict:
        """Vérifie les lois de conservation sémantique."""
        total_momentum = [0.0, 0.0, 0.0]
        total_charge = 0.0
        for p in self.particles.values():
            for i in range(min(len(p.momentum), 3)):
                total_momentum[i] += p.momentum[i]
            total_charge += p.charge
        return {
            "momentum_conserved": all(abs(m) < 0.01
                                      for m in total_momentum),
            "total_momentum": [round(m, 4) for m in total_momentum],
            "charge_conserved": abs(total_charge) < 0.01,
            "total_charge": total_charge,
        }

    def compute_ricci_curvature(self) -> float:
        """Courbure de Ricci de l'espace sémantique."""
        total = 0.0
        for f in self.fields.values():
            total += f.intensity * f.curvature
        return round(total, 4)

    def get_stats(self) -> dict:
        return {
            "particles": len(self.particles),
            "fields": len(self.fields),
            "energy": self.semantic_energy(),
            "ricci_curvature": self.compute_ricci_curvature(),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create_field":
            f = self.create_field(
                input_data.get("name", "?"),
                input_data.get("field_type", "scalaire"),
                input_data.get("intensity", 0.0),
            )
            return {"status": "ok", "field": f.to_dict()}
        elif action == "create_particle":
            p = self.create_particle(
                input_data.get("concept", "?"),
                input_data.get("mass", 1.0),
                input_data.get("charge", 0.0),
            )
            return {"status": "ok", "particle": p.to_dict()}
        elif action == "geodesic":
            return {"status": "ok",
                    "path": self.compute_geodesic(
                        input_data.get("particle_id", ""),
                        input_data.get("steps", 10))}
        elif action == "conservation":
            return {"status": "ok",
                    "laws": self.conservation_laws()}
        return {"status": "ok", "particles": len(self.particles)}
