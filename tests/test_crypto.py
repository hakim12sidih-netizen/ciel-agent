"""
Tests unitaires pour les primitives cryptographiques de CIEL.
"""
from __future__ import annotations

import pytest

from ciel.core import crypto


class TestBlake2b:
    def test_basic_hash(self) -> None:
        h = crypto.blake2b(b"hello")
        assert len(h) == 32
        assert isinstance(h, bytes)

    def test_hash_determinism(self) -> None:
        assert crypto.blake2b(b"x") == crypto.blake2b(b"x")

    def test_different_inputs_different_hashes(self) -> None:
        assert crypto.blake2b(b"a") != crypto.blake2b(b"b")

    def test_custom_digest_size(self) -> None:
        for size in (16, 32, 48, 64):
            h = crypto.blake2b(b"data", digest_size=size)
            assert len(h) == size

    def test_domain_separation(self) -> None:
        # Mêmes données, domains différents = hashes différents
        a = crypto.blake2b(b"x", domain=b"DOMAIN_A")
        b = crypto.blake2b(b"x", domain=b"DOMAIN_B")
        assert a != b

    def test_invalid_digest_size_raises(self) -> None:
        with pytest.raises(ValueError):
            crypto.blake2b(b"x", digest_size=0)
        with pytest.raises(ValueError):
            crypto.blake2b(b"x", digest_size=128)

    def test_invalid_domain_size_raises(self) -> None:
        with pytest.raises(ValueError):
            crypto.blake2b(b"x", domain=b"x" * 17)

    def test_known_vector(self) -> None:
        # BLAKE2b-256("") = 0e5751c026e543b2e8ab2eb06099daa1d1e5df47778f7787faab45cdf12fe3a8
        h = crypto.blake2b(b"")
        assert h.hex() == (
            "0e5751c026e543b2e8ab2eb06099daa1d1e5df47778f7787faab45cdf12fe3a8"
        )


class TestHMAC:
    def test_hmac_basic(self) -> None:
        h = crypto.hmac_blake2b(b"key", b"msg")
        assert len(h) == 32

    def test_hmac_determinism(self) -> None:
        assert crypto.hmac_blake2b(b"k", b"m") == crypto.hmac_blake2b(b"k", b"m")

    def test_hmac_different_keys(self) -> None:
        assert crypto.hmac_blake2b(b"k1", b"m") != crypto.hmac_blake2b(b"k2", b"m")

    def test_hmac_verify(self) -> None:
        h = crypto.hmac_blake2b(b"k", b"m")
        assert crypto.hmac_verify(b"k", b"m", h)
        assert not crypto.hmac_verify(b"k", b"m2", h)
        assert not crypto.hmac_verify(b"k2", b"m", h)

    def test_hmac_empty_key_raises(self) -> None:
        with pytest.raises(ValueError):
            crypto.hmac_blake2b(b"", b"msg")


class TestEd25519:
    def test_keypair_generation(self) -> None:
        priv, pub = crypto.ed25519_keypair()
        assert priv is not None
        assert pub is not None

    def test_sign_and_verify(self) -> None:
        priv, pub = crypto.ed25519_keypair()
        msg = b"ciel axiom alpha"
        sig = crypto.ed25519_sign(priv, msg)
        assert len(sig) == 64
        assert crypto.ed25519_verify(pub, sig, msg)

    def test_verify_tampered_message(self) -> None:
        priv, pub = crypto.ed25519_keypair()
        sig = crypto.ed25519_sign(priv, b"original")
        assert not crypto.ed25519_verify(pub, sig, b"tampered")

    def test_verify_wrong_public_key(self) -> None:
        priv1, _ = crypto.ed25519_keypair()
        _, pub2 = crypto.ed25519_keypair()
        sig = crypto.ed25519_sign(priv1, b"msg")
        assert not crypto.ed25519_verify(pub2, sig, b"msg")

    def test_public_key_from_bytes_roundtrip(self) -> None:
        priv, pub = crypto.ed25519_keypair()
        raw = pub.public_bytes(
            encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.Raw,
            format=__import__("cryptography").hazmat.primitives.serialization.PublicFormat.Raw,
        )
        pub2 = crypto.ed25519_public_from_bytes(raw)
        assert crypto.ed25519_verify(pub2, crypto.ed25519_sign(priv, b"x"), b"x")

    def test_invalid_public_key_size(self) -> None:
        with pytest.raises(ValueError):
            crypto.ed25519_public_from_bytes(b"\x00" * 31)


class TestX25519:
    def test_keypair_generation(self) -> None:
        priv, pub = crypto.x25519_keypair()
        assert priv is not None
        assert pub is not None

    def test_shared_secret_symmetry(self) -> None:
        a_priv, a_pub = crypto.x25519_keypair()
        b_priv, b_pub = crypto.x25519_keypair()
        s_ab = crypto.x25519_exchange(a_priv, b_pub)
        s_ba = crypto.x25519_exchange(b_priv, a_pub)
        assert s_ab == s_ba
        assert len(s_ab) == 32

    def test_different_pairs_different_secrets(self) -> None:
        a_priv, a_pub = crypto.x25519_keypair()
        b_priv, b_pub = crypto.x25519_keypair()
        c_priv, c_pub = crypto.x25519_keypair()
        s_ab = crypto.x25519_exchange(a_priv, b_pub)
        s_ac = crypto.x25519_exchange(a_priv, c_pub)
        assert s_ab != s_ac


class TestHKDF:
    def test_basic_derivation(self) -> None:
        secret = b"\x42" * 32
        key = crypto.hkdf_derive(secret, salt=b"salt", info=b"info", length=32)
        assert len(key) == 32

    def test_determinism(self) -> None:
        secret = b"\x01" * 32
        k1 = crypto.hkdf_derive(secret, salt=b"", info=b"ctx")
        k2 = crypto.hkdf_derive(secret, salt=b"", info=b"ctx")
        assert k1 == k2

    def test_different_info_different_keys(self) -> None:
        secret = b"\x01" * 32
        k1 = crypto.hkdf_derive(secret, salt=b"", info=b"v1")
        k2 = crypto.hkdf_derive(secret, salt=b"", info=b"v2")
        assert k1 != k2

    def test_custom_length(self) -> None:
        secret = b"x" * 32
        for length in (16, 32, 64, 100):
            key = crypto.hkdf_derive(secret, salt=b"", info=b"", length=length)
            assert len(key) == length

    def test_empty_secret_raises(self) -> None:
        with pytest.raises(ValueError):
            crypto.hkdf_derive(b"", salt=b"s", info=b"i")

    def test_invalid_length_raises(self) -> None:
        with pytest.raises(ValueError):
            crypto.hkdf_derive(b"x" * 32, salt=b"", info=b"", length=0)
        with pytest.raises(ValueError):
            crypto.hkdf_derive(b"x" * 32, salt=b"", info=b"", length=10_000)


class TestChaCha20Poly1305:
    def test_encrypt_decrypt(self) -> None:
        key = crypto.random_bytes(32)
        nonce = crypto.new_nonce()
        ct = crypto.aead_encrypt(key, nonce, b"hello CIEL")
        assert ct != b"hello CIEL"
        assert len(ct) == len(b"hello CIEL") + 16  # +16 pour tag
        pt = crypto.aead_decrypt(key, nonce, ct)
        assert pt == b"hello CIEL"

    def test_aad_matters(self) -> None:
        key = crypto.random_bytes(32)
        nonce = crypto.new_nonce()
        ct = crypto.aead_encrypt(key, nonce, b"data", aad=b"v1")
        # Avec mauvais AAD, déchiffrement échoue
        with pytest.raises(Exception):
            crypto.aead_decrypt(key, nonce, ct, aad=b"v2")

    def test_tampered_ciphertext_fails(self) -> None:
        key = crypto.random_bytes(32)
        nonce = crypto.new_nonce()
        ct = crypto.aead_encrypt(key, nonce, b"data")
        tampered = bytes([ct[0] ^ 0x01]) + ct[1:]
        with pytest.raises(Exception):
            crypto.aead_decrypt(key, nonce, tampered)

    def test_invalid_key_size(self) -> None:
        with pytest.raises(ValueError):
            crypto.aead_encrypt(b"x" * 16, crypto.new_nonce(), b"data")
        with pytest.raises(ValueError):
            crypto.aead_decrypt(b"x" * 16, crypto.new_nonce(), b"x" * 32)

    def test_invalid_nonce_size(self) -> None:
        with pytest.raises(ValueError):
            crypto.aead_encrypt(b"x" * 32, b"x" * 8, b"data")
        with pytest.raises(ValueError):
            crypto.aead_decrypt(b"x" * 32, b"x" * 8, b"x" * 16)


class TestSealedBox:
    def test_seal_and_open(self) -> None:
        priv, pub = crypto.x25519_keypair()
        box = crypto.SealedBox(pub)
        message = b"Top secret CIEL message"
        blob = box.easy_seal(message)
        assert blob != message
        # Blob = ephemeral_pub (32) + nonce (12) + ciphertext+tag
        assert len(blob) > 32 + 12
        opened = crypto.open_sealed_box(priv, blob)
        assert opened == message

    def test_seal_uses_fresh_ephemeral_each_time(self) -> None:
        priv, pub = crypto.x25519_keypair()
        box = crypto.SealedBox(pub)
        m = b"same message"
        b1 = box.easy_seal(m)
        b2 = box.easy_seal(m)
        # Les sceaux sont différents (ephemeral_key + nonce frais)
        assert b1 != b2
        # Mais les deux déchiffrent correctement
        assert crypto.open_sealed_box(priv, b1) == m
        assert crypto.open_sealed_box(priv, b2) == m

    def test_sealbox_rejects_tampered_blob(self) -> None:
        priv, pub = crypto.x25519_keypair()
        box = crypto.SealedBox(pub)
        blob = bytearray(box.easy_seal(b"data"))
        blob[20] ^= 0x01  # flip un bit
        with pytest.raises(Exception):
            crypto.open_sealed_box(priv, bytes(blob))

    def test_sealbox_too_short_blob(self) -> None:
        priv, _ = crypto.x25519_keypair()
        with pytest.raises(ValueError):
            crypto.open_sealed_box(priv, b"x" * 10)


class TestRandomBytes:
    def test_random_bytes_length(self) -> None:
        for n in (16, 32, 64, 100):
            data = crypto.random_bytes(n)
            assert len(data) == n

    def test_random_bytes_uniqueness(self) -> None:
        # Très haute probabilité d'unicité sur 32 bytes
        samples = [crypto.random_bytes(32) for _ in range(100)]
        assert len(set(samples)) == 100
