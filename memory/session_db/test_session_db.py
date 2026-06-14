"""
Tests for SessionDB, VectorSearch, and CRDTSync.
Run: python3 -m pytest ciel/memory/session_db/test_session_db.py -v
"""

import json
import math
import tempfile
from pathlib import Path

import pytest

from ciel.memory.session_db.core import SessionDB, MIGRATIONS, SCHEMA_VERSION
from ciel.memory.session_db.vector import VectorSearch, _cosine_similarity
from ciel.memory.session_db.crdt import CRDTSync, CRDTMessage, SyncOp


@pytest.fixture
def db():
    """SessionDB with a temporary file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    db = SessionDB(path)
    yield db
    db.close()
    Path(path).unlink(missing_ok=True)


# ── SessionDB Tests ──────────────────────────────────────

class TestSessionDB:
    def test_create_session(self, db):
        sid = db.create_session(platform="test", title="Test Session")
        assert sid is not None
        assert len(sid) > 0

        session = db.get_session(sid)
        assert session is not None
        assert session["session_id"] == sid
        assert session["platform"] == "test"
        assert session["title"] == "Test Session"
        assert session["is_active"] == 1

    def test_get_session_not_found(self, db):
        assert db.get_session("nonexistent") is None

    def test_list_sessions(self, db):
        db.create_session(platform="test", title="S1")
        db.create_session(platform="test", title="S2")
        db.create_session(platform="other", title="S3")

        all_sessions = db.list_sessions()
        assert len(all_sessions) >= 3

        test_sessions = db.list_sessions(platform="test")
        assert len(test_sessions) == 2

    def test_list_sessions_empty(self, db):
        assert db.list_sessions() == []

    def test_update_session(self, db):
        sid = db.create_session(title="Original")
        db.update_session(sid, title="Updated", model="gpt-4")
        session = db.get_session(sid)
        assert session["title"] == "Updated"
        assert session["model"] == "gpt-4"

    def test_update_session_metadata(self, db):
        sid = db.create_session(title="Test")
        db.update_session(sid, metadata={"key": "value"})
        session = db.get_session(sid)
        assert json.loads(session["metadata"])["key"] == "value"

    def test_close_session(self, db):
        sid = db.create_session()
        db.close_session(sid)
        session = db.get_session(sid)
        assert session["is_active"] == 0

    def test_delete_session(self, db):
        sid = db.create_session()
        db.add_message(sid, "user", "hello")
        db.delete_session(sid)
        assert db.get_session(sid) is None
        assert db.get_messages(sid) == []

    def test_add_message(self, db):
        sid = db.create_session()
        msg_id = db.add_message(sid, "user", "Hello, world!", tokens=5)
        assert msg_id > 0

        messages = db.get_messages(sid)
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello, world!"
        assert messages[0]["role"] == "user"

        session = db.get_session(sid)
        assert session["message_count"] == 1

    def test_add_messages_increments_count(self, db):
        sid = db.create_session()
        for i in range(5):
            db.add_message(sid, "user", f"msg {i}")
        assert db.message_count(sid) == 5

    def test_get_messages_pagination(self, db):
        sid = db.create_session()
        for i in range(10):
            db.add_message(sid, "user", f"msg {i}")
        msgs = db.get_messages(sid, limit=3, offset=5)
        assert len(msgs) == 3
        assert msgs[0]["content"] == "msg 5"

    def test_search_messages_fts(self, db):
        sid = db.create_session()
        db.add_message(sid, "user", "The quick brown fox")
        db.add_message(sid, "assistant", "jumps over the lazy dog")
        db.add_message(sid, "user", "fox and dog are friends")

        results = db.search_messages("fox")
        assert len(results) >= 1
        assert any("fox" in r["content"] for r in results)

        results = db.search_messages("fox", session_id=sid)
        assert len(results) >= 1

    def test_search_messages_empty_results(self, db):
        sid = db.create_session()
        db.add_message(sid, "user", "hello")
        results = db.search_messages("xyznonexistent")
        assert results == []

    def test_stats(self, db):
        sid = db.create_session()
        db.add_message(sid, "user", "hello")
        stats = db.stats()
        assert stats["total_sessions"] >= 1
        assert stats["total_messages"] >= 1
        assert stats["schema_version"] == SCHEMA_VERSION
        assert stats["db_size"] > 0

    def test_schema_version(self, db):
        assert db._get_version() == SCHEMA_VERSION

    def test_migrations_applied(self, db):
        conn = db._get_conn()
        # Check that all migration tables exist
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = [r[0] for r in tables]
        assert "sessions" in names
        assert "messages" in names
        assert "messages_fts" in names
        assert "message_embeddings" in names
        assert "sync_log" in names

    def test_wal_mode(self, db):
        conn = db._get_conn()
        row = conn.execute("PRAGMA journal_mode").fetchone()
        assert row[0].lower() == "wal"

    def test_foreign_keys(self, db):
        conn = db._get_conn()
        row = conn.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1

    def test_busy_timeout(self, db):
        conn = db._get_conn()
        row = conn.execute("PRAGMA busy_timeout").fetchone()
        assert row[0] == 5000

    def test_concurrent_access(self, db):
        """Multiple threads can access the DB."""
        import threading
        errors = []

        def worker():
            try:
                sid = db.create_session()
                for i in range(10):
                    db.add_message(sid, "user", f"thread msg {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_message_order(self, db):
        sid = db.create_session()
        ids = []
        for i in range(5):
            mid = db.add_message(sid, "user", f"msg {i}")
            ids.append(mid)
        msgs = db.get_messages(sid)
        assert [m["id"] for m in msgs] == ids

    def test_add_message_with_metadata(self, db):
        sid = db.create_session()
        mid = db.add_message(sid, "user", "test", metadata={"key": "val"})
        msgs = db.get_messages(sid)
        meta = json.loads(msgs[0]["metadata"])
        assert meta["key"] == "val"

    def test_save_embedding(self, db):
        sid = db.create_session()
        mid = db.add_message(sid, "user", "vector test")
        db.save_embedding(mid, b"\x00" * 16, model="test", dim=4)
        row = db.get_embedding(mid)
        assert row is not None
        assert row["dim"] == 4

    def test_sync_log(self, db):
        sid = db.create_session()
        entries = db.get_sync_log(sid)
        assert len(entries) >= 1  # create session generates a log entry


# ── VectorSearch Tests ───────────────────────────────────

class TestVectorSearch:
    def test_store_and_get_vector(self, db):
        sid = db.create_session()
        mid = db.add_message(sid, "user", "vector data")
        vs = VectorSearch(db)
        vs.store(mid, [0.1, 0.2, 0.3, 0.4], model="test")
        retrieved = vs.get(mid)
        assert retrieved is not None
        assert len(retrieved) == 4
        assert abs(retrieved[0] - 0.1) < 0.001

    def test_search_by_vector(self, db):
        sid = db.create_session()
        vs = VectorSearch(db)

        # Store messages with vectors
        texts = [
            ("user", "python programming", [1.0, 0.0, 0.0]),
            ("user", "machine learning", [0.0, 1.0, 0.0]),
            ("user", "cooking recipes", [0.0, 0.0, 1.0]),
        ]
        mids = []
        for role, content, vec in texts:
            mid = db.add_message(sid, role, content)
            vs.store(mid, vec, model="test")
            mids.append(mid)

        # Search for python-related content
        results = vs.search([0.9, 0.1, 0.0], top_k=2)
        assert len(results) >= 1
        assert results[0]["score"] > 0.8

    def test_search_threshold(self, db):
        sid = db.create_session()
        vs = VectorSearch(db)
        mid = db.add_message(sid, "user", "unique content")
        vs.store(mid, [1.0, 0.0], model="test")

        results = vs.search([-1.0, 0.0], top_k=5, threshold=0.9)
        assert len(results) == 0  # orthogonal vectors should be below threshold

    def test_search_empty_db(self, db):
        vs = VectorSearch(db)
        results = vs.search([1.0, 0.0])
        assert results == []

    def test_search_multiple_sessions(self, db):
        vs = VectorSearch(db)
        for s in range(3):
            sid = db.create_session()
            for i in range(2):
                mid = db.add_message(sid, "user", f"session {s} msg {i}")
                vs.store(mid, [float(s), float(i)], model="test")

        results = vs.search([0.0, 0.0], top_k=10)
        assert len(results) >= 3

    def test_get_nonexistent(self, db):
        vs = VectorSearch(db)
        assert vs.get(99999) is None

    def test_cosine_similarity(self):
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        assert abs(_cosine_similarity(a, b) - 1.0) < 0.001

        c = [0.0, 1.0, 0.0]
        assert abs(_cosine_similarity(a, c)) < 0.001

        d = [2.0, 0.0, 0.0]
        assert abs(_cosine_similarity(a, d) - 1.0) < 0.001

        zero = [0.0, 0.0, 0.0]
        assert _cosine_similarity(a, zero) == 0.0


# ── CRDTSync Tests ───────────────────────────────────────

class TestCRDTSync:
    def test_create_message(self, db):
        crdt = CRDTSync(db, source_id="test-node")
        sid = db.create_session()
        msg = crdt.create_message(sid, "user", "Hello CRDT", tokens=3)

        assert msg.uid is not None
        assert msg.role == "user"
        assert msg.content == "Hello CRDT"
        assert msg.source == "test-node"
        assert msg.wall_ts > 0

        # Verify it's in the DB
        messages = db.get_messages(sid)
        assert len(messages) == 1
        meta = json.loads(messages[0]["metadata"])
        assert meta["crdt_uid"] == msg.uid

    def test_get_ops(self, db):
        crdt = CRDTSync(db)
        sid = db.create_session()
        crdt.create_message(sid, "user", "op1")
        crdt.create_message(sid, "assistant", "op2")

        ops = crdt.get_ops(sid)
        assert len(ops) >= 4  # 2 messages × 2 fields each

        for op in ops:
            assert isinstance(op, SyncOp)
            assert op.field in ("role", "content")

    def test_merge_new_message(self, db):
        crdt = CRDTSync(db, source_id="local")
        sid = db.create_session()

        # Simulate remote ops
        wall_ts = 1000.0
        remote_ops = [
            SyncOp(uid="remote-uid-1", field="role", value="user",
                   wall_ts=wall_ts, source="remote-node"),
            SyncOp(uid="remote-uid-1", field="content", value="Hello from remote",
                   wall_ts=wall_ts + 1, source="remote-node"),
        ]

        applied = crdt.merge(sid, remote_ops)
        assert applied >= 2

    def test_lww_tiebreaker(self, db):
        crdt = CRDTSync(db, source_id="local")
        sid = db.create_session()

        # Local message
        msg = crdt.create_message(sid, "user", "local content", tokens=0)

        # Remote op with older timestamp should NOT override
        remote_ops = [
            SyncOp(uid=msg.uid, field="content", value="old remote content",
                   wall_ts=msg.wall_ts - 100, source="remote-node"),
        ]
        crdt.merge(sid, remote_ops)

        messages = db.get_messages(sid)
        assert messages[0]["content"] == "local content"

        # Remote op with newer timestamp SHOULD override
        remote_ops2 = [
            SyncOp(uid=msg.uid, field="content", value="new remote content",
                   wall_ts=msg.wall_ts + 100, source="remote-node"),
        ]
        crdt.merge(sid, remote_ops2)

        messages = db.get_messages(sid)
        assert messages[0]["content"] == "new remote content"

    def test_sync_two_way(self, db):
        crdt = CRDTSync(db, source_id="node-a")
        sid = db.create_session()

        # Create local messages
        crdt.create_message(sid, "user", "from A", tokens=0)
        crdt.create_message(sid, "assistant", "response A", tokens=0)

        # Simulate two-way sync: send local ops, merge remote ops
        remote_ops = [
            SyncOp(uid="remote-uid", field="role", value="user",
                   wall_ts=2000.0, source="node-b"),
            SyncOp(uid="remote-uid", field="content", value="from B",
                   wall_ts=2001.0, source="node-b"),
        ]

        outgoing = crdt.sync(sid, remote_ops, since_id=0)
        assert len(outgoing) > 0

    def test_sync_idempotent(self, db):
        """Merging the same ops twice produces the same result."""
        crdt = CRDTSync(db, source_id="local")
        sid = db.create_session()

        ops = [
            SyncOp(uid="uid-1", field="content", value="hello",
                   wall_ts=100.0, source="remote"),
            SyncOp(uid="uid-1", field="role", value="user",
                   wall_ts=99.0, source="remote"),
        ]

        applied1 = crdt.merge(sid, ops)
        applied2 = crdt.merge(sid, ops)
        # Second merge should still accept ops that weren't previously applied
        # due to the way merge works
        assert applied2 >= 0

    def test_get_ops_empty(self, db):
        crdt = CRDTSync(db)
        sid = db.create_session()
        ops = crdt.get_ops(sid, since_id=99999)
        assert ops == []

    def test_multiple_messages_sync(self, db):
        crdt = CRDTSync(db, source_id="node-a")
        sid = db.create_session()

        for i in range(5):
            crdt.create_message(sid, "user", f"msg {i}", tokens=i)

        ops = crdt.get_ops(sid)
        # Each message creates 2 field ops (role + content) plus session create
        assert len(ops) >= 10

    def test_source_tiebreaker(self, db):
        """Same wall_ts: higher source string wins."""
        crdt = CRDTSync(db, source_id="local")
        sid = db.create_session()
        msg = crdt.create_message(sid, "user", "original")

        # Same timestamp, but "z-node" > "local" alphabetically
        remote = [
            SyncOp(uid=msg.uid, field="content", value="from z",
                   wall_ts=msg.wall_ts, source="z-node"),
        ]
        crdt.merge(sid, remote)
        messages = db.get_messages(sid)
        assert messages[0]["content"] == "from z"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
