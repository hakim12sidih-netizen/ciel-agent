"""
Vector search for SessionDB.

Two modes:
  1. **sqlite-vec** (fast) — if the extension is installed
  2. **Pure SQL + Python** (portable) — cosine similarity via numpy or manual

The vector table uses binary BLOBs (np.float32 array packed via .tobytes()).
"""

from __future__ import annotations

import json
import math
import struct
from typing import Any

from ciel.memory.session_db.core import SessionDB


def _bytes_to_floats(data: bytes) -> list[float]:
    """Unpack binary float32 array."""
    count = len(data) // 4
    return list(struct.unpack(f"{count}f", data))


def _floats_to_bytes(floats: list[float]) -> bytes:
    """Pack list of floats to binary float32 array."""
    return struct.pack(f"{len(floats)}f", *floats)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VectorSearch:
    """
    Vector search over message embeddings stored in SessionDB.

    Usage:
        db = SessionDB()
        vs = VectorSearch(db)

        # Store an embedding
        vs.store(msg_id, [0.1, 0.2, ...], model="text-embedding-3-small")

        # Search
        results = vs.search([0.15, 0.25, ...], top_k=10)
    """

    def __init__(self, db: SessionDB):
        self.db = db
        self._vec_available = self._check_vec()

    def _check_vec(self) -> bool:
        """Check if sqlite-vec extension is available."""
        try:
            conn = self.db._get_conn()
            conn.execute("SELECT vec_version()")
            return True
        except Exception:
            return False

    @property
    def has_vec_extension(self) -> bool:
        return self._vec_available

    def store(
        self,
        message_id: int,
        vector: list[float],
        model: str = "",
    ) -> None:
        """Store a float32 embedding vector for a message."""
        blob = _floats_to_bytes(vector)
        self.db.save_embedding(
            message_id=message_id,
            embedding=blob,
            model=model,
            dim=len(vector),
        )

    def get(self, message_id: int) -> list[float] | None:
        """Retrieve the embedding vector for a message."""
        row = self.db.get_embedding(message_id)
        if row is None:
            return None
        return _bytes_to_floats(row["embedding"])

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Search for similar messages by vector similarity.

        Returns list of {message_id, session_id, content, role, score}.
        """
        if self._vec_available:
            return self._search_vec(query_vector, top_k, threshold)
        return self._search_python(query_vector, top_k, threshold)

    def _search_python(
        self,
        query_vector: list[float],
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Brute-force cosine similarity in Python."""
        conn = self.db._get_conn()
        rows = conn.execute(
            """SELECT m.id, m.session_id, m.content, m.role, e.embedding
               FROM message_embeddings e
               JOIN messages m ON m.id = e.message_id
               ORDER BY e.rowid"""
        ).fetchall()

        scored: list[tuple[float, dict]] = []
        for row in rows:
            vec = _bytes_to_floats(row["embedding"])
            score = _cosine_similarity(query_vector, vec)
            if score >= threshold:
                scored.append((score, {
                    "message_id": row["id"],
                    "session_id": row["session_id"],
                    "content": row["content"],
                    "role": row["role"],
                    "score": round(score, 6),
                }))

        scored.sort(key=lambda x: -x[0])
        return [s[1] for s in scored[:top_k]]

    def _search_vec(
        self,
        query_vector: list[float],
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Fast vector search via sqlite-vec extension."""
        conn = self.db._get_conn()
        query_blob = _floats_to_bytes(query_vector)

        try:
            rows = conn.execute(
                """SELECT m.id, m.session_id, m.content, m.role,
                          vec_distance_cosine(e.embedding, ?) AS score
                   FROM message_embeddings e
                   JOIN messages m ON m.id = e.message_id
                   WHERE vec_distance_cosine(e.embedding, ?) <= ?
                   ORDER BY score ASC
                   LIMIT ?""",
                (query_blob, query_blob, 1.0 - threshold, top_k),
            ).fetchall()
        except Exception:
            return self._search_python(query_vector, top_k, threshold)

        return [
            {
                "message_id": r["id"],
                "session_id": r["session_id"],
                "content": r["content"],
                "role": r["role"],
                "score": round(1.0 - r["score"], 6),
            }
            for r in rows
        ]
