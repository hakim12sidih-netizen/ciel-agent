from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class SessionRecord:
    session_id: str
    platform: str
    chat_id: str
    user_id: str
    title: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0
    model: str = ""
    system_prompt: str = ""
    metadata: str = "{}"
    is_active: bool = True


class LLMState:
    """SQLite state store avec FTS5 full-text search.

    Adapté de hermes_state.py de LLMBridge Agent.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or Path.home() / ".ciel" / "hermes_state.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path))
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
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
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                    tokens INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    content, content=messages, content_rowid=id
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_platform ON sessions(platform);
                CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active);
            """)
            conn.commit()

    def create_session(
        self,
        platform: str = "cli",
        chat_id: str = "",
        user_id: str = "",
        title: str = "",
        model: str = "",
        system_prompt: str = "",
    ) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO sessions (session_id, platform, chat_id, user_id, title, model,
                   system_prompt, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, platform, chat_id, user_id, title, model, system_prompt, now, now),
            )
            conn.commit()
        logger.debug(f"Created session {session_id} for {platform}")
        return session_id

    def get_session(self, session_id: str) -> SessionRecord | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        return SessionRecord(**dict(row))

    def list_sessions(
        self, platform: str = "", limit: int = 50, offset: int = 0
    ) -> list[SessionRecord]:
        conn = self._get_conn()
        if platform:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE platform = ? AND is_active = 1 ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (platform, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE is_active = 1 ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [SessionRecord(**dict(r)) for r in rows]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata or {})
        with self._lock:
            conn = self._get_conn()
            cur = conn.execute(
                """INSERT INTO messages (session_id, role, content, timestamp, tokens, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, now, tokens, meta_json),
            )
            msg_id = cur.lastrowid
            conn.execute(
                "UPDATE sessions SET message_count = message_count + 1, updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
            conn.commit()
        return msg_id

    def get_messages(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT id, role, content, timestamp, tokens, metadata
               FROM messages WHERE session_id = ?
               ORDER BY id ASC LIMIT ? OFFSET ?""",
            (session_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_messages(
        self, query: str, session_id: str = "", limit: int = 20
    ) -> list[dict[str, Any]]:
        conn = self._get_conn()
        if session_id:
            rows = conn.execute(
                """SELECT m.id, m.session_id, m.role, m.content, m.timestamp
                   FROM messages m JOIN messages_fts fts ON m.id = fts.rowid
                   WHERE messages_fts MATCH ? AND m.session_id = ?
                   ORDER BY rank LIMIT ?""",
                (query, session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT m.id, m.session_id, m.role, m.content, m.timestamp
                   FROM messages m JOIN messages_fts fts ON m.id = fts.rowid
                   WHERE messages_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (query, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def close_session(self, session_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE sessions SET is_active = 0, updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
            conn.commit()

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()

    def stats(self) -> dict[str, Any]:
        conn = self._get_conn()
        total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        active_sessions = conn.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1").fetchone()[0]
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "db_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
        }
