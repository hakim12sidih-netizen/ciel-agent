"""
SessionDB — Persistant SQLite session store with WAL, FTS5, and migrations.

Étend LLMState avec :
  - Migration system (schema version tracking)
  - Proper connection pooling per thread
  - WAL + foreign_keys + busy timeout
  - Message attachments metadata
  - Session metadata JSON
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2

# Migration steps: (version, description, SQL)
MIGRATIONS: list[tuple[int, str, list[str]]] = [
    (1, "Initial schema: sessions, messages, messages_fts",
     [
         """CREATE TABLE IF NOT EXISTS sessions (
             session_id TEXT PRIMARY KEY,
             platform TEXT NOT NULL DEFAULT 'cli',
             chat_id TEXT NOT NULL DEFAULT '',
             user_id TEXT NOT NULL DEFAULT '',
             title TEXT NOT NULL DEFAULT '',
             created_at TEXT NOT NULL DEFAULT (datetime('now')),
             updated_at TEXT NOT NULL DEFAULT (datetime('now')),
             message_count INTEGER NOT NULL DEFAULT 0,
             model TEXT NOT NULL DEFAULT '',
             system_prompt TEXT NOT NULL DEFAULT '',
             metadata TEXT NOT NULL DEFAULT '{}',
             is_active INTEGER NOT NULL DEFAULT 1
         )""",
         """CREATE TABLE IF NOT EXISTS messages (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             session_id TEXT NOT NULL REFERENCES sessions(session_id),
             role TEXT NOT NULL,
             content TEXT NOT NULL,
             timestamp TEXT NOT NULL DEFAULT (datetime('now')),
             tokens INTEGER DEFAULT 0,
             metadata TEXT DEFAULT '{}'
         )""",
         """CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
             content, content=messages, content_rowid=id
         )""",
         "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)",
         "CREATE INDEX IF NOT EXISTS idx_sessions_platform ON sessions(platform)",
         "CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active)",
     ]),
    (2, "Add FTS triggers, embeddings table, and CRDT sync table",
     [
         # FTS sync triggers — external content FTS5 needs manual sync
         """CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
             INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
         END""",
         """CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
             INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.id, old.content);
         END""",
         """CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
             INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.id, old.content);
             INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
         END""",
         # Embeddings table
         """CREATE TABLE IF NOT EXISTS message_embeddings (
             message_id INTEGER PRIMARY KEY REFERENCES messages(id) ON DELETE CASCADE,
             embedding BLOB NOT NULL,
             model TEXT NOT NULL DEFAULT '',
             dim INTEGER NOT NULL DEFAULT 0,
             created_at TEXT NOT NULL DEFAULT (datetime('now'))
         )""",
         # CRDT sync log
         """CREATE TABLE IF NOT EXISTS sync_log (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             session_id TEXT NOT NULL,
             entry_type TEXT NOT NULL,
             entry_id TEXT NOT NULL,
             operation TEXT NOT NULL,
             patch TEXT NOT NULL DEFAULT '{}',
             timestamp TEXT NOT NULL DEFAULT (datetime('now')),
             source TEXT NOT NULL DEFAULT 'local'
         )""",
         "CREATE INDEX IF NOT EXISTS idx_sync_session ON sync_log(session_id)",
     ]),
]


class SessionDB:
    """
    Session database with WAL, FTS5, migration support.

    Thread-safe: one connection per thread via threading.local().
    Writes serialized via threading.Lock().
    """

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or Path.home() / ".ciel" / "session.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._write_lock = threading.Lock()
        self._migrate()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection, creating if needed."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path))
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn.execute("PRAGMA busy_timeout=5000")
        return self._local.conn

    def _get_version(self) -> int:
        """Read current schema version from the database."""
        conn = self._get_conn()
        try:
            row = conn.execute("PRAGMA user_version").fetchone()
            return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0

    def _set_version(self, version: int):
        """Persist schema version."""
        conn = self._get_conn()
        conn.execute(f"PRAGMA user_version={version}")

    def _migrate(self):
        """Run pending migrations sequentially."""
        conn = self._get_conn()
        current = self._get_version()

        for version, description, statements in MIGRATIONS:
            if version > current:
                with self._write_lock:
                    for stmt in statements:
                        try:
                            conn.execute(stmt)
                        except sqlite3.OperationalError as e:
                            # FTS5 might already exist
                            if "already exists" not in str(e):
                                raise
                    self._set_version(version)

    def close(self):
        """Close the thread-local connection."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    # ── Session CRUD ──────────────────────────────────────

    def create_session(
        self,
        platform: str = "cli",
        chat_id: str = "",
        user_id: str = "",
        title: str = "",
        model: str = "",
        system_prompt: str = "",
        metadata: dict | None = None,
    ) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata or {})

        with self._write_lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO sessions (session_id, platform, chat_id, user_id,
                   title, created_at, updated_at, model, system_prompt, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, platform, chat_id, user_id, title,
                 now, now, model, system_prompt, meta_json),
            )
            conn.commit()

        self._log_sync(session_id, "session", session_id, "create")
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def list_sessions(
        self, platform: str = "", limit: int = 50, offset: int = 0
    ) -> list[dict]:
        conn = self._get_conn()
        if platform:
            rows = conn.execute(
                """SELECT * FROM sessions
                   WHERE platform = ? AND is_active = 1
                   ORDER BY updated_at DESC LIMIT ? OFFSET ?""",
                (platform, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM sessions
                   WHERE is_active = 1
                   ORDER BY updated_at DESC LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]

    def update_session(
        self, session_id: str, **fields: Any
    ) -> bool:
        """Update session fields (title, model, system_prompt, metadata)."""
        allowed = {"title", "model", "system_prompt", "metadata"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False

        if "metadata" in updates and isinstance(updates["metadata"], dict):
            updates["metadata"] = json.dumps(updates["metadata"])

        now = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in updates)

        with self._write_lock:
            conn = self._get_conn()
            conn.execute(
                f"UPDATE sessions SET {set_clause} WHERE session_id = ?",
                (*updates.values(), session_id),
            )
            conn.commit()
        return True

    def close_session(self, session_id: str) -> None:
        with self._write_lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE sessions SET is_active = 0, updated_at = ? WHERE session_id = ?",
                (datetime.now(timezone.utc).isoformat(), session_id),
            )
            conn.commit()

    def delete_session(self, session_id: str) -> None:
        with self._write_lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()

    # ── Message CRUD ──────────────────────────────────────

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens: int = 0,
        metadata: dict | None = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata or {})

        with self._write_lock:
            conn = self._get_conn()
            cursor = conn.execute(
                """INSERT INTO messages (session_id, role, content, timestamp, tokens, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, now, tokens, meta_json),
            )
            msg_id = cursor.lastrowid

            conn.execute(
                """UPDATE sessions SET message_count = message_count + 1,
                   updated_at = ? WHERE session_id = ?""",
                (now, session_id),
            )
            conn.commit()

        self._log_sync(session_id, "message", str(msg_id), "create")
        return msg_id

    def get_messages(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM messages
               WHERE session_id = ?
               ORDER BY id ASC LIMIT ? OFFSET ?""",
            (session_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_messages(
        self, query: str, session_id: str = "", limit: int = 20
    ) -> list[dict]:
        conn = self._get_conn()
        if session_id:
            rows = conn.execute(
                """SELECT m.*, rank FROM messages m
                   JOIN messages_fts fts ON m.id = fts.rowid
                   WHERE messages_fts MATCH ? AND m.session_id = ?
                   ORDER BY rank LIMIT ?""",
                (query, session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT m.*, rank FROM messages m
                   JOIN messages_fts fts ON m.id = fts.rowid
                   WHERE messages_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (query, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def message_count(self, session_id: str) -> int:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT message_count FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row["message_count"] if row else 0

    # ── Embeddings / Vector ───────────────────────────────

    def save_embedding(
        self, message_id: int, embedding: bytes, model: str = "", dim: int = 0
    ):
        """Store a binary embedding blob for a message."""
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO message_embeddings
               (message_id, embedding, model, dim)
               VALUES (?, ?, ?, ?)""",
            (message_id, embedding, model, dim),
        )
        conn.commit()

    def get_embedding(self, message_id: int) -> dict | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM message_embeddings WHERE message_id = ?",
            (message_id,),
        ).fetchone()
        return dict(row) if row else None

    # ── Sync Log ──────────────────────────────────────────

    def _log_sync(
        self, session_id: str, entry_type: str, entry_id: str,
        operation: str, patch: dict | None = None,
        source: str = "local",
    ):
        try:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO sync_log (session_id, entry_type, entry_id,
                   operation, patch, source) VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, entry_type, entry_id, operation,
                 json.dumps(patch or {}), source),
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass  # sync_log may not exist yet

    def get_sync_log(
        self, session_id: str, since_id: int = 0, limit: int = 100
    ) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM sync_log
               WHERE session_id = ? AND id > ?
               ORDER BY id ASC LIMIT ?""",
            (session_id, since_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Stats ─────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        conn = self._get_conn()
        sessions = conn.execute(
            "SELECT COUNT(*) as c FROM sessions"
        ).fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) as c FROM sessions WHERE is_active=1"
        ).fetchone()[0]
        msgs = conn.execute(
            "SELECT COUNT(*) as c FROM messages"
        ).fetchone()[0]
        return {
            "total_sessions": sessions,
            "active_sessions": active,
            "total_messages": msgs,
            "db_path": str(self.db_path),
            "db_size": self.db_path.stat().st_size,
            "schema_version": self._get_version(),
        }
