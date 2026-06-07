"""
CIEL v∞.2 — Reversibility : snapshots pour Axiome γ.

Toute évolution de CIEL doit être :
  - Snapshotable (peut être capturée)
  - Auditable (peut être inspectée)
  - Restaurable (peut être annulée dans 30 jours)

Architecture :
  - Snapshot : dict sérialisable + timestamp + signature
  - SnapshotStore : append-only journal sur disque (JSONL)
  - Restore : retrouve + restaure un snapshot

Format JSONL (un snapshot par ligne) :
  {"id": "...", "kind": "...", "data": {...}, "ts": ..., "sig": "..."}

Chaque snapshot est signé avec le Noyau Primordial (BLAKE2b keyed hash).
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.core.identity import Identity, demo_identity

SNAPSHOT_DOMAIN = b"CIELSNAP\x00"


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Un snapshot immutable d'un état CIEL.

    Attributes:
        id: UUID unique
        kind: Type de snapshot (axiom_update, skill_added, state_change, ...)
        timestamp: Unix timestamp
        data: Données sérialisables (état complet)
        previous_id: ID du snapshot précédent (chaîne)
        signature: HMAC du snapshot (avec noyau_key)
    """

    id: str
    kind: str
    timestamp: int
    data: tuple[tuple[str, Any], ...]  # hashable
    previous_id: str | None
    signature: str
    author_uuid: str

    def __post_init__(self) -> None:
        if not self.kind or not isinstance(self.kind, str):
            raise ValueError("kind doit être string non vide")
        if not self.id or not isinstance(self.id, str):
            raise ValueError("id doit être string non vide")
        if self.timestamp <= 0:
            raise ValueError(f"timestamp doit être > 0, reçu {self.timestamp}")
        if len(self.signature) != 64:
            raise ValueError(f"signature doit faire 64 chars hex, reçu {len(self.signature)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "timestamp": self.timestamp,
            "data": dict(self.data),
            "previous_id": self.previous_id,
            "signature": self.signature,
            "author_uuid": self.author_uuid,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)


class SnapshotStore:
    """Magasin de snapshots append-only (journal JSONL).

    Usage:
        >>> store = SnapshotStore(Path("data/snapshots"), identity)
        >>> snap = store.create("axiom_init", {"axioms_count": 4})
        >>> restored = store.restore(snap.id)
    """

    def __init__(
        self,
        path: Path,
        identity: Identity | None = None,
        max_age_days: int = 30,
    ) -> None:
        self._path = path
        self._identity = identity or demo_identity()
        self._max_age_s = max_age_days * 86400
        self._index: dict[str, Snapshot] = {}
        self._chain_head: str | None = None
        self._load()

    def _load(self) -> None:
        """Charge tous les snapshots depuis le disque."""
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            return
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                snap = Snapshot(
                    id=d["id"],
                    kind=d["kind"],
                    timestamp=int(d["timestamp"]),
                    data=tuple(sorted(d.get("data", {}).items())),
                    previous_id=d.get("previous_id"),
                    signature=d["signature"],
                    author_uuid=d["author_uuid"],
                )
                if _verify_snapshot(snap, self._identity.noyau_key):
                    self._index[snap.id] = snap
                    self._chain_head = snap.id
            except (KeyError, ValueError, json.JSONDecodeError):
                # Snapshot corrompu : on l'ignore
                continue

    def _append(self, snapshot: Snapshot) -> None:
        """Append au journal (atomique via O_APPEND)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(snapshot.to_json() + "\n")

    def create(self, kind: str, data: dict[str, Any] | None = None) -> Snapshot:
        """Crée un nouveau snapshot."""
        ts = int(time.time() * 1000)  # milliseconds for better ordering
        snap_id = str(uuid.uuid4())
        data_tuple = tuple(sorted((data or {}).items()))
        previous = self._chain_head
        snap = Snapshot(
            id=snap_id,
            kind=kind,
            timestamp=ts,
            data=data_tuple,
            previous_id=previous,
            signature=_sign_snapshot(snap_id, kind, ts, data_tuple, previous, self._identity),
            author_uuid=self._identity.uuid,
        )
        self._index[snap_id] = snap
        self._chain_head = snap_id
        self._append(snap)
        return snap

    def get(self, snap_id: str) -> Snapshot | None:
        return self._index.get(snap_id)

    def latest(self) -> Snapshot | None:
        if self._chain_head is None:
            return None
        return self._index.get(self._chain_head)

    def restore(self, snap_id: str) -> dict[str, Any] | None:
        """Récupère les données d'un snapshot pour restauration."""
        snap = self._index.get(snap_id)
        if snap is None:
            return None
        return dict(snap.data)

    def history(self, limit: int = 100) -> list[Snapshot]:
        """Retourne les N derniers snapshots (du plus récent au plus ancien)."""
        all_snaps = sorted(self._index.values(), key=lambda s: s.timestamp, reverse=True)
        return all_snaps[:limit]

    def within_retention(self) -> list[Snapshot]:
        """Snapshots dans la fenêtre de rétention (Axiome γ : 30 jours)."""
        cutoff = int(time.time()) - self._max_age_s
        return [s for s in self._index.values() if s.timestamp >= cutoff]

    def prune_expired(self) -> int:
        """Supprime les snapshots expirés (retourne le nombre supprimés)."""
        cutoff = int(time.time()) - self._max_age_s
        expired = [sid for sid, s in self._index.items() if s.timestamp < cutoff]
        for sid in expired:
            del self._index[sid]
        # Note : on n'efface PAS le journal sur disque pour audit
        return len(expired)

    def stats(self) -> dict[str, Any]:
        return {
            "total": len(self._index),
            "within_retention": len(self.within_retention()),
            "chain_head": self._chain_head,
            "max_age_days": self._max_age_s // 86400,
            "path": str(self._path),
        }


# ── Helpers ──────────────────────────────────────────────

def _sign_snapshot(
    snap_id: str,
    kind: str,
    timestamp: int,
    data: tuple[tuple[str, Any], ...],
    previous_id: str | None,
    identity: Identity,
) -> str:
    """Signe un snapshot avec la clé Noyau (BLAKE2b keyed)."""
    payload = json.dumps(
        {
            "id": snap_id,
            "kind": kind,
            "ts": timestamp,
            "data": data,
            "prev": previous_id,
            "author": identity.uuid,
        },
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.blake2b(
        payload, key=identity.noyau_key, digest_size=32, person=b"CIELSNAP"
    ).hexdigest()


def _verify_snapshot(snap: Snapshot, noyau_key: bytes) -> bool:
    """Vérifie la signature d'un snapshot."""
    expected = hashlib.blake2b(
        json.dumps(
            {
                "id": snap.id,
                "kind": snap.kind,
                "ts": snap.timestamp,
                "data": list(snap.data),
                "prev": snap.previous_id,
                "author": snap.author_uuid,
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8"),
        key=noyau_key,
        digest_size=32,
        person=b"CIELSNAP",
    ).hexdigest()
    return expected == snap.signature
