"""ZKP — Zero-Knowledge Proof utilities."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("ciel.security.zkp")


def generate_proof(secret: str, public: str) -> dict[str, Any]:
    """Génère une preuve à connaissance nulle."""
    log.warning("ZKP stub: not implemented")
    return {"proof": "", "status": "stub"}


def verify(proof: dict, public: str) -> bool:
    """Vérifie une preuve."""
    return False
