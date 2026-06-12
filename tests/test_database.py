"""Tests for CIEL DatabaseEngine — persistence layer."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from ciel.database.core import DatabaseEngine, TableDef, Query


@pytest.fixture
def db():
    tmp = tempfile.mktemp(suffix=".db")
    engine = DatabaseEngine(db_path=tmp)
    engine.register_table(TableDef(
        name="test_table",
        columns={"id": "TEXT", "name": "TEXT", "value": "REAL",
                 "created_at": "REAL", "updated_at": "REAL"},
        primary_key="id",
        indexes=["name"],
    ))
    yield engine
    try:
        os.remove(tmp)
    except OSError:
        pass
    for f in [Path(tmp).parent / "test_table.json"]:
        if f.exists():
            f.unlink()


class TestDatabaseEngine:
    def test_init(self, db):
        assert db.initialized is False

    def test_initialize_creates_db_file(self, db):
        r = db.initialize()
        assert r["status"] == "ok"
        assert Path(db.db_path).exists()

    def test_reinitialize_is_idempotent(self, db):
        db.initialize()
        r = db.initialize()
        assert r["status"] == "already_initialized"

    def test_insert_generates_id(self, db):
        db.initialize()
        r = db.insert("test_table", {"name": "hello", "value": 42.0})
        assert r["status"] == "ok"
        assert r["id"].startswith("ROW-")

    def test_insert_with_custom_id(self, db):
        db.initialize()
        r = db.insert("test_table", {"id": "my-custom-id", "name": "custom",
                                      "value": 1.0})
        assert r["status"] == "ok"
        assert r["id"] == "my-custom-id"

    def test_insert_unknown_table(self, db):
        db.initialize()
        r = db.insert("ghost", {"x": 1})
        assert r["status"] == "error"

    def test_query_all(self, db):
        db.initialize()
        db.insert("test_table", {"name": "a", "value": 1.0})
        db.insert("test_table", {"name": "b", "value": 2.0})
        results = db.query(Query(table="test_table", limit=100))
        assert len(results) == 2

    def test_query_with_filter(self, db):
        db.initialize()
        db.insert("test_table", {"name": "target", "value": 99.0})
        db.insert("test_table", {"name": "other", "value": 1.0})
        results = db.query(Query(table="test_table",
                                 filters={"name": "target"}))
        assert len(results) == 1
        assert results[0]["value"] == 99.0

    def test_update(self, db):
        db.initialize()
        r = db.insert("test_table", {"name": "old", "value": 0.0})
        row_id = r["id"]
        db.update("test_table", row_id, {"value": 100.0})
        results = db.query(Query(table="test_table", filters={"id": row_id}))
        assert results[0]["value"] == 100.0

    def test_delete(self, db):
        db.initialize()
        r = db.insert("test_table", {"name": "gone", "value": 1.0})
        row_id = r["id"]
        db.delete("test_table", row_id)
        results = db.query(Query(table="test_table", filters={"id": row_id}))
        assert len(results) == 0

    def test_export_json(self, db):
        db.initialize()
        db.insert("test_table", {"name": "x", "value": 1.0})
        db.insert("test_table", {"name": "y", "value": 2.0})
        rows = db.export_json("test_table")
        assert len(rows) == 2

    def test_import_json(self, db):
        db.initialize()
        rows = [{"name": "imported1", "value": 10.0},
                {"name": "imported2", "value": 20.0}]
        r = db.import_json("test_table", rows)
        assert r["imported"] == 2
        results = db.query(Query(table="test_table", limit=100))
        assert len(results) == 2

    def test_register_table_duplicate(self, db):
        msg = db.register_table(TableDef(
            name="test_table", columns={"id": "TEXT"}))
        assert "already registered" in msg

    def test_process_initialize(self, db):
        r = db.process({"action": "initialize"})
        assert r["status"] == "ok"

    def test_process_insert(self, db):
        db.initialize()
        r = db.process({"action": "insert",
                        "table": "test_table",
                        "data": {"name": "proc", "value": 7.0}})
        assert r["status"] == "ok"

    def test_process_query(self, db):
        db.initialize()
        db.insert("test_table", {"name": "q", "value": 3.0})
        r = db.process({"action": "query",
                        "query": {"table": "test_table",
                                  "filters": {"name": "q"}}})
        assert r["status"] == "ok"
        assert len(r["result"]) == 1

    def test_process_update(self, db):
        db.initialize()
        r = db.insert("test_table", {"name": "u", "value": 0.0})
        r2 = db.process({"action": "update",
                         "table": "test_table",
                         "id": r["id"],
                         "data": {"value": 999.0}})
        assert r2["status"] == "ok"

    def test_process_delete(self, db):
        db.initialize()
        r = db.insert("test_table", {"name": "d", "value": 0.0})
        r2 = db.process({"action": "delete",
                         "table": "test_table",
                         "id": r["id"]})
        assert r2["status"] == "ok"

    def test_process_export(self, db):
        db.initialize()
        db.insert("test_table", {"name": "e", "value": 1.0})
        r = db.process({"action": "export", "table": "test_table"})
        assert r["status"] == "ok"

    def test_process_stats(self, db):
        r = db.process({})
        assert "tables" in r

    def test_get_stats(self, db):
        stats = db.get_stats()
        assert "test_table" in stats["tables"]

    def test_json_fallback_when_no_sqlite(self):
        """Without aiosqlite, initialize reports error but insert uses JSON."""
        tmp = tempfile.mktemp(suffix=".db")
        engine = DatabaseEngine(db_path=tmp)
        engine.register_table(TableDef(
            name="test_table",
            columns={"id": "TEXT", "name": "TEXT", "value": "REAL",
                     "created_at": "REAL", "updated_at": "REAL"},
            primary_key="id",
            indexes=["name"],
        ))
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "aiosqlite":
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        builtins.__import__ = mock_import
        try:
            r = engine.initialize()
            # SQLite not available, but engine continues in degraded mode
            assert r["status"] == "error"
            assert "aiosqlite" in r.get("error", "")
            # JSON fallback should work for writes
            r2 = engine.insert("test_table", {"name": "json_test", "value": 1.0})
            assert r2["status"] == "ok"
            assert r2.get("mode") == "json"
        finally:
            builtins.__import__ = original_import
        try:
            os.remove(tmp)
        except OSError:
            pass

    def test_migrate_add_column(self, db):
        db.initialize()
        r = db.migrate([{"action": "add_column",
                         "table": "test_table",
                         "column": "new_col TEXT"}])
        assert r["status"] == "ok"

    def test_empty_table_query(self, db):
        db.initialize()
        results = db.query(Query(table="test_table"))
        assert results == []
