"""
CIEL v∞.2 — Crypto : primitives cryptographiques standard.

Fournit :
  - BLAKE2b-256 (hash rapide, ~1 GB/s sur CPU moderne)
  - BLAKE2b variable digest (16, 32, 64 bytes)
  - Ed25519 (signature 64 bytes, vérification 128 bits sécurité)
  - X25519 (échange de clés ECDH, forward secrecy)
  - ChaCha20-Poly1305 (AEAD symétrique, 256 bits clé)
  - HKDF-SHA256 (dérivation de clés)
  - HMAC-BLAKE2b (intégrité symétrique)
  - Argon2id (KDF pour mots de passe) via hashlib.scrypt en fallback

Ces primitives sont utilisées par :
  - Strate 1 (NOYAU) : Ed25519 pour signer les axiomes
  - Strate 3 (IMMUNE) : ChaCha20-Poly1305 pour chiffrer snapshots
  - Strate 17 (SWARM) : X25519 pour handshake instances
  - Strate 18 (SECURITY) : HKDF pour dériver clés de session
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from typing import Final

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# ── Constantes ────────────────────────────────────────────
HASH_SIZE: Final[int] = 32  # BLAKE2b-256
NONCE_SIZE: Final[int] = 12  # ChaCha20-Poly1305
KEY_SIZE: Final[int] = 32  # 256 bits
SIGNATURE_SIZE: Final[int] = 64  # Ed25519

# Domaines de séparation (person parameter de BLAKE2b)
DOMAIN_AXIOM: Final[bytes] = b"CIELAXIOM\x00"
DOMAIN_SKILL: Final[bytes] = b"CIELSKILL\x00"
DOMAIN_SNAP: Final[bytes] = b"CIELSNAP\x00"
DOMAIN_SESS: Final[bytes] = b"CIELSESS\x00"


# ═══════════════════════════════════════════════════════════
# HASH
# ═══════════════════════════════════════════════════════════

def blake2b(data: bytes, digest_size: int = HASH_SIZE, domain: bytes | None = None) -> bytes:
    """Hash BLAKE2b avec domain separation optionnel.

    Args:
        data: données à hasher
        digest_size: taille du digest (16, 32, 48, 64 — max 64 pour BLAKE2b)
        domain: bytes de séparation (max 16)

    Returns:
        bytes du digest
    """
    if digest_size < 1 or digest_size > 64:
        raise ValueError(f"digest_size doit être entre 1 et 64, reçu {digest_size}")
    if domain is not None and len(domain) > 16:
        raise ValueError(f"domain doit faire <= 16 bytes, reçu {len(domain)}")
    if domain is not None:
        return hashlib.blake2b(data, digest_size=digest_size, person=domain).digest()
    return hashlib.blake2b(data, digest_size=digest_size).digest()


def sha256(data: bytes) -> bytes:
    """SHA-256 standard (pour interop avec écosystème existant)."""
    return hashlib.sha256(data).digest()


def sha3_256(data: bytes) -> bytes:
    """SHA3-256 (post-quantique ready, NIST standard)."""
    return hashlib.sha3_256(data).digest()


# ═══════════════════════════════════════════════════════════
# HMAC (intégrité symétrique)
# ═══════════════════════════════════════════════════════════

def hmac_blake2b(key: bytes, message: bytes) -> bytes:
    """HMAC-BLAKE2b pour intégrité symétrique (32 bytes)."""
    if not key:
        raise ValueError("key ne peut pas être vide")
    # Utiliser BLAKE2b avec digest_size=32 pour obtenir un HMAC de 32 bytes
    return hmac.new(key, message, lambda: hashlib.blake2b(digest_size=32)).digest()


def hmac_verify(key: bytes, message: bytes, expected: bytes) -> bool:
    """Vérifie un HMAC en temps constant (résistant timing attacks)."""
    actual = hmac_blake2b(key, message)
    return hmac.compare_digest(actual, expected)


# ═══════════════════════════════════════════════════════════
# Ed25519 (signature)
# ═══════════════════════════════════════════════════════════

def ed25519_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Génère une paire Ed25519 (32 bytes priv, 32 bytes pub)."""
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def ed25519_sign(private_key: Ed25519PrivateKey, message: bytes) -> bytes:
    """Signe un message (signature 64 bytes)."""
    return private_key.sign(message)


def ed25519_verify(public_key: Ed25519PublicKey, signature: bytes, message: bytes) -> bool:
    """Vérifie une signature. Retourne False si invalide (pas d'exception)."""
    try:
        public_key.verify(signature, message)
        return True
    except Exception:
        return False


def ed25519_public_from_bytes(raw: bytes) -> Ed25519PublicKey:
    """Reconstruit une clé publique depuis 32 bytes raw."""
    if len(raw) != 32:
        raise ValueError(f"Ed25519 public key doit faire 32 bytes, reçu {len(raw)}")
    return Ed25519PublicKey.from_public_bytes(raw)


def ed25519_private_from_bytes(raw: bytes) -> Ed25519PrivateKey:
    """Reconstruit une clé privée depuis 32 bytes raw."""
    if len(raw) != 32:
        raise ValueError(f"Ed25519 private key doit faire 32 bytes, reçu {len(raw)}")
    return Ed25519PrivateKey.from_private_bytes(raw)


# ═══════════════════════════════════════════════════════════
# X25519 (échange de clés)
# ═══════════════════════════════════════════════════════════

def x25519_keypair() -> tuple[X25519PrivateKey, X25519PublicKey]:
    """Génère une paire X25519 (32 bytes priv, 32 bytes pub)."""
    priv = X25519PrivateKey.generate()
    return priv, priv.public_key()


def x25519_exchange(
    my_private: X25519PrivateKey, their_public: X25519PublicKey
) -> bytes:
    """Calcule le secret partagé ECDH (32 bytes)."""
    return my_private.exchange(their_public)


# ═══════════════════════════════════════════════════════════
# HKDF (dérivation de clés)
# ═══════════════════════════════════════════════════════════

def hkdf_derive(
    secret: bytes,
    salt: bytes,
    info: bytes,
    length: int = KEY_SIZE,
) -> bytes:
    """Dérive `length` bytes de clés depuis un secret IKM.

    Args:
        secret: Input Key Material (ex: secret ECDH)
        salt: sel (peut être vide)
        info: contexte d'utilisation (max 1024 bytes)
        length: nombre de bytes à dériver

    Returns:
        bytes de longueur `length`
    """
    if not secret:
        raise ValueError("secret ne peut pas être vide")
    if length < 1 or length > 255 * 32:
        raise ValueError(f"length doit être entre 1 et 8160, reçu {length}")
    kdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt if salt else None,
        info=info,
    )
    return kdf.derive(secret)


# ═══════════════════════════════════════════════════════════
# ChaCha20-Poly1305 (chiffrement authentifié)
# ═══════════════════════════════════════════════════════════

def aead_encrypt(key: bytes, nonce: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    """Chiffre avec ChaCha20-Poly1305 (AEAD).

    Format de sortie : ciphertext || tag (16 bytes)
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"key doit faire {KEY_SIZE} bytes, reçu {len(key)}")
    if len(nonce) != NONCE_SIZE:
        raise ValueError(f"nonce doit faire {NONCE_SIZE} bytes, reçu {len(nonce)}")
    cipher = ChaCha20Poly1305(key)
    return cipher.encrypt(nonce, plaintext, aad)


def aead_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes = b"") -> bytes:
    """Déchiffre avec ChaCha20-Poly1305.

    Raises:
        cryptography.exceptions.InvalidTag: si tag invalide
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"key doit faire {KEY_SIZE} bytes, reçu {len(key)}")
    if len(nonce) != NONCE_SIZE:
        raise ValueError(f"nonce doit faire {NONCE_SIZE} bytes, reçu {len(nonce)}")
    cipher = ChaCha20Poly1305(key)
    return cipher.decrypt(nonce, ciphertext, aad)


def new_nonce() -> bytes:
    """Génère un nonce aléatoire (12 bytes). À utiliser UNE fois par clé."""
    return os.urandom(NONCE_SIZE)


# ═══════════════════════════════════════════════════════════
# Utilitaires haut-niveau
# ═══════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class SealedBox:
    """Boîte scellée : chiffre un message pour un destinataire (X25519+ChaCha20).

    Pattern : ephemeral_keypair → ECDH → HKDF → ChaCha20-Poly1305
    """

    recipient_public: X25519PublicKey

    def seal(self, plaintext: bytes, aad: bytes = b"") -> tuple[bytes, bytes, bytes]:
        """Chiffre pour le destinataire.

        Returns:
            (ephemeral_public_raw, nonce, ciphertext_with_tag)
        """
        eph_priv, eph_pub = x25519_keypair()
        shared = x25519_exchange(eph_priv, self.recipient_public)
        key = hkdf_derive(shared, salt=b"", info=b"ciel-sealbox-v1", length=KEY_SIZE)
        nonce = new_nonce()
        ct = aead_encrypt(key, nonce, plaintext, aad)
        eph_raw = eph_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return eph_raw, nonce, ct

    def easy_seal(self, plaintext: bytes) -> bytes:
        """Sérialise ephemeral_pub || nonce || ciphertext en un seul blob."""
        eph, nonce, ct = self.seal(plaintext)
        return eph + nonce + ct


def open_sealed_box(
    recipient_private: X25519PrivateKey, blob: bytes, aad: bytes = b""
) -> bytes:
    """Ouvre une SealedBox (côté destinataire)."""
    if len(blob) < 32 + 12 + 16:
        raise ValueError("blob trop court pour SealedBox")
    eph_raw = blob[:32]
    nonce = blob[32:44]
    ct = blob[44:]
    eph_pub = X25519PublicKey.from_public_bytes(eph_raw)
    shared = x25519_exchange(recipient_private, eph_pub)
    key = hkdf_derive(shared, salt=b"", info=b"ciel-sealbox-v1", length=KEY_SIZE)
    return aead_decrypt(key, nonce, ct, aad)


# ── Test helpers ──────────────────────────────────────────

def random_bytes(n: int) -> bytes:
    """n bytes aléatoires cryptographiquement sûrs."""
    return secrets.token_bytes(n)
