from __future__ import annotations

import math

import numpy as np
import pytest
from ciel.quantum.core import (
    Qubit, QuantumGate, QuantumRegister, QuantumCircuit,
    SuperpositionBelief, QuantumOracle, QAOA, VQE,
    QuantumEngine,
)


class TestQubit:
    def test_default(self):
        q = Qubit()
        assert q.alpha == pytest.approx(1.0)
        assert q.beta == pytest.approx(0.0)
        assert q.prob0() == 1.0
        assert q.prob1() == 0.0

    def test_superposition(self):
        q = Qubit(complex(1 / math.sqrt(2)), complex(1 / math.sqrt(2)))
        assert q.prob0() == pytest.approx(0.5)
        assert q.prob1() == pytest.approx(0.5)

    def test_normalization(self):
        q = Qubit(complex(2.0), complex(0.0))
        assert q.prob0() == pytest.approx(1.0)

    def test_measure_collapse(self):
        q = Qubit(complex(0.5**0.5), complex(0.5**0.5))
        result = q.measure()
        assert result in (0, 1)
        assert q.prob0() in (0.0, 1.0)

    def test_density_matrix(self):
        q = Qubit()
        dm = q.density_matrix()
        assert dm.shape == (2, 2)
        assert dm[0, 0] == pytest.approx(1.0)

    def test_measure_zero_prob(self):
        q = Qubit(complex(0.0), complex(1.0))
        assert q.measure() == 1


class TestQuantumGate:
    def test_hadamard(self):
        h = QuantumGate.hadamard()
        assert h.name == "H"
        q = Qubit()
        q2 = h.apply(q)
        assert q2.prob0() == pytest.approx(0.5)

    def test_pauli_x(self):
        x = QuantumGate.pauli_x()
        q = Qubit()
        q2 = x.apply(q)
        assert q2.prob1() == pytest.approx(1.0)

    def test_pauli_z(self):
        z = QuantumGate.pauli_z()
        q = Qubit(complex(1 / math.sqrt(2)), complex(1 / math.sqrt(2)))
        q2 = z.apply(q)
        assert q2.prob0() == pytest.approx(0.5)

    def test_s_gate(self):
        s = QuantumGate.s_gate()
        q = Qubit(complex(0.0), complex(1.0))
        q2 = s.apply(q)
        assert abs(q2.beta - 1j) < 1e-10

    def test_t_gate(self):
        t = QuantumGate.t_gate()
        q = Qubit(complex(0.0), complex(1.0))
        q2 = t.apply(q)
        expected = math.cos(math.pi / 4) + 1j * math.sin(math.pi / 4)
        assert abs(q2.beta - expected) < 1e-10

    def test_phase(self):
        p = QuantumGate.phase(math.pi)
        q = Qubit(complex(0.0), complex(1.0))
        q2 = p.apply(q)
        assert abs(q2.beta - (-1.0)) < 1e-10

    def test_rx(self):
        rx = QuantumGate.rx(math.pi)
        q = Qubit()
        q2 = rx.apply(q)
        assert q2.beta.imag == pytest.approx(-1.0, abs=1e-10)

    def test_ry(self):
        ry = QuantumGate.ry(math.pi)
        q = Qubit()
        q2 = ry.apply(q)
        assert q2.prob1() == pytest.approx(1.0, abs=1e-10)

    def test_rz(self):
        rz = QuantumGate.rz(math.pi)
        q = Qubit()
        q2 = rz.apply(q)
        assert q2.prob0() == 1.0

    def test_gates_dict(self):
        from ciel.quantum.core import GATES
        assert "H" in GATES
        assert "X" in GATES
        assert "T" in GATES
        assert callable(GATES["H"])


class TestQuantumRegister:
    def test_create(self):
        reg = QuantumRegister(3)
        assert reg.n_qubits == 3
        assert len(reg.qubits) == 3

    def test_apply_gate(self):
        reg = QuantumRegister(1)
        reg.apply_gate(QuantumGate.hadamard())
        assert reg.qubits[0].prob0() == pytest.approx(0.5)

    def test_apply_gate_invalid_target(self):
        reg = QuantumRegister(1)
        with pytest.raises(ValueError):
            reg.apply_gate(QuantumGate.hadamard(), 5)

    def test_cnot(self):
        reg = QuantumRegister(2)
        reg.qubits[0] = Qubit(complex(0.0), complex(1.0))
        reg.apply_cnot(0, 1)
        assert reg.qubits[1].prob1() == pytest.approx(1.0)

    def test_cnot_invalid(self):
        reg = QuantumRegister(2)
        with pytest.raises(ValueError):
            reg.apply_cnot(0, 0)

    def test_measure_all(self):
        reg = QuantumRegister(3)
        results = reg.measure_all()
        assert len(results) == 3

    def test_state_vector(self):
        reg = QuantumRegister(2)
        sv = reg.state_vector()
        assert len(sv) == 4
        assert sv[0] == pytest.approx(1.0)

    def test_probabilities(self):
        reg = QuantumRegister(1)
        reg.apply_gate(QuantumGate.hadamard())
        probs = reg.probabilities()
        assert len(probs) == 2
        assert probs[0] == pytest.approx(0.5)

    def test_reset(self):
        reg = QuantumRegister(2)
        reg.apply_gate(QuantumGate.pauli_x(), 0)
        reg.reset()
        assert reg.qubits[0].prob0() == 1.0


class TestQuantumCircuit:
    def test_create(self):
        c = QuantumCircuit(2)
        assert c.register.n_qubits == 2
        assert c.depth() == 0

    def test_h(self):
        c = QuantumCircuit()
        c.h(0)
        assert c.depth() == 1

    def test_x(self):
        c = QuantumCircuit()
        c.x(0)
        assert c.register.qubits[0].prob1() == 1.0

    def test_cnot(self):
        c = QuantumCircuit(2)
        c.x(0)
        c.cnot(0, 1)
        assert c.register.qubits[1].prob1() == 1.0

    def test_measure(self):
        c = QuantumCircuit()
        result = c.measure(0)
        assert result in (0, 1)

    def test_measure_all(self):
        c = QuantumCircuit(3)
        results = c.measure_all()
        assert len(results) == 3

    def test_rx_ry_rz(self):
        c = QuantumCircuit()
        c.rx(math.pi, 0)
        c.ry(math.pi, 0)
        c.rz(math.pi, 0)
        assert c.depth() == 3

    def test_s_t(self):
        c = QuantumCircuit()
        c.s(0)
        c.t(0)
        assert c.depth() == 2

    def test_circuit_string(self):
        c = QuantumCircuit()
        c.h(0)
        c.x(0)
        s = c.circuit_string()
        assert "H" in s
        assert "X" in s

    def test_y_z(self):
        c = QuantumCircuit()
        c.y(0)
        c.z(0)
        assert c.depth() == 2


class TestSuperpositionBelief:
    def test_empty(self):
        b = SuperpositionBelief("test")
        assert b.observe() == ""
        assert b.entropy() == 0.0

    def test_add_state(self):
        b = SuperpositionBelief("color")
        b.add_state("red", 1.0)
        b.add_state("blue", 1.0)
        assert b.observe() in ("red", "blue")

    def test_entropy(self):
        b = SuperpositionBelief("coin")
        b.add_state("heads", 1.0)
        b.add_state("tails", 1.0)
        assert b.entropy() == pytest.approx(1.0)

    def test_interference(self):
        a = SuperpositionBelief("a")
        b = SuperpositionBelief("b")
        a.add_state("x", 1.0)
        b.add_state("x", 1.0)
        assert a.interference(b) == 1.0

    def test_interference_no_overlap(self):
        a = SuperpositionBelief("a")
        b = SuperpositionBelief("b")
        a.add_state("x", 1.0)
        b.add_state("y", 1.0)
        assert a.interference(b) == 0.0


class TestQuantumOracle:
    def test_evaluate(self):
        o = QuantumOracle(lambda x: x * 2)
        assert o.evaluate(5) == 10
        assert o.call_count() == 1

    def test_grover_oracle(self):
        o = QuantumOracle()
        circuit = o.grover_oracle(0, 2)
        assert circuit.depth() == 1


class TestQAOA:
    def test_create(self):
        qaoa = QAOA(2, 1)
        assert qaoa.n_qubits == 2
        assert qaoa.p_layers == 1

    def test_cost_hamiltonian(self):
        qaoa = QAOA(2, 1)
        cost = qaoa.cost_hamiltonian([1.0, -1.0])
        assert isinstance(cost, float)

    def test_optimize(self):
        qaoa = QAOA(2, 1)
        params = qaoa.optimize([1.0, -1.0], steps=5)
        assert len(params) == 2


class TestVQE:
    def test_create(self):
        vqe = VQE(2)
        assert vqe.n_qubits == 2

    def test_ansatz(self):
        vqe = VQE(2)
        circuit = vqe.ansatz([0.5, 0.8])
        assert circuit.depth() > 0

    def test_energy(self):
        vqe = VQE(1)
        e = vqe.energy([0.5], [1.0, -1.0])
        assert isinstance(e, float)

    def test_optimize(self):
        vqe = VQE(1)
        params = vqe.optimize([1.0, -1.0], steps=5)
        assert len(params) == 1


class TestQuantumEngine:
    def test_create(self):
        e = QuantumEngine()
        assert e._circuits == []
        assert e._measurements == []

    def test_create_qubit(self):
        e = QuantumEngine()
        q = e.create_qubit(1.0, 0.0)
        assert q.prob0() == 1.0

    def test_create_register(self):
        e = QuantumEngine()
        reg = e.create_register(3)
        assert reg.n_qubits == 3

    def test_create_circuit(self):
        e = QuantumEngine()
        c = e.create_circuit(2)
        assert c.register.n_qubits == 2

    def test_run_circuit_single(self):
        e = QuantumEngine()
        c = e.create_circuit(1)
        c.h(0)
        results = e.run_circuit(c, shots=1)
        assert len(results) == 1
        assert len(results[0]) == 1

    def test_run_circuit_multi(self):
        e = QuantumEngine()
        c = e.create_circuit(2)
        c.h(0)
        c.cnot(0, 1)
        results = e.run_circuit(c, shots=3)
        assert len(results) == 3

    def test_create_belief(self):
        e = QuantumEngine()
        b = e.create_belief("test")
        assert b.concept == "test"

    def test_create_oracle(self):
        e = QuantumEngine()
        o = e.create_oracle(lambda x: x + 1)
        assert o.evaluate(1) == 2

    def test_create_qaoa(self):
        e = QuantumEngine()
        qaoa = e.create_qaoa(2, 1)
        assert qaoa.n_qubits == 2

    def test_create_vqe(self):
        e = QuantumEngine()
        vqe = e.create_vqe(2)
        assert vqe.n_qubits == 2

    def test_get_stats(self):
        e = QuantumEngine()
        stats = e.get_stats()
        assert "circuits_executed" in stats
        assert stats["circuits_executed"] == 0

    def test_process_qubit(self):
        e = QuantumEngine()
        r = e.process({"action": "qubit", "alpha": 0.707, "beta": 0.707})
        assert r["success"] is True
        assert "prob0" in r

    def test_process_apply_gate(self):
        e = QuantumEngine()
        r = e.process({"action": "apply_gate", "gate": "H", "alpha": 1.0, "beta": 0.0})
        assert r["success"] is True
        assert r["gate"] == "H"

    def test_process_apply_gate_unknown(self):
        e = QuantumEngine()
        r = e.process({"action": "apply_gate", "gate": "ZZ"})
        assert r["success"] is False

    def test_process_measure(self):
        e = QuantumEngine()
        r = e.process({"action": "measure"})
        assert r["success"] is True
        assert r["result"] == 0

    def test_process_circuit(self):
        e = QuantumEngine()
        r = e.process({
            "action": "circuit",
            "n_qubits": 1,
            "gates": [{"gate": "H", "target": 0}],
        })
        assert r["success"] is True
        assert "results" in r

    def test_process_belief(self):
        e = QuantumEngine()
        r = e.process({
            "action": "belief",
            "concept": "color",
            "states": {"red": 1.0, "blue": 1.0},
        })
        assert r["success"] is True
        assert "entropy" in r
        assert r["entropy"] == pytest.approx(1.0)

    def test_process_qaoa(self):
        e = QuantumEngine()
        r = e.process({"action": "qaoa", "weights": [1.0, -1.0], "layers": 1})
        assert r["success"] is True
        assert len(r["params"]) == 2

    def test_process_vqe(self):
        e = QuantumEngine()
        r = e.process({"action": "vqe", "hamiltonian": [1.0, -1.0]})
        assert r["success"] is True
        assert len(r["params"]) == 1

    def test_process_stats(self):
        e = QuantumEngine()
        r = e.process({"action": "stats"})
        assert r["success"] is True

    def test_process_bad_action(self):
        e = QuantumEngine()
        r = e.process({"action": "nonexistent"})
        assert r["success"] is False

    def test_process_bad_input(self):
        e = QuantumEngine()
        r = e.process("bad")
        assert r["success"] is False
