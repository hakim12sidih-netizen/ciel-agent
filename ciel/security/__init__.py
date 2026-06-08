"""
Strate 3 + Transverse — SECURITY : Défense Totale.

Composants :
  - ThreatDetector    : 12 catégories A1-A12, scoring, mitigation
  - PostQuantumCrypto : Kyber KEM + Dilithium signature (SHA3)
  - ZKP               : Zero-Knowledge Proof (Schnorr-like)
  - SecretSharing     : Shamir (k,n)-threshold SMPC
  - AuditLog          : chaîne de hash immuable
  - Aegis             : bouclier multi-niveaux (NONE→PARANOID)
  - SecurityEngine    : process() compatible CIELBrain
"""
from __future__ import annotations

from ciel.security.core import (
    ThreatCategory, ThreatEvent, ThreatDetector,
    PostQuantumCrypto, ZKP, SecretSharing,
    AuditEntry, AuditLog, Aegis,
    SecurityEngine, THREAT_NAMES,
)
__all__ = [
    "ThreatCategory", "ThreatEvent", "ThreatDetector",
    "PostQuantumCrypto", "ZKP", "SecretSharing",
    "AuditEntry", "AuditLog", "Aegis",
    "SecurityEngine", "THREAT_NAMES",
]
