"""
CIEL v∞.2 — Test suite.

Organisation :
  - test_axioms.py       : property-based sur les 4 axiomes (αβγδ)
  - test_identity.py     : Ed25519 + UUID v7 + persistence
  - test_crypto.py       : BLAKE2b, Ed25519, X25519, ChaCha20-Poly1305
  - test_kernel.py       : boucle asyncio + tick + drift
  - test_observability.py: Counter/Gauge/Histogram
  - test_ethics.py       : filter + transparency + reversibility
  - test_polyglot.py     : bridge subprocess
  - test_imports.py      : tous les modules importent
  - test_smoke.py        : E2E minimal (kernel + axioms + identity)
"""
