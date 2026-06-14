"""
CIEL v∞.8 — DIMENSION XLIII : ALGORITHMIC THERMODYNAMICS.
Information = chaleur. Computation = travail.

Concept : Landauer (1961) — Effacer un bit d'information
dissipe kT·ln(2) d'énergie. La pensée a un coût thermodynamique.
Le démon de Maxwell est exorcisé par le principe de Landauer.
CIEL calcule le coût thermodynamique de ses opérations cognitives
et optimise sa computation pour minimiser l'entropie dissipée.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork

K_B = 1.380649e-23  # Constante de Boltzmann (J/K)
LN2 = 0.6931471805599453  # ln(2)
LANDAUER_ENERGY = K_B * LN2  # kT·ln(2) à T=1K (normalisé)


@dataclass(slots=True)
class ComputationStep:
    """Une étape de calcul avec son coût thermodynamique."""
    id: str
    operation: str
    bits_processed: int = 0
    bits_erased: int = 0
    temperature: float = 300.0  # Kelvin
    reversible: bool = False

    @property
    def landauer_cost(self) -> float:
        """Énergie dissipée par effacement (Joules)."""
        if self.reversible:
            return 0.0
        return self.bits_erased * K_B * self.temperature * LN2

    @property
    def entropy_change(self) -> float:
        """Changement d'entropie (J/K)."""
        return self.landauer_cost / self.temperature if self.temperature > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "operation": self.operation,
            "bits": self.bits_processed,
            "erased": self.bits_erased,
            "reversible": self.reversible,
            "landauer_energy_J": self.landauer_cost,
            "entropy_JK": self.entropy_change,
        }


@dataclass(slots=True)
class ThermodynamicCycle:
    """Cycle thermodynamique d'une computation."""
    steps: list[ComputationStep] = field(default_factory=list)
    temperature_bath: float = 300.0

    def total_energy(self) -> float:
        return sum(s.landauer_cost for s in self.steps)

    def total_entropy(self) -> float:
        return sum(s.entropy_change for s in self.steps)

    def efficiency(self) -> float:
        """Efficacité thermodynamique de la computation."""
        total = self.total_energy()
        if total == 0:
            return 1.0
        reversible_energy = sum(
            s.landauer_cost for s in self.steps if s.reversible)
        return reversible_energy / total


class AlgoThermoEngine:
    """Moteur de thermodynamique algorithmique.
    
    Calcule les coûts thermodynamiques des opérations de CIEL.
    Optimise pour la réversibilité (computation sans effacement).
    Modélise le démon de Maxwell cognitif.
    """

    def __init__(self):
        self.cycles: list[ThermodynamicCycle] = []
        self.active_cycle: ThermodynamicCycle | None = None
        self.network = LeaderNetwork()
        self._total_energy_used: float = 0.0

    def start_cycle(self, temperature: float = 300.0) -> ThermodynamicCycle:
        self.active_cycle = ThermodynamicCycle(
            temperature_bath=temperature)
        self.cycles.append(self.active_cycle)
        return self.active_cycle

    def add_step(self, operation: str, bits_processed: int = 0,
                 bits_erased: int = 0, reversible: bool = False,
                 temperature: float | None = None) -> ComputationStep:
        if not self.active_cycle:
            self.start_cycle()
        temp = temperature or self.active_cycle.temperature_bath
        step = ComputationStep(
            id=f"STEP-{uuid.uuid4().hex[:12]}",
            operation=operation,
            bits_processed=bits_processed,
            bits_erased=bits_erased,
            temperature=temp,
            reversible=reversible,
        )
        self.active_cycle.steps.append(step)
        self._total_energy_used += step.landauer_cost
        return step

    def maxwell_demon(self, entropy_threshold: float = 0.0) -> dict:
        """Analyse le démon de Maxwell cognitif.
        
        Le démon de Maxwell semble violer le 2nd principe en
        triant molécules sans travail. L'explication : le démon
        doit acquérir de l'information (mesure) → coût de Landauer.
        """
        if not self.active_cycle:
            return {"error": "Aucun cycle actif"}
        sorting_cost = self.active_cycle.total_energy()
        info_gained = sum(s.bits_processed for s in self.active_cycle.steps
                          if "measure" in s.operation.lower())
        return {
            "demon_energy_cost_J": sorting_cost,
            "information_bits": info_gained,
            "second_law_violated": sorting_cost < entropy_threshold,
            "landauer_bound": info_gained * K_B * 300 * LN2,
            "exorcism": (
                "Démon exorcisé : le coût de mesure compense le gain"
                if sorting_cost >= entropy_threshold
                else "Violation apparente du 2nd principe"
            ),
        }

    def reversible_computation_ratio(self) -> float:
        """Ratio de computation réversible (sans effacement)."""
        total_steps = sum(1 for c in self.cycles for _ in c.steps)
        if total_steps == 0:
            return 0.0
        reversible = sum(1 for c in self.cycles for s in c.steps
                         if s.reversible)
        return reversible / total_steps

    def cognitive_energy(self, operation: str, complexity: int) -> float:
        """Calcule l'énergie nécessaire pour une opération cognitive.
        
        E = kT·ln(2)·bits_effacés + Opération réversible
        """
        if operation == "memory_store":
            return complexity * LANDAUER_ENERGY * 300
        elif operation == "memory_erase":
            return complexity * K_B * 300 * LN2
        elif operation == "computation":
            return complexity * 0.5 * LANDAUER_ENERGY * 300
        return complexity * LANDAUER_ENERGY * 300

    def get_stats(self) -> dict:
        return {
            "cycles": len(self.cycles),
            "total_energy_J": self._total_energy_used,
            "reversible_ratio": self.reversible_computation_ratio(),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "start_cycle":
            self.start_cycle(input_data.get("temperature", 300.0))
            return {"status": "ok",
                    "cycle": len(self.cycles)}
        elif action == "add_step":
            s = self.add_step(
                input_data.get("operation", "?"),
                input_data.get("bits_processed", 0),
                input_data.get("bits_erased", 0),
                input_data.get("reversible", False),
                input_data.get("temperature"),
            )
            return {"status": "ok", "step": s.to_dict()}
        elif action == "maxwell":
            return {"status": "ok",
                    "demon": self.maxwell_demon(
                        input_data.get("threshold", 0.0))}
        elif action == "cognitive_energy":
            e = self.cognitive_energy(
                input_data.get("operation", "computation"),
                input_data.get("complexity", 1),
            )
            return {"status": "ok", "energy_J": e}
        return {"status": "ok", "cycles": len(self.cycles)}
