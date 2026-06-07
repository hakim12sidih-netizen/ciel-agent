"""
Tests unitaires pour l'identité CIEL.
"""
from __future__ import annotations

import json
import time

import pytest

from ciel.core.identity import (
    IDENTITY_FILE,
    NOYAU_KEY_FILE,
    PRIVATE_KEY_FILE,
    PUBLIC_KEY_FILE,
    Identity,
    bootstrap,
    demo_identity,
    demo_key,
    exists,
    load,
)


class TestIdentityStructure:
    def test_demo_identity_is_valid(self) -> None:
        i = demo_identity()
        assert len(i.public_key_bytes) == 32
        assert len(i.noyau_key) == 32
        import uuid as _uuid_mod
        u = _uuid_mod.UUID(i.uuid)
        assert u.version == 7
        assert len(i.fingerprint) == 32  # 16 bytes hex

    def test_uuid_is_v7(self) -> None:
        import uuid
        i = demo_identity()
        u = uuid.UUID(i.uuid)
        assert u.version == 7

    def test_identity_is_immutable(self) -> None:
        i = demo_identity()
        with pytest.raises(Exception):  # FrozenInstanceError
            i.uuid = "hacked"  # type: ignore[misc]

    def test_short_fingerprint(self) -> None:
        i = demo_identity()
        assert len(i.public_fingerprint()) == 16


class TestIdentityBootstrap:
    def test_bootstrap_creates_files(self, identity_dir) -> None:
        assert not exists(identity_dir)
        bootstrap(identity_dir)
        assert (identity_dir / IDENTITY_FILE).exists()
        assert (identity_dir / NOYAU_KEY_FILE).exists()
        assert (identity_dir / PRIVATE_KEY_FILE).exists()
        assert (identity_dir / PUBLIC_KEY_FILE).exists()

    def test_bootstrap_creates_valid_identity(self, identity_dir) -> None:
        i = bootstrap(identity_dir)
        assert len(i.uuid) == 36  # standard UUID
        assert len(i.public_key_bytes) == 32
        assert len(i.noyau_key) == 32

    def test_bootstrap_fails_if_exists(self, identity_dir) -> None:
        bootstrap(identity_dir)
        with pytest.raises(FileExistsError):
            bootstrap(identity_dir)

    def test_noyau_key_file_is_600(self, identity_dir) -> None:
        import stat
        bootstrap(identity_dir)
        f = identity_dir / NOYAU_KEY_FILE
        mode = f.stat().st_mode
        # Sur Linux, les 9 derniers bits sont rwx pour owner/group/other
        perms = mode & 0o777
        # 0o600 = rw pour owner seulement
        assert perms == 0o600, f"attendu 0o600, reçu {oct(perms)}"

    def test_private_key_file_is_600(self, identity_dir) -> None:
        bootstrap(identity_dir)
        f = identity_dir / PRIVATE_KEY_FILE
        perms = f.stat().st_mode & 0o777
        assert perms == 0o600, f"attendu 0o600, reçu {oct(perms)}"


class TestIdentityLoad:
    def test_load_after_bootstrap(self, identity_dir) -> None:
        i1 = bootstrap(identity_dir)
        i2 = load(identity_dir)
        assert i1.uuid == i2.uuid
        assert i1.public_key_bytes == i2.public_key_bytes
        assert i1.fingerprint == i2.fingerprint
        # noyau_key n'est PAS sérialisé publiquement mais doit être rechargé
        assert i1.noyau_key == i2.noyau_key

    def test_load_fails_if_missing(self, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            load(tmp_path / "nope")

    def test_load_fails_on_incomplete(self, identity_dir) -> None:
        bootstrap(identity_dir)
        (identity_dir / NOYAU_KEY_FILE).unlink()
        with pytest.raises(FileNotFoundError):
            load(identity_dir)

    def test_load_validates_fingerprint(self, identity_dir) -> None:
        bootstrap(identity_dir)
        # Corrompt le fichier JSON (mauvais fingerprint)
        data = json.loads((identity_dir / IDENTITY_FILE).read_text())
        data["fingerprint"] = "0" * 32
        (identity_dir / IDENTITY_FILE).write_text(json.dumps(data))
        with pytest.raises(ValueError, match="fingerprint incohérent"):
            load(identity_dir)

    def test_load_validates_noyau_size(self, identity_dir) -> None:
        bootstrap(identity_dir)
        (identity_dir / NOYAU_KEY_FILE).write_bytes(b"x" * 10)  # trop court
        with pytest.raises(ValueError, match="noyau_key corrompue"):
            load(identity_dir)


class TestIdentitySignatures:
    def test_sign_and_verify(self) -> None:
        i = demo_identity()
        msg = "CIEL axiom α signed by Manas:Ciel".encode("utf-8")
        sig = i.sign(msg)
        assert len(sig) == 32
        assert i.verify_signature(msg, sig)
        assert not i.verify_signature(b"tampered", sig)

    def test_signature_is_deterministic(self) -> None:
        i = demo_identity()
        msg = b"deterministic test"
        s1 = i.sign(msg)
        s2 = i.sign(msg)
        assert s1 == s2  # HMAC est déterministe

    def test_different_keys_different_signatures(self) -> None:
        i1 = demo_identity()
        i2 = demo_identity()
        # demo_identity() retourne la même (déterministe) — utilisons 2 noyaux
        from ciel.core.identity import _generate_noyau_key, _fallback_uuid7
        import time
        ts = int(time.time() * 1000)
        i1 = Identity(
            uuid=_fallback_uuid7(ts),
            public_key_bytes=i1.public_key_bytes,
            public_key_hex=i1.public_key_hex,
            fingerprint=i1.fingerprint,
            created_at=1718000000,
            noyau_key=_generate_noyau_key(),
        )
        msg = b"different keys test"
        assert i1.sign(msg) != i2.sign(msg)  # noyaux différents

    def test_public_key_obj_roundtrip(self) -> None:
        i = demo_identity()
        obj = i.public_key_obj()
        raw = obj.public_bytes(
            encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.Raw,
            format=__import__("cryptography").hazmat.primitives.serialization.PublicFormat.Raw,
        )
        assert raw == i.public_key_bytes


class TestIdentityExists:
    def test_exists_false_on_empty(self, identity_dir) -> None:
        assert not exists(identity_dir)

    def test_exists_true_after_bootstrap(self, identity_dir) -> None:
        bootstrap(identity_dir)
        assert exists(identity_dir)
