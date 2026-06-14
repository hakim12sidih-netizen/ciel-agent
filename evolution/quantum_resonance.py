from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QubitState(Enum):
    ZERO = "|0⟩"
    ONE = "|1⟩"
    SUPERPOSITION = "α|0⟩+β|1⟩"
    ENTANGLED = "|Φ⁺⟩"


@dataclass(slots=True)
class Qubit:
    id: str
    state: QubitState
    amplitude_real: float
    amplitude_imag: float
    phase: float = 0.0
    entangled_with: str | None = None


@dataclass(slots=True)
class ResonanceField:
    id: str
    frequency: float
    amplitude: float
    coherence: float
    harmonics: list[float] = field(default_factory=list)


class QuantumResonance:
    def __init__(self) -> None:
        self._qubits: dict[str, Qubit] = {}
        self._fields: dict[str, ResonanceField] = {}
        self._coherence: float = 1.0

    def create_qubit(self) -> Qubit:
        qid = f"qubit_{len(self._qubits)}"
        state = random.choice([QubitState.ZERO, QubitState.ONE, QubitState.SUPERPOSITION])
        q = Qubit(
            id=qid,
            state=state,
            amplitude_real=random.uniform(-1, 1),
            amplitude_imag=random.uniform(-1, 1),
            phase=random.uniform(0, 2 * math.pi),
        )
        self._qubits[qid] = q
        return q

    def entangle(self, q1_id: str, q2_id: str) -> bool:
        if q1_id not in self._qubits or q2_id not in self._qubits:
            return False
        q1 = self._qubits[q1_id]; q2 = self._qubits[q2_id]
        q1.state = QubitState.ENTANGLED; q2.state = QubitState.ENTANGLED
        q1.entangled_with = q2_id; q2.entangled_with = q1_id
        return True

    def measure(self, qubit_id: str) -> int:
        q = self._qubits.get(qubit_id)
        if not q:
            return 0
        prob_one = (q.amplitude_real ** 2 + q.amplitude_imag ** 2) * 0.5 + 0.5
        result = 1 if random.random() < prob_one else 0
        q.state = QubitState.ONE if result else QubitState.ZERO
        q.amplitude_real = float(result)
        q.amplitude_imag = 0.0
        self._coherence *= 0.95
        return result

    def create_field(self, frequency: float) -> ResonanceField:
        fid = f"field_{len(self._fields)}"
        f = ResonanceField(
            id=fid,
            frequency=frequency,
            amplitude=random.uniform(0.1, 1.0),
            coherence=random.uniform(0.5, 1.0),
            harmonics=[frequency * (i + 2) for i in range(3)],
        )
        self._fields[fid] = f
        return f

    def get_state(self) -> dict[str, Any]:
        return {
            "qubits": len(self._qubits),
            "fields": len(self._fields),
            "coherence": self._coherence,
            "entangled_pairs": sum(1 for q in self._qubits.values() if q.entangled_with is not None) // 2,
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "state")
        if action == "state":
            return {"success": True, **self.get_state()}
        elif action == "create_qubit":
            q = self.create_qubit()
            return {"success": True, "qubit_id": q.id, "state": q.state.value}
        elif action == "measure":
            q = self.measure(str(input_data.get("qubit_id", "")))
            return {"success": True, "result": q}
        return {"success": False, "error": f"unknown action '{action}'"}
