"""
Smoke tests : test E2E minimal du pipeline CIEL.

Vérifie que tous les composants interagissent correctement :
  - Identity bootstrap
  - Axioms signés et vérifiés
  - Kernel tick
  - EthicsFilter validation + record
  - Transparency certificate
  - Snapshot persistence
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from ciel.core import crypto
from ciel.core.axioms import get_axioms, load_axioms
from ciel.core.identity import (
    bootstrap as bootstrap_identity,
    demo_identity,
    load as load_identity,
)
from ciel.core.kernel import Kernel, KernelConfig, KernelState
from ciel.ethics.axioms_guard import AlphaViolation
from ciel.ethics.filter import EthicsFilter, new_action
from ciel.ethics.reversibility import SnapshotStore
from ciel.ethics.transparency import global_log


class TestSmokeE2E:
    def test_axioms_loaded(self) -> None:
        """Les 4 axiomes sont chargés."""
        axioms = get_axioms()
        assert set(axioms.keys()) == {"α", "β", "γ", "δ"}

    def test_full_lifecycle(self, tmp_ciel_root: Path) -> None:
        """Cycle de vie complet : identité + axiomes + kernel + filter + snapshot."""
        # 1. Identité
        identity = bootstrap_identity(tmp_ciel_root / "data" / "identity")
        assert identity.uuid

        # 2. Axiomes signés
        axioms = load_axioms(identity.noyau_key)
        assert len(axioms) == 4

        # 3. Kernel tick
        async def tick() -> None:
            k = Kernel(
                root=tmp_ciel_root,
                identity_dir=tmp_ciel_root / "data" / "identity",
                config=KernelConfig(tick_interval_ms=20, max_ticks=3),
            )
            async with k:
                ticks = []
                async for t in k.run():
                    ticks.append(t)
                assert len(ticks) == 3
                assert k.tick_count == 3

        asyncio.run(tick())

        # 4. Filter : valider une action sûre
        f = EthicsFilter()
        a = new_action("read_file", "data.txt", risk=0.1)
        f.validate(a)
        rec = f.record(a, snapshot={"file": "data.txt"})
        assert rec.status == "success"

        # 5. Filter : bloquer une action nuisible
        bad = new_action("harm_user", "alice", risk=0.5)
        with pytest.raises(AlphaViolation):
            f.validate(bad)

        # 6. Transparency : certifier les actions
        log = global_log()
        cert = log.certify(
            action_id=a.id,
            action_category="read_file",
            axioms_consulted=["α", "β"],
            skills_used=["read_file"],
            confidence=0.95,
            identity=identity,
        )
        assert len(cert.signature) == 64
        assert cert.signatory_uuid == identity.uuid

        # 7. Snapshot : persister
        store = SnapshotStore(
            tmp_ciel_root / "data" / "snapshots" / "snap.jsonl",
            identity=identity,
        )
        s1 = store.create("init", {"axioms": 4, "kernel_ticks": 3})
        s2 = store.create("post_validation", {"actions": 1, "blocked": 1})
        assert s2.previous_id == s1.id
        assert store.restore(s1.id) == {"axioms": 4, "kernel_ticks": 3}

    def test_crypto_round_trip(self) -> None:
        """Sign + verify + encrypt + decrypt."""
        # Ed25519
        priv, pub = crypto.ed25519_keypair()
        sig = crypto.ed25519_sign(priv, "CIEL axiom α".encode("utf-8"))
        assert crypto.ed25519_verify(pub, sig, "CIEL axiom α".encode("utf-8"))

        # X25519 + ChaCha20-Poly1305
        a_priv, a_pub = crypto.x25519_keypair()
        b_priv, b_pub = crypto.x25519_keypair()
        shared = crypto.x25519_exchange(a_priv, b_pub)
        key = crypto.hkdf_derive(shared, salt=b"", info=b"test", length=32)
        nonce = crypto.new_nonce()
        ct = crypto.aead_encrypt(key, nonce, b"secret CIEL data")
        pt = crypto.aead_decrypt(key, nonce, ct)
        assert pt == b"secret CIEL data"

    def test_persistence_round_trip(self, tmp_ciel_root: Path) -> None:
        """Identité + snapshot survivent à un rechargement."""
        # Premier cycle
        i1 = bootstrap_identity(tmp_ciel_root / "data" / "identity")
        s = SnapshotStore(
            tmp_ciel_root / "data" / "snapshots" / "snap.jsonl",
            identity=i1,
        )
        s1 = s.create("init", {"v": "0.1.0"})

        # Recharge
        i2 = load_identity(tmp_ciel_root / "data" / "identity")
        s2 = SnapshotStore(
            tmp_ciel_root / "data" / "snapshots" / "snap.jsonl",
            identity=i2,
        )
        assert s2.get(s1.id) is not None
        assert i2.uuid == i1.uuid


class TestSmokeCLI:
    def test_main_help(self, capsys) -> None:
        """main.py --help s'exécute."""
        import subprocess
        import sys
        r = subprocess.run(
            [sys.executable, "main.py", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True, text=True, timeout=5,
        )
        assert r.returncode == 0
        assert "CIEL" in r.stdout

    def test_main_version(self) -> None:
        """main.py version affiche la version."""
        import subprocess
        import sys
        r = subprocess.run(
            [sys.executable, "main.py", "version"],
            cwd=Path(__file__).parent.parent,
            capture_output=True, text=True, timeout=5,
        )
        assert r.returncode == 0
        assert "0.1.0" in r.stdout
        assert "ÉVEIL" in r.stdout

    def test_main_axioms(self) -> None:
        """main.py axioms affiche les 4 axiomes."""
        import subprocess
        import sys
        r = subprocess.run(
            [sys.executable, "main.py", "axioms"],
            cwd=Path(__file__).parent.parent,
            capture_output=True, text=True, timeout=5,
        )
        assert r.returncode == 0
        assert "Axiome α" in r.stdout
        assert "Axiome β" in r.stdout
        assert "Axiome γ" in r.stdout
        assert "Axiome δ" in r.stdout
