"""
CIEL v∞.8 — DATABASE ENGINE. Full persistence layer via aiosqlite.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


class DatabaseError(Exception):
    pass


@dataclass
class TableDef:
    name: str
    columns: dict[str, str]
    primary_key: str = "id"
    indexes: list[str] = field(default_factory=list)


@dataclass
class Query:
    table: str
    filters: dict[str, Any] = field(default_factory=dict)
    order_by: str | None = None
    limit: int = 100
    offset: int = 0


class DatabaseEngine:
    """Moteur de persistance via aiosqlite.

    Gère création de tables, CRUD, migrations simples et
    export/import JSON. Fonctionne en mode synchrone avec
    un fichier SQLite unique.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(Path.home() / ".ciel" / "ciel.db")
        self._tables: dict[str, TableDef] = {}
        self._conn: Any = None
        self._initialized = False
        self.network = LeaderNetwork()

    @property
    def initialized(self) -> bool:
        return self._initialized

    def _ensure_db_dir(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def register_table(self, table: TableDef) -> str:
        if table.name in self._tables:
            return f"table '{table.name}' already registered"
        self._tables[table.name] = table
        if self._initialized and self._conn:
            self._create_table(table)
        return f"registered '{table.name}'"

    def initialize(self) -> dict:
        if self._initialized:
            return {"status": "already_initialized"}
        self._ensure_db_dir()
        try:
            import aiosqlite
        except ImportError:
            return {"status": "error", "error": "aiosqlite not available, using JSON fallback"}

        try:
            import sqlite3
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        except Exception as e:
            return {"status": "error", "error": str(e)}

        for table in self._tables.values():
            self._create_table(table)

        self._initialized = True
        return {"status": "ok", "tables": len(self._tables), "path": self.db_path}

    def _create_table(self, table: TableDef):
        if not self._conn:
            return
        cols = ", ".join(f"{k} {v}" for k, v in table.columns.items())
        pk = f"PRIMARY KEY ({table.primary_key})"
        sql = f"CREATE TABLE IF NOT EXISTS {table.name} ({cols}, {pk})"
        self._conn.execute(sql)
        for idx_col in table.indexes:
            try:
                self._conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table.name}_{idx_col} ON {table.name}({idx_col})")
            except Exception:
                pass
        self._conn.commit()

    def insert(self, table: str, data: dict) -> dict:
        self._ensure_initialized()
        if table not in self._tables:
            return {"status": "error", "error": f"unknown table '{table}'"}
        if "id" not in data:
            data["id"] = f"ROW-{uuid.uuid4().hex[:12]}"
        if "created_at" not in data:
            data["created_at"] = time.time()
        if "updated_at" not in data:
            data["updated_at"] = time.time()

        if self._conn:
            try:
                known_cols = self._get_columns(table)
                if known_cols:
                    data = {k: v for k, v in data.items() if k in known_cols}
                cols = ", ".join(data.keys())
                placeholders = ", ".join("?" for _ in data)
                sql = f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
                self._conn.execute(sql, list(data.values()))
                self._conn.commit()
                return {"status": "ok", "id": data.get("id", "")}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._json_insert(table, data)

    def _get_columns(self, table: str) -> set[str]:
        if not self._conn:
            return set()
        try:
            cursor = self._conn.execute(f"PRAGMA table_info({table})")
            return {r["name"] for r in cursor.fetchall()}
        except Exception:
            return set()

    def _json_insert(self, table: str, data: dict) -> dict:
        jpath = Path(self.db_path).parent / f"{table}.json"
        rows = []
        if jpath.exists():
            try:
                rows = json.loads(jpath.read_text())
            except (json.JSONDecodeError, OSError):
                rows = []
        rows.append(data)
        jpath.write_text(json.dumps(rows, indent=2))
        return {"status": "ok", "id": data["id"], "mode": "json"}

    def query(self, q: Query) -> list[dict]:
        self._ensure_initialized()
        if self._conn:
            return self._sql_query(q)
        else:
            return self._json_query(q)

    def _sql_query(self, q: Query) -> list[dict]:
        where_clauses = []
        params: list[Any] = []
        for k, v in q.filters.items():
            where_clauses.append(f"{k} = ?")
            params.append(v)
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
        order_sql = f"ORDER BY {q.order_by}" if q.order_by else ""
        sql = f"SELECT * FROM {q.table} {where_sql} {order_sql} LIMIT ? OFFSET ?"
        params.extend([q.limit, q.offset])
        try:
            cursor = self._conn.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            return [{"error": str(e)}]

    def _json_query(self, q: Query) -> list[dict]:
        jpath = Path(self.db_path).parent / f"{q.table}.json"
        if not jpath.exists():
            return []
        try:
            rows = json.loads(jpath.read_text())
        except (json.JSONDecodeError, OSError):
            return []
        result = rows
        for k, v in q.filters.items():
            result = [r for r in result if r.get(k) == v]
        if q.order_by:
            reverse = q.order_by.startswith("-")
            key = q.order_by.lstrip("-")
            result = sorted(result, key=lambda r: r.get(key, 0), reverse=reverse)
        result = result[q.offset:q.offset + q.limit]
        return result

    def update(self, table: str, row_id: str, data: dict) -> dict:
        self._ensure_initialized()
        if self._conn:
            data["updated_at"] = time.time()
            sets = ", ".join(f"{k} = ?" for k in data)
            params = list(data.values()) + [row_id]
            try:
                self._conn.execute(f"UPDATE {table} SET {sets} WHERE id = ?", params)
                self._conn.commit()
                return {"status": "ok"}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            jpath = Path(self.db_path).parent / f"{table}.json"
            if not jpath.exists():
                return {"status": "error", "error": "not found"}
            try:
                rows = json.loads(jpath.read_text())
            except (json.JSONDecodeError, OSError):
                return {"status": "error", "error": "corrupt"}
            for r in rows:
                if r.get("id") == row_id:
                    r.update(data)
                    r["updated_at"] = time.time()
                    break
            jpath.write_text(json.dumps(rows, indent=2))
            return {"status": "ok", "mode": "json"}

    def delete(self, table: str, row_id: str) -> dict:
        self._ensure_initialized()
        if self._conn:
            try:
                self._conn.execute(f"DELETE FROM {table} WHERE id = ?", [row_id])
                self._conn.commit()
                return {"status": "ok"}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            jpath = Path(self.db_path).parent / f"{table}.json"
            if not jpath.exists():
                return {"status": "error", "error": "not found"}
            try:
                rows = json.loads(jpath.read_text())
            except (json.JSONDecodeError, OSError):
                return {"status": "error", "error": "corrupt"}
            rows = [r for r in rows if r.get("id") != row_id]
            jpath.write_text(json.dumps(rows, indent=2))
            return {"status": "ok", "mode": "json"}

    def migrate(self, migrations: list[dict]) -> dict:
        """Execute simple migrations: add_column, drop_table, create_table."""
        if not self._conn:
            return {"status": "ok", "note": "no SQLite, skipping migrations"}
        applied = 0
        for m in migrations:
            action = m.get("action", "")
            table = m.get("table", "")
            try:
                if action == "add_column":
                    col_def = m["column"]
                    self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
                    applied += 1
                elif action == "drop_table":
                    self._conn.execute(f"DROP TABLE IF EXISTS {table}")
                    applied += 1
                elif action == "create_table":
                    td = m["table_def"]
                    self._create_table(TableDef(**td))
                    applied += 1
            except Exception as e:
                return {"status": "error", "error": str(e), "migration": m}
        self._conn.commit()
        return {"status": "ok", "applied": applied}

    def export_json(self, table: str) -> list[dict]:
        return self.query(Query(table=table, limit=10000))

    def import_json(self, table: str, rows: list[dict]) -> dict:
        imported = 0
        for row in rows:
            r = self.insert(table, row)
            if r.get("status") == "ok":
                imported += 1
        return {"status": "ok", "imported": imported, "table": table}

    def get_stats(self) -> dict:
        stats = {"tables": list(self._tables.keys()), "initialized": self._initialized}
        if self._conn:
            try:
                cursor = self._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                stats["sqlite_tables"] = [r["name"] for r in cursor.fetchall()]
            except Exception:
                stats["sqlite_tables"] = []
        return stats

    def _ensure_initialized(self):
        if not self._initialized:
            self.initialize()

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "stats")
        if action == "initialize":
            return self.initialize()
        elif action == "register_table":
            td = input_data.get("table_def", {})
            return {"status": "ok",
                    "result": self.register_table(TableDef(**td))}
        elif action == "insert":
            return self.insert(input_data.get("table", ""),
                               input_data.get("data", {}))
        elif action == "query":
            q = input_data.get("query", {})
            return {"status": "ok",
                    "result": self.query(Query(**q))}
        elif action == "update":
            return self.update(input_data.get("table", ""),
                               input_data.get("id", ""),
                               input_data.get("data", {}))
        elif action == "delete":
            return self.delete(input_data.get("table", ""),
                               input_data.get("id", ""))
        elif action == "migrate":
            return self.migrate(input_data.get("migrations", []))
        elif action == "export":
            return {"status": "ok",
                    "result": self.export_json(input_data.get("table", ""))}
        elif action == "import":
            return self.import_json(input_data.get("table", ""),
                                    input_data.get("rows", []))
        return self.get_stats()
