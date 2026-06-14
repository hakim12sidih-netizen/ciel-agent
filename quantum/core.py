from __future__ import annotations

import cmath
import math
import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np


class Qubit:
    """Un qubit en superposition |ψ⟩ = α|0⟩ + β|1⟩."""

    def __init__(self, alpha: complex = 1.0, beta: complex = 0.0):
        norm = abs(alpha) ** 2 + abs(beta) ** 2
        if norm == 0:
            alpha = 1.0
            norm = 1.0
        self.alpha = alpha / math.sqrt(norm)
        self.beta = beta / math.sqrt(norm)

    def measure(self) -> int:
        prob0 = abs(self.alpha) ** 2
        outcome = 0 if random.random() < prob0 else 1
        self.alpha = complex(1.0 if outcome == 0 else 0.0)
        self.beta = complex(1.0 if outcome == 1 else 0.0)
        return outcome

    def prob0(self) -> float:
        return abs(self.alpha) ** 2

    def prob1(self) -> float:
        return abs(self.beta) ** 2

    def density_matrix(self) -> np.ndarray:
        return np.array([
            [abs(self.alpha) ** 2, self.alpha * self.beta.conjugate()],
            [self.alpha.conjugate() * self.beta, abs(self.beta) ** 2],
        ])

    def __repr__(self) -> str:
        return f"{self.alpha:.3f}|0⟩ + {self.beta:.3f}|1⟩"


class QuantumGate:
    """Porte quantique — matrice 2×2 unitaire."""

    def __init__(self, matrix: np.ndarray, name: str = ""):
        self.matrix = matrix
        self.name = name

    def apply(self, qubit: Qubit) -> Qubit:
        v = np.array([[qubit.alpha], [qubit.beta]])
        result = self.matrix @ v
        return Qubit(result[0, 0], result[1, 0])

    @staticmethod
    def hadamard() -> QuantumGate:
        h = (1 / math.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
        return QuantumGate(h, "H")

    @staticmethod
    def pauli_x() -> QuantumGate:
        return QuantumGate(np.array([[0, 1], [1, 0]], dtype=complex), "X")

    @staticmethod
    def pauli_y() -> QuantumGate:
        return QuantumGate(
            np.array([[0, -1j], [1j, 0]], dtype=complex), "Y"
        )

    @staticmethod
    def pauli_z() -> QuantumGate:
        return QuantumGate(np.array([[1, 0], [0, -1]], dtype=complex), "Z")

    @staticmethod
    def s_gate() -> QuantumGate:
        return QuantumGate(np.array([[1, 0], [0, 1j]], dtype=complex), "S")

    @staticmethod
    def t_gate() -> QuantumGate:
        return QuantumGate(
            np.array([[1, 0], [0, cmath.exp(1j * math.pi / 4)]], dtype=complex), "T"
        )

    @staticmethod
    def phase(phi: float) -> QuantumGate:
        return QuantumGate(
            np.array([[1, 0], [0, cmath.exp(1j * phi)]], dtype=complex),
            f"P({phi:.2f})",
        )

    @staticmethod
    def rx(theta: float) -> QuantumGate:
        return QuantumGate(
            np.array([
                [math.cos(theta / 2), -1j * math.sin(theta / 2)],
                [-1j * math.sin(theta / 2), math.cos(theta / 2)],
            ], dtype=complex),
            f"Rx({theta:.2f})",
        )

    @staticmethod
    def ry(theta: float) -> QuantumGate:
        return QuantumGate(
            np.array([
                [math.cos(theta / 2), -math.sin(theta / 2)],
                [math.sin(theta / 2), math.cos(theta / 2)],
            ], dtype=complex),
            f"Ry({theta:.2f})",
        )

    @staticmethod
    def rz(theta: float) -> QuantumGate:
        return QuantumGate(
            np.array([
                [cmath.exp(-1j * theta / 2), 0],
                [0, cmath.exp(1j * theta / 2)],
            ], dtype=complex),
            f"Rz({theta:.2f})",
        )


GATES = {
    "H": QuantumGate.hadamard,
    "X": QuantumGate.pauli_x,
    "Y": QuantumGate.pauli_y,
    "Z": QuantumGate.pauli_z,
    "S": QuantumGate.s_gate,
    "T": QuantumGate.t_gate,
}


class QuantumRegister:
    """Registre quantique multi-qubits."""

    def __init__(self, n_qubits: int = 1):
        self.n_qubits = n_qubits
        self.qubits = [Qubit() for _ in range(n_qubits)]

    def apply_gate(self, gate: QuantumGate, target: int = 0) -> None:
        if target < 0 or target >= self.n_qubits:
            raise ValueError(f"invalid target qubit {target}")
        self.qubits[target] = gate.apply(self.qubits[target])

    def apply_cnot(self, control: int, target: int) -> None:
        if control < 0 or control >= self.n_qubits:
            raise ValueError(f"invalid control {control}")
        if target < 0 or target >= self.n_qubits:
            raise ValueError(f"invalid target {target}")
        if control == target:
            raise ValueError("control and target must differ")
        prob1 = self.qubits[control].prob1()
        if random.random() < prob1:
            self.qubits[target] = QuantumGate.pauli_x().apply(self.qubits[target])

    def measure_all(self) -> list[int]:
        return [q.measure() for q in self.qubits]

    def measure(self, qubit: int = 0) -> int:
        return self.qubits[qubit].measure()

    def state_vector(self) -> np.ndarray:
        dim = 1 << self.n_qubits
        vec = np.zeros(dim, dtype=complex)
        for i in range(dim):
            amp = 1.0 + 0j
            for j in range(self.n_qubits):
                bit = (i >> (self.n_qubits - 1 - j)) & 1
                q = self.qubits[j]
                amp *= q.alpha if bit == 0 else q.beta
            vec[i] = amp
        return vec

    def probabilities(self) -> list[float]:
        sv = self.state_vector()
        return [abs(x) ** 2 for x in sv]

    def reset(self) -> None:
        self.qubits = [Qubit() for _ in range(self.n_qubits)]


class QuantumCircuit:
    """Circuit quantique — séquence de portes et mesures."""

    def __init__(self, n_qubits: int = 1):
        self.register = QuantumRegister(n_qubits)
        self._operations: list[dict[str, Any]] = []
        self._measurements: list[int] = []

    def h(self, target: int = 0) -> None:
        self.register.apply_gate(QuantumGate.hadamard(), target)
        self._operations.append({"gate": "H", "target": target})

    def x(self, target: int = 0) -> None:
        self.register.apply_gate(QuantumGate.pauli_x(), target)
        self._operations.append({"gate": "X", "target": target})

    def y(self, target: int = 0) -> None:
        self.register.apply_gate(QuantumGate.pauli_y(), target)
        self._operations.append({"gate": "Y", "target": target})

    def z(self, target: int = 0) -> None:
        self.register.apply_gate(QuantumGate.pauli_z(), target)
        self._operations.append({"gate": "Z", "target": target})

    def s(self, target: int = 0) -> None:
        self.register.apply_gate(QuantumGate.s_gate(), target)
        self._operations.append({"gate": "S", "target": target})

    def t(self, target: int = 0) -> None:
        self.register.apply_gate(QuantumGate.t_gate(), target)
        self._operations.append({"gate": "T", "target": target})

    def rx(self, theta: float, target: int = 0) -> None:
        self.register.apply_gate(QuantumGate.rx(theta), target)
        self._operations.append({"gate": f"Rx({theta:.3f})", "target": target})

    def ry(self, theta: float, target: int = 0) -> None:
        self.register.apply_gate(QuantumGate.ry(theta), target)
        self._operations.append({"gate": f"Ry({theta:.3f})", "target": target})

    def rz(self, theta: float, target: int = 0) -> None:
        self.register.apply_gate(QuantumGate.rz(theta), target)
        self._operations.append({"gate": f"Rz({theta:.3f})", "target": target})

    def cnot(self, control: int, target: int) -> None:
        self.register.apply_cnot(control, target)
        self._operations.append({"gate": "CNOT", "control": control, "target": target})

    def measure(self, qubit: int = 0) -> int:
        result = self.register.measure(qubit)
        self._measurements.append(result)
        self._operations.append({"gate": "MEASURE", "target": qubit, "result": result})
        return result

    def measure_all(self) -> list[int]:
        results = self.register.measure_all()
        self._measurements.extend(results)
        self._operations.append({"gate": "MEASURE_ALL", "results": results})
        return results

    def depth(self) -> int:
        return len(self._operations)

    def circuit_string(self) -> str:
        return " -> ".join(
            op.get("gate", str(op)) for op in self._operations
        )


class SuperpositionBelief:
    """Croyance en superposition — états multiples pondérés."""

    def __init__(self, concept: str = ""):
        self.concept = concept
        self.states: dict[str, float] = {}
        self._collapsed: str | None = None

    def add_state(self, label: str, amplitude: float) -> None:
        self.states[label] = amplitude
        self._collapsed = None

    def observe(self) -> str:
        if not self.states:
            return ""
        total = sum(abs(a) for a in self.states.values())
        if total == 0:
            return ""
        r = random.uniform(0, total)
        cumulative = 0.0
        for label, amp in self.states.items():
            cumulative += abs(amp)
            if r <= cumulative:
                self._collapsed = label
                return label
        return list(self.states.keys())[-1]

    def interference(self, other: SuperpositionBelief) -> float:
        common = set(self.states.keys()) & set(other.states.keys())
        if not common:
            return 0.0
        total = 0.0
        for k in common:
            total += abs(self.states[k]) * abs(other.states[k])
        return total / len(common)

    def entropy(self) -> float:
        total = sum(abs(a) for a in self.states.values())
        if total == 0:
            return 0.0
        h = 0.0
        for a in self.states.values():
            p = abs(a) / total
            if p > 0:
                h -= p * math.log2(p)
        return h


class QuantumOracle:
    """Oracle quantique — fonction boîte noire."""

    def __init__(self, func: Any = None):
        self._func = func or (lambda x: x)
        self._calls = 0

    def evaluate(self, x: Any) -> Any:
        self._calls += 1
        return self._func(x)

    def grover_oracle(self, target: int, n_qubits: int) -> QuantumCircuit:
        circuit = QuantumCircuit(n_qubits)
        circuit.z(target)
        return circuit

    def call_count(self) -> int:
        return self._calls


class QAOA:
    """Quantum Approximate Optimization Algorithm — simplifié."""

    def __init__(self, n_qubits: int = 2, p_layers: int = 1):
        self.n_qubits = n_qubits
        self.p_layers = p_layers
        self._optimal_params: list[float] = []

    def cost_hamiltonian(self, weights: list[float]) -> float:
        circuit = QuantumCircuit(self.n_qubits)
        for i in range(self.n_qubits):
            circuit.h(i)
        for _ in range(self.p_layers):
            gamma = random.uniform(0, 2 * math.pi)
            beta = random.uniform(0, math.pi)
            for i, w in enumerate(weights):
                circuit.rz(gamma * w, i)
            for i in range(self.n_qubits):
                circuit.rx(beta, i)
        results = circuit.measure_all()
        cost = sum(weights[i] * (1 if results[i] == 0 else -1) for i in range(min(len(results), len(weights))))  # noqa: E501
        return cost

    def optimize(self, weights: list[float], steps: int = 10) -> list[float]:
        best_cost = float("inf")
        best_params = [0.0] * (2 * self.p_layers)
        for _ in range(steps):
            params = [random.uniform(0, 2 * math.pi) for _ in range(2 * self.p_layers)]
            cost = self.cost_hamiltonian(weights)
            if cost < best_cost:
                best_cost = cost
                best_params = params
        self._optimal_params = best_params
        return best_params


class VQE:
    """Variational Quantum Eigensolver — simplifié."""

    def __init__(self, n_qubits: int = 1):
        self.n_qubits = n_qubits
        self._params: list[float] = []

    def ansatz(self, params: list[float]) -> QuantumCircuit:
        circuit = QuantumCircuit(self.n_qubits)
        for i in range(self.n_qubits):
            circuit.ry(params[i] if i < len(params) else 0.5, i)
        for i in range(self.n_qubits - 1):
            circuit.cnot(i, i + 1)
        return circuit

    def energy(self, params: list[float], hamiltonian: list[float]) -> float:
        circuit = self.ansatz(params)
        state = circuit.register.state_vector()
        energy = 0.0
        dim = 1 << self.n_qubits
        for i in range(min(len(hamiltonian), dim)):
            energy += hamiltonian[i] * abs(state[i]) ** 2
        return energy

    def optimize(self, hamiltonian: list[float], steps: int = 20) -> list[float]:
        best_energy = float("inf")
        best_params = [0.5] * self.n_qubits
        for _ in range(steps):
            params = [random.uniform(0, math.pi) for _ in range(self.n_qubits)]
            e = self.energy(params, hamiltonian)
            if e < best_energy:
                best_energy = e
                best_params = params
        self._params = best_params
        return best_params

    def ground_energy(self) -> float:
        return self.energy(self._params, [1.0] * (1 << self.n_qubits))


class QuantumEngine:
    """Moteur quantique — superposition, portes, circuits, oracles, QAOA, VQE."""

    def __init__(self):
        self._circuits: list[dict[str, Any]] = []
        self._measurements: list[int] = []

    def create_qubit(self, alpha: float = 1.0, beta: float = 0.0) -> Qubit:
        return Qubit(complex(alpha), complex(beta))

    def create_register(self, n: int = 1) -> QuantumRegister:
        return QuantumRegister(n)

    def create_circuit(self, n_qubits: int = 1) -> QuantumCircuit:
        return QuantumCircuit(n_qubits)

    def run_circuit(self, circuit: QuantumCircuit, shots: int = 1) -> list[list[int]]:
        results = []
        for _ in range(shots):
            reg = QuantumRegister(circuit.register.n_qubits)
            temp = QuantumCircuit(circuit.register.n_qubits)
            temp.register = reg
            for op in circuit._operations:
                g = op.get("gate", "")
                t = op.get("target", 0)
                if g == "H":
                    temp.h(t)
                elif g == "X":
                    temp.x(t)
                elif g == "Y":
                    temp.y(t)
                elif g == "Z":
                    temp.z(t)
                elif g == "S":
                    temp.s(t)
                elif g == "T":
                    temp.t(t)
                elif g == "CNOT":
                    temp.cnot(op.get("control", 0), t)
                elif g.startswith("Rx"):
                    theta = float(g.split("(")[1].split(")")[0])
                    temp.rx(theta, t)
                elif g.startswith("Ry"):
                    theta = float(g.split("(")[1].split(")")[0])
                    temp.ry(theta, t)
                elif g.startswith("Rz"):
                    theta = float(g.split("(")[1].split(")")[0])
                    temp.rz(theta, t)
                elif g == "MEASURE":
                    temp.measure(t)
                elif g == "MEASURE_ALL":
                    temp.measure_all()
            results.append(temp.measure_all())
        self._circuits.append({"circuit": str(circuit.circuit_string()), "shots": shots, "results": results})
        self._measurements.extend(results[-1] if results else [])
        return results

    def create_belief(self, concept: str = "") -> SuperpositionBelief:
        return SuperpositionBelief(concept)

    def create_oracle(self, func: Any = None) -> QuantumOracle:
        return QuantumOracle(func)

    def create_qaoa(self, n_qubits: int = 2, layers: int = 1) -> QAOA:
        return QAOA(n_qubits, layers)

    def create_vqe(self, n_qubits: int = 1) -> VQE:
        return VQE(n_qubits)

    def get_stats(self) -> dict[str, Any]:
        return {
            "circuits_executed": len(self._circuits),
            "total_measurements": len(self._measurements),
            "measurement_counts": {
                "0": self._measurements.count(0),
                "1": self._measurements.count(1),
            } if self._measurements else {},
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "qubit":
            q = self.create_qubit(float(data.get("alpha", 1.0)), float(data.get("beta", 0.0)))
            return {"success": True, "action": "qubit", "prob0": q.prob0(), "prob1": q.prob1()}

        elif action == "apply_gate":
            gate_name = str(data.get("gate", "H")).upper()
            target = int(data.get("target", 0))
            if gate_name not in GATES:
                return {"success": False, "error": f"unknown gate '{gate_name}'"}
            q = self.create_qubit(float(data.get("alpha", 1.0)), float(data.get("beta", 0.0)))
            q2 = GATES[gate_name]().apply(q)
            return {"success": True, "action": "apply_gate", "gate": gate_name,
                    "prob0": q2.prob0(), "prob1": q2.prob1()}

        elif action == "measure":
            alpha = float(data.get("alpha", 1.0))
            beta = float(data.get("beta", 0.0))
            q = Qubit(complex(alpha), complex(beta))
            result = q.measure()
            return {"success": True, "action": "measure", "result": result}

        elif action == "circuit":
            n = int(data.get("n_qubits", 1))
            gates = data.get("gates", [])
            circuit = self.create_circuit(n)
            for g in gates:
                name = str(g.get("gate", "")).upper()
                t = int(g.get("target", 0))
                if name == "H":
                    circuit.h(t)
                elif name == "X":
                    circuit.x(t)
                elif name == "CNOT":
                    circuit.cnot(t, int(g.get("control", 0)))
            results = self.run_circuit(circuit)
            return {"success": True, "action": "circuit", "results": results,
                    "depth": circuit.depth()}

        elif action == "belief":
            concept = str(data.get("concept", "unknown"))
            belief = self.create_belief(concept)
            states = data.get("states", {})
            for label, amp in states.items():
                belief.add_state(label, float(amp))
            observed = belief.observe()
            return {"success": True, "action": "belief", "concept": concept,
                    "entropy": belief.entropy(), "observed": observed}

        elif action == "qaoa":
            weights = data.get("weights", [1.0, -1.0])
            layers = int(data.get("layers", 1))
            qaoa = self.create_qaoa(len(weights), layers)
            params = qaoa.optimize(weights)
            return {"success": True, "action": "qaoa", "params": params}

        elif action == "vqe":
            hamiltonian = data.get("hamiltonian", [1.0, -1.0])
            n = int(math.log2(len(hamiltonian))) if len(hamiltonian) > 1 else 1
            vqe = self.create_vqe(n)
            params = vqe.optimize(hamiltonian)
            return {"success": True, "action": "vqe", "params": params}

        elif action == "stats":
            return {"success": True, "action": "stats", "stats": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
