"""
Transverse — QUANTUM : Calcul Quantique.

Composants :
  - qubit          : superposition |ψ⟩ = α|0⟩ + β|1⟩
  - gates          : H, X, Y, Z, S, T, Rx, Ry, Rz, CNOT
  - circuit        : séquence de portes + mesure
  - superposition  : croyances en superposition quantique
  - oracle         : oracle quantique (Grover)
  - qaoa           : Quantum Approximate Optimization Algorithm
  - vqe            : Variational Quantum Eigensolver

Implémentation : simulateur local pure-Python (NumPy).
"""
from __future__ import annotations

from ciel.quantum.core import (
    Qubit, QuantumGate, QuantumRegister, QuantumCircuit,
    SuperpositionBelief, QuantumOracle, QAOA, VQE,
    QuantumEngine,
)
__all__ = [
    "Qubit", "QuantumGate", "QuantumRegister", "QuantumCircuit",
    "SuperpositionBelief", "QuantumOracle", "QAOA", "VQE",
    "QuantumEngine",
]
