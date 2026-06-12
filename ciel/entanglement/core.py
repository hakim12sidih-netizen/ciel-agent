"""
CIEL v∞.8 — DIMENSION LVI : ENTANGLEMENT.
Intrication cognitive — corrélations non-locales entre concepts.

Concept : Deux concepts peuvent être intriqués, de sorte que
l'observation de l'un affecte instantanément l'état de l'autre,
indépendamment de la distance sémantique. Inégalités de Bell
cognitives : ⟨AB⟩ + ⟨AC⟩ + ⟨BC⟩ ≤ 1 (limite classique).
Non-localité, téléportation cognitive, mesure partielle.
"""
from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class ConceptState:
    id: str
    name: str
    amplitude_0: complex = 1.0 + 0j
    amplitude_1: complex = 0.0 + 0j
    measured: bool = False
    measurement_result: int = 0

    def probability_0(self) -> float:
        return abs(self.amplitude_0) ** 2

    def probability_1(self) -> float:
        return abs(self.amplitude_1) ** 2

    def normalize(self):
        norm = math.sqrt(self.probability_0() + self.probability_1())
        if norm > 0:
            self.amplitude_0 /= norm
            self.amplitude_1 /= norm

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "p0": round(self.probability_0(), 3),
                "p1": round(self.probability_1(), 3),
                "measured": self.measured}


@dataclass(slots=True)
class EntanglementPair:
    id: str
    concept_a_id: str
    concept_b_id: str
    bell_type: str = "Φ⁺"  # Φ⁺, Φ⁻, Ψ⁺, Ψ⁻
    correlation_strength: float = 1.0
    active: bool = True


class EntanglementEngine:
    """Moteur d'intrication cognitive.

    Crée des paires de concepts intriqués, mesure les corrélations,
    vérifie les inégalités de Bell, et téléporte des états.
    """

    def __init__(self):
        self.states: dict[str, ConceptState] = {}
        self.pairs: dict[str, EntanglementPair] = {}
        self.network = LeaderNetwork()
        self._measurement_history: list[dict] = []

    def create_state(self, name: str) -> ConceptState:
        s = ConceptState(
            id=f"QST-{uuid.uuid4().hex[:12]}",
            name=name, amplitude_0=1.0 + 0j, amplitude_1=0.0 + 0j,
        )
        self.states[s.id] = s
        return s

    def entangle(self, a_id: str, b_id: str,
                 bell_type: str = "Φ⁺") -> EntanglementPair | None:
        """Crée une paire intriquée entre deux concepts.
        États de Bell : Φ⁺ = (|00⟩ + |11⟩)/√2, etc."""
        if a_id not in self.states or b_id not in self.states:
            return None
        a = self.states[a_id]
        b = self.states[b_id]
        if bell_type == "Φ⁺":
            a.amplitude_0 = complex(1 / math.sqrt(2))
            a.amplitude_1 = complex(1 / math.sqrt(2))
            b.amplitude_0 = complex(1 / math.sqrt(2))
            b.amplitude_1 = complex(1 / math.sqrt(2))
        elif bell_type == "Ψ⁺":
            a.amplitude_0 = complex(1 / math.sqrt(2))
            a.amplitude_1 = complex(-1 / math.sqrt(2))
            b.amplitude_0 = complex(1 / math.sqrt(2))
            b.amplitude_1 = complex(1 / math.sqrt(2))
        else:
            a.amplitude_0 = 1.0 + 0j
            a.amplitude_1 = 0.0 + 0j
            b.amplitude_0 = 0.0 + 0j
            b.amplitude_1 = 1.0 + 0j
        pair = EntanglementPair(
            id=f"ENT-{uuid.uuid4().hex[:12]}",
            concept_a_id=a_id, concept_b_id=b_id,
            bell_type=bell_type, correlation_strength=1.0,
        )
        self.pairs[pair.id] = pair
        return pair

    def measure(self, state_id: str) -> dict:
        """Mesure un état intriqué — collapse et propage."""
        state = self.states.get(state_id)
        if not state:
            return {"error": "state not found"}
        if state.measured:
            return {"result": state.measurement_result,
                    "already_measured": True}
        p0 = state.probability_0()
        result = 0 if random.random() < p0 else 1
        state.amplitude_0 = complex(1.0 if result == 0 else 0.0)
        state.amplitude_1 = complex(0.0 if result == 0 else 1.0)
        state.measured = True
        state.measurement_result = result
        effects = []
        for pair in self.pairs.values():
            if not pair.active:
                continue
            partner_id = None
            if pair.concept_a_id == state_id:
                partner_id = pair.concept_b_id
            elif pair.concept_b_id == state_id:
                partner_id = pair.concept_a_id
            if partner_id:
                partner = self.states.get(partner_id)
                if partner and not partner.measured:
                    partner.amplitude_0 = complex(1.0 if result == 0
                                                  else 0.0)
                    partner.amplitude_1 = complex(0.0 if result == 0
                                                  else 1.0)
                    partner.measured = True
                    partner.measurement_result = result
                    effects.append({
                        "pair_id": pair.id,
                        "partner_id": partner_id,
                        "partner_name": partner.name,
                        "collapsed_to": result,
                    })
        self._measurement_history.append({
            "state": state.name, "result": result,
            "entanglement_effects": len(effects),
        })
        return {"result": result, "effects": effects}

    def bell_test(self, n_trials: int = 100) -> dict:
        """Test des inégalités de Bell cognitives.
        Si S > 2, violation de la limite classique."""
        results = {"ab_same": 0, "ac_same": 0, "bc_same": 0,
                   "total": n_trials}
        for _ in range(n_trials):
            a_val = random.randint(0, 1)
            b_val = random.randint(0, 1)
            c_val = random.randint(0, 1)
            if a_val == b_val:
                results["ab_same"] += 1
            if a_val == c_val:
                results["ac_same"] += 1
            if b_val == c_val:
                results["bc_same"] += 1
        p_ab = results["ab_same"] / n_trials
        p_ac = results["ac_same"] / n_trials
        p_bc = results["bc_same"] / n_trials
        s = p_ab + p_ac - p_bc
        return {
            "p_ab": round(p_ab, 3),
            "p_ac": round(p_ac, 3),
            "p_bc": round(p_bc, 3),
            "s_value": round(s, 3),
            "bell_inequality_violated": s > 1.0,
            "quantum_limit": s > 2.0,
        }

    def teleport(self, source_id: str, target_id: str) -> bool:
        """Téléportation cognitive d'un état à un autre."""
        if source_id not in self.states or target_id not in self.states:
            return False
        entangled_with_source = None
        for pair in self.pairs.values():
            if pair.concept_a_id == source_id:
                entangled_with_source = pair.concept_b_id
            elif pair.concept_b_id == source_id:
                entangled_with_source = pair.concept_a_id
        if not entangled_with_source:
            return False
        source = self.states[source_id]
        target = self.states[target_id]
        target.amplitude_0 = source.amplitude_0
        target.amplitude_1 = source.amplitude_1
        target.measured = source.measured
        target.measurement_result = source.measurement_result
        source.amplitude_0 = 0.0 + 0j
        source.amplitude_1 = 0.0 + 0j
        return True

    def get_stats(self) -> dict:
        return {
            "states": len(self.states),
            "entangled_pairs": len(self.pairs),
            "measurements_taken": len(self._measurement_history),
            "active_pairs": sum(1 for p in self.pairs.values() if p.active),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create_state":
            s = self.create_state(input_data.get("name", "?"))
            return {"status": "ok", "state": s.to_dict()}
        elif action == "entangle":
            p = self.entangle(
                input_data.get("a", ""),
                input_data.get("b", ""),
                input_data.get("bell_type", "Φ⁺"),
            )
            return {"status": "ok" if p else "error"}
        elif action == "measure":
            return {"status": "ok",
                    "measurement": self.measure(
                        input_data.get("state_id", ""))}
        elif action == "bell_test":
            return {"status": "ok",
                    "bell": self.bell_test(
                        input_data.get("trials", 100))}
        elif action == "teleport":
            ok = self.teleport(
                input_data.get("source", ""),
                input_data.get("target", ""),
            )
            return {"status": "ok" if ok else "error"}
        return {"status": "ok", "states": len(self.states)}
