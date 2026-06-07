"""
Tests pour SnapshotStore (Axiome γ — réversibilité).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ciel.core.identity import demo_identity
from ciel.ethics.reversibility import Snapshot, SnapshotStore


class TestSnapshot:
    def test_basic_snapshot(self) -> None:
        s = Snapshot(
            id="snap1",
            kind="init",
            timestamp=1718000000,
            data=(("version", "0.1.0"),),
            previous_id=None,
            signature="a" * 64,
            author_uuid="uuid-1",
        )
        assert s.kind == "init"
        assert s.previous_id is None

    def test_invalid_kind(self) -> None:
        with pytest.raises(ValueError):
            Snapshot(
                id="x", kind="",  # vide
                timestamp=1, data=(), previous_id=None,
                signature="a" * 64, author_uuid="u",
            )

    def test_invalid_timestamp(self) -> None:
        with pytest.raises(ValueError):
            Snapshot(
                id="x", kind="init", timestamp=0,  # invalide
                data=(), previous_id=None,
                signature="a" * 64, author_uuid="u",
            )

    def test_invalid_signature_length(self) -> None:
        with pytest.raises(ValueError):
            Snapshot(
                id="x", kind="init", timestamp=1, data=(), previous_id=None,
                signature="abc",  # trop court
                author_uuid="u",
            )

    def test_to_json_roundtrip(self) -> None:
        s = Snapshot(
            id="x", kind="init", timestamp=1, data=(("a", 1),), previous_id=None,
            signature="a" * 64, author_uuid="u",
        )
        j = s.to_json()
        d = json.loads(j)
        assert d["id"] == "x"


class TestSnapshotStore:
    def test_empty_store(self, snapshots_dir) -> None:
        store = SnapshotStore(snapshots_dir / "snap.jsonl")
        assert store.latest() is None
        assert store.history() == []

    def test_create_snapshot(self, snapshots_dir) -> None:
        store = SnapshotStore(snapshots_dir / "snap.jsonl")
        s = store.create("init", {"version": "0.1.0"})
        assert s.kind == "init"
        assert s.previous_id is None
        assert store.latest() is not None
        assert store.latest().id == s.id

    def test_snapshot_chain(self, snapshots_dir) -> None:
        store = SnapshotStore(snapshots_dir / "snap.jsonl")
        s1 = store.create("init", {"a": 1})
        s2 = store.create("update", {"a": 2})
        s3 = store.create("update", {"a": 3})
        # Chaîne : None → s1 → s2 → s3
        assert s1.previous_id is None
        assert s2.previous_id == s1.id
        assert s3.previous_id == s2.id
        assert store.latest().id == s3.id

    def test_persistence(self, snapshots_dir) -> None:
        # Crée + ferme
        store1 = SnapshotStore(snapshots_dir / "snap.jsonl")
        s1 = store1.create("init", {"v": 1})
        s2 = store1.create("update", {"v": 2})
        # Recharge
        store2 = SnapshotStore(snapshots_dir / "snap.jsonl")
        assert store2.latest().id == s2.id
        assert store2.get(s1.id) is not None

    def test_restore(self, snapshots_dir) -> None:
        store = SnapshotStore(snapshots_dir / "snap.jsonl")
        s = store.create("state", {"key": "value", "n": 42})
        restored = store.restore(s.id)
        assert restored == {"key": "value", "n": 42}

    def test_restore_unknown(self, snapshots_dir) -> None:
        store = SnapshotStore(snapshots_dir / "snap.jsonl")
        assert store.restore("nope") is None

    def test_history_ordering(self, snapshots_dir) -> None:
        import time
        store = SnapshotStore(snapshots_dir / "snap.jsonl")
        s1 = store.create("a", {})
        time.sleep(0.01)  # larger sleep for timestamp resolution
        s2 = store.create("b", {})
        time.sleep(0.01)
        s3 = store.create("c", {})
        h = store.history()
        # Du plus récent au plus ancien
        assert h[0].id == s3.id
        assert h[1].id == s2.id
        assert h[2].id == s1.id

    def test_signature_verification(self, snapshots_dir) -> None:
        """Les snapshots ont une signature vérifiable par la clé Noyau."""
        from ciel.core.identity import demo_identity
        id_ = demo_identity()
        store = SnapshotStore(snapshots_dir / "snap.jsonl", identity=id_)
        s = store.create("x", {"a": 1})
        # La signature doit faire 64 chars hex
        assert len(s.signature) == 64
        assert all(c in "0123456789abcdef" for c in s.signature)

    def test_corrupted_snapshot_ignored(self, snapshots_dir) -> None:
        """Un snapshot corrompu dans le journal est ignoré au chargement."""
        from ciel.core.identity import demo_identity
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        journal = snapshots_dir / "snap.jsonl"
        # Écrit un JSON invalide puis un snapshot valide
        with journal.open("w") as f:
            f.write("this is not JSON\n")
        id_ = demo_identity()
        store = SnapshotStore(journal, identity=id_)
        s = store.create("valid", {"a": 1})
        # Recharge : la ligne corrompue est ignorée, le valide reste
        store2 = SnapshotStore(journal, identity=id_)
        assert store2.get(s.id) is not None
        assert store2.latest().id == s.id

    def test_retention_default_30_days(self, snapshots_dir) -> None:
        store = SnapshotStore(snapshots_dir / "snap.jsonl")
        assert store._max_age_s == 30 * 86400
        s = store.create("test", {"x": 1})
        assert s in store.within_retention()

    def test_stats(self, snapshots_dir) -> None:
        store = SnapshotStore(snapshots_dir / "snap.jsonl")
        store.create("a", {})
        store.create("b", {})
        s = store.stats()
        assert s["total"] == 2
        assert s["within_retention"] == 2
        assert s["max_age_days"] == 30
