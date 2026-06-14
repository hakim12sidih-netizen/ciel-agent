from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SearchResult:
    id: str
    content: str
    source: str
    score: float
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content[:200],
            "source": self.source,
            "score": round(self.score, 4),
            "timestamp": self.timestamp,
        }


class FTS5Memory:
    """Recherche full-text avec SQLite FTS5.

    Remplace la recherche naïve par une recherche sémantique et
    full-text sur les sessions, messages, et skills.

    Inspiré du système Hermès FTS5.
    """

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = Path(db_path or Path.home() / ".ciel" / "fts5.db")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                content, source, metadata,
                content_rowid='rowid',
                tokenize='porter unicode61'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_docs (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'unknown',
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_source
            ON memory_docs(source)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_timestamp
            ON memory_docs(timestamp DESC)
        """)
        conn.commit()

    def index(self, doc_id: str, content: str, source: str = "unknown",
              metadata: dict | None = None) -> None:
        conn = self._get_conn()
        now = time.time()
        meta_json = json.dumps(metadata or {})
        conn.execute(
            "INSERT OR REPLACE INTO memory_docs (id, content, source, timestamp, metadata) "
            "VALUES (?, ?, ?, ?, ?)",
            (doc_id, content, source, now, meta_json),
        )
        conn.execute(
            "INSERT OR REPLACE INTO memory_fts (rowid, content, source, metadata) "
            "VALUES (?, ?, ?, ?)",
            (conn.execute("SELECT rowid FROM memory_docs WHERE id = ?", (doc_id,))
             .fetchone()[0],
             content, source, meta_json),
        )
        conn.commit()

    def search(self, query: str, limit: int = 10,
               source: str = "") -> list[SearchResult]:
        conn = self._get_conn()
        query_safe = query.replace('"', '""')
        sql = """
            SELECT d.id, d.content, d.source, d.timestamp, d.metadata,
                   rank as score
            FROM memory_fts f
            JOIN memory_docs d ON f.rowid = d.rowid
            WHERE memory_fts MATCH ?
        """
        params: list[Any] = [query_safe]
        if source:
            sql += " AND d.source = ?"
            params.append(source)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        results: list[SearchResult] = []
        try:
            for row in conn.execute(sql, params):
                meta = {}
                try:
                    meta = json.loads(row["metadata"] or "{}")
                except Exception:
                    pass
                results.append(SearchResult(
                    id=row["id"],
                    content=row["content"],
                    source=row["source"],
                    score=row["score"],
                    timestamp=row["timestamp"],
                    metadata=meta,
                ))
        except sqlite3.OperationalError:
            pass
        return results

    def delete(self, doc_id: str) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT rowid FROM memory_docs WHERE id = ?", (doc_id,)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM memory_fts WHERE rowid = ?", (row[0],))
            conn.execute("DELETE FROM memory_docs WHERE id = ?", (doc_id,))
            conn.commit()
            return True
        return False

    def count(self, source: str = "") -> int:
        conn = self._get_conn()
        if source:
            row = conn.execute(
                "SELECT COUNT(*) FROM memory_docs WHERE source = ?", (source,)
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) FROM memory_docs").fetchone()
        return row[0] if row else 0

    def optimize(self) -> None:
        conn = self._get_conn()
        conn.execute("INSERT INTO memory_fts(memory_fts) VALUES('optimize')")
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
