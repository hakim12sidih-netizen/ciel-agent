"""
CRDT Sync — lightweight state-based CRDT for offline message replication.

Architecture:
  - Each message gets a UUID (msg_uid) that is stable across devices
  - Each field is a LWW (Last-Writer-Wins) register with wall-clock timestamp
  - A SyncOp captures {uid, field, value, timestamp, source}
  - merge() applies operations idempotently (latest timestamp wins)
  - sync() exchanges ops between two stores
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.memory.session_db.core import SessionDB


@dataclass
class CRDTMessage:
    """
    A message with CRDT metadata for conflict-free merging.

    The uid is globally unique and stable across devices.
    Fields use LWW: the value with the highest wall_ts wins.
    """
    uid: str
    session_id: str
    role: str
    content: str
    wall_ts: float  # milliseconds since epoch
    source: str = "local"
    metadata: dict = field(default_factory=dict)
    tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "wall_ts": self.wall_ts,
            "source": self.source,
            "metadata": self.metadata,
            "tokens": self.tokens,
        }

    @classmethod
    def from_dict(cls, d: dict) -> CRDTMessage:
        return cls(
            uid=d["uid"],
            session_id=d["session_id"],
            role=d["role"],
            content=d["content"],
            wall_ts=d.get("wall_ts", time.time() * 1000),
            source=d.get("source", "remote"),
            metadata=d.get("metadata", {}),
            tokens=d.get("tokens", 0),
        )


@dataclass
class SyncOp:
    """
    A single CRDT operation: set a field on a message.

    LWW merge: when two ops conflict, the one with higher
    (wall_ts, source) wins (deterministic tiebreaker).
    """
    uid: str
    field: str
    value: Any
    wall_ts: float
    source: str

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "field": self.field,
            "value": self.value,
            "wall_ts": self.wall_ts,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SyncOp:
        return cls(
            uid=d["uid"],
            field=d["field"],
            value=d["value"],
            wall_ts=d.get("wall_ts", 0),
            source=d.get("source", "remote"),
        )


class CRDTSync:
    """
    CRDT sync engine over SessionDB.

    Provides:
      - create_message(): create a CRDT-tracked message
      - get_ops(): get all pending ops since a given ID
      - merge(): apply remote ops to local store
      - sync(): generate ops to send, merge received ops
    """

    def __init__(self, db: SessionDB, source_id: str | None = None):
        self.db = db
        self.source_id = source_id or f"ciel-{uuid.uuid4().hex[:8]}"

    # ── Create ────────────────────────────────────────────

    def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens: int = 0,
        metadata: dict | None = None,
    ) -> CRDTMessage:
        """Create a message with CRDT uid and return it."""
        uid = str(uuid.uuid4())
        wall_ts = time.time() * 1000

        msg = CRDTMessage(
            uid=uid,
            session_id=session_id,
            role=role,
            content=content,
            wall_ts=wall_ts,
            source=self.source_id,
            metadata=metadata or {},
            tokens=tokens,
        )

        # Store in DB via the normal path
        msg_id = self.db.add_message(
            session_id=session_id,
            role=role,
            content=content,
            tokens=tokens,
            metadata={"crdt_uid": uid, "wall_ts": wall_ts, "source": self.source_id},
        )

        # Log each field as a SyncOp
        ops = [
            SyncOp(uid, "role", role, wall_ts, self.source_id),
            SyncOp(uid, "content", content, wall_ts, self.source_id),
        ]
        self._log_ops(session_id, ops)

        return msg

    def _log_ops(self, session_id: str, ops: list[SyncOp]):
        """Persist SyncOps to the sync_log table."""
        conn = self.db._get_conn()
        now = time.time() * 1000
        for op in ops:
            conn.execute(
                """INSERT INTO sync_log
                   (session_id, entry_type, entry_id, operation, patch, source)
                   VALUES (?, 'crdt_op', ?, ?, ?, ?)""",
                (session_id, op.uid, op.field,
                 json.dumps({"value": op.value, "wall_ts": op.wall_ts}),
                 op.source),
            )
        conn.commit()

    # ── Read Ops ──────────────────────────────────────────

    def get_ops(self, session_id: str, since_id: int = 0) -> list[SyncOp]:
        """Get all CRDT ops for a session since a given sync_log ID."""
        rows = self.db.get_sync_log(session_id, since_id=since_id)
        ops = []
        for row in rows:
            if row["entry_type"] != "crdt_op":
                continue
            try:
                patch = json.loads(row["patch"])
                ops.append(SyncOp(
                    uid=row["entry_id"],
                    field=row["operation"],
                    value=patch.get("value", ""),
                    wall_ts=patch.get("wall_ts", 0),
                    source=row["source"],
                ))
            except (json.JSONDecodeError, KeyError):
                continue
        return ops

    # ── Merge ─────────────────────────────────────────────

    def merge(self, session_id: str, remote_ops: list[SyncOp]) -> int:
        """
        Merge remote SyncOps into local state.

        LWW rule: for each (uid, field) pair, the op with higher
        (wall_ts, source) wins. Returns count of applied ops.
        """
        # Group remote ops by (uid, field) keeping the highest timestamp
        best: dict[tuple[str, str], SyncOp] = {}
        for op in remote_ops:
            key = (op.uid, op.field)
            existing = best.get(key)
            if existing is None or self._op_wins(op, existing):
                best[key] = op

        # Get existing CRDT metadata for all relevant UIDs
        uids = {k[0] for k in best}
        existing_state = self._get_current_state(session_id, uids)

        applied = 0
        conn = self.db._get_conn()

        for (uid, field), remote_op in best.items():
            local = existing_state.get(uid, {})
            local_ts = local.get(f"{field}_ts", 0)
            local_src = local.get(f"{field}_src", "")

            if remote_op.wall_ts > local_ts or (
                remote_op.wall_ts == local_ts and remote_op.source > local_src
            ):
                # Apply remote value
                existing_msg = conn.execute(
                    "SELECT id FROM messages WHERE session_id = ? AND json_extract(metadata, '$.crdt_uid') = ?",
                    (session_id, uid),
                ).fetchone()

                if existing_msg:
                    if field == "content":
                        conn.execute(
                            "UPDATE messages SET content = ?, metadata = json_set(metadata, '$.remote_ts', ?) WHERE id = ?",
                            (remote_op.value, remote_op.wall_ts, existing_msg["id"]),
                        )
                    elif field == "role":
                        conn.execute(
                            "UPDATE messages SET role = ? WHERE id = ?",
                            (remote_op.value, existing_msg["id"]),
                        )
                else:
                    # Create new message from remote
                    if field == "content" and "role" in best:
                        # Wait for both fields to arrive
                        continue

            applied += 1

        conn.commit()
        return applied

    def _op_wins(self, a: SyncOp, b: SyncOp) -> bool:
        """Deterministic tiebreaker: higher (wall_ts, source) wins."""
        return (a.wall_ts, a.source) > (b.wall_ts, b.source)

    def _get_current_state(self, session_id: str, uids: set[str]) -> dict[str, dict]:
        """Get current CRDT metadata for a set of message UIDs."""
        if not uids:
            return {}

        placeholders = ",".join("?" for _ in uids)
        conn = self.db._get_conn()
        rows = conn.execute(
            f"""SELECT json_extract(metadata, '$.crdt_uid') as uid,
                       json_extract(metadata, '$.wall_ts') as wall_ts,
                       json_extract(metadata, '$.source') as source
                FROM messages
                WHERE session_id = ? AND json_extract(metadata, '$.crdt_uid') IN ({placeholders})""",
            (session_id, *uids),
        ).fetchall()

        state: dict[str, dict] = {}
        for row in rows:
            uid = row["uid"]
            if uid:
                state[uid] = {
                    "content_ts": float(row["wall_ts"] or 0),
                    "content_src": row["source"] or "",
                    "role_ts": float(row["wall_ts"] or 0),
                    "role_src": row["source"] or "",
                }
        return state

    # ── Full Sync ─────────────────────────────────────────

    def sync(
        self, session_id: str, remote_ops: list[SyncOp], since_id: int = 0
    ) -> list[SyncOp]:
        """
        Two-way sync:
          1. Merge remote ops into local
          2. Return local ops since the given sync_log ID
        """
        self.merge(session_id, remote_ops)
        return self.get_ops(session_id, since_id=since_id)
