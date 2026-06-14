"""FHE — Fully Homomorphic Encryption stubs."""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("ciel.security.fhe")


def encrypt(plaintext: int | float, public_key: str) -> bytes:
    """Chiffre une valeur avec FHE."""
    log.warning("FHE stub: not implemented")
    return b""


def decrypt(ciphertext: bytes, secret_key: str) -> float:
    """Déchiffre une valeur FHE."""
    return 0.0


def add(a: bytes, b: bytes) -> bytes:
    """Addition homomorphe."""
    return b""


def multiply(a: bytes, b: bytes) -> bytes:
    """Multiplication homomorphe."""
    return b""
