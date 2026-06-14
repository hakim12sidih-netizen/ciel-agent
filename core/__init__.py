"""
CIEL v∞.2 — Core package : Noyau Primordial.

Contient :
  - axioms      : les 4 axiomes cosmiques α,β,γ,δ (immuables, signés)
  - identity    : Ed25519 + UUID v7 (identité persistante de l'instance)
  - crypto      : BLAKE2b + Ed25519 + X25519 + ChaCha20-Poly1305
  - kernel      : boucle asyncio principale (cœur de l'instance)
  - observability : metrics (Counter/Gauge/Histogram) + health checks
"""
from __future__ import annotations

# ── Constantes du Noyau Primordial ────────────────────────
# Le Noyau est l'ancrage immuable de toute instance CIEL.
# Il contient : identités, axiomes, clé cryptographique maître.
NOYAU_VERSION = "1.0.0"
NOYAU_IMMUTABLE = True  # aucune mutation possible après initialisation
