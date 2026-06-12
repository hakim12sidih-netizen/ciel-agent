"""
CIEL v∞.8 — CACHE ENGINE. TTL cache with memory + SQLite backends.
"""
from __future__ import annotations

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass
class CacheEntry:
    key: str
    value: Any
    ttl: float  # seconds
    created: float = 0.0
    hits: int = 0

    @property
    def expired(self) -> bool:
        return time.time() - self.created > self.ttl

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value,
                "ttl": self.ttl, "created": self.created,
                "hits": self.hits}

    @classmethod
    def from_dict(cls, d: dict) -> CacheEntry:
        return cls(key=d["key"], value=d["value"], ttl=d["ttl"],
                   created=d.get("created", 0.0),
                   hits=d.get("hits", 0))


class CacheBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> Any: ...
    @abstractmethod
    def set(self, key: str, value: Any, ttl: float) -> None: ...
    @abstractmethod
    def delete(self, key: str) -> bool: ...
    @abstractmethod
    def clear(self) -> None: ...
    @abstractmethod
    def stats(self) -> dict: ...


class MemoryBackend(CacheBackend):
    def __init__(self, max_size: int = 1000):
        self._store: dict[str, CacheEntry] = {}
        self._max_size = max_size

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expired:
            del self._store[key]
            return None
        entry.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: float) -> None:
        if len(self._store) >= self._max_size and key not in self._store:
            oldest = min(self._store.keys(),
                         key=lambda k: self._store[k].created)
            del self._store[oldest]
        self._store[key] = CacheEntry(
            key=key, value=value, ttl=ttl,
            created=time.time())

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def clear(self) -> None:
        self._store.clear()

    def stats(self) -> dict:
        return {"backend": "memory", "entries": len(self._store),
                "max_size": self._max_size,
                "expired": sum(1 for e in self._store.values()
                               if e.expired)}


class SQLiteBackend(CacheBackend):
    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or str(Path.home() / ".ciel" / "cache.db")
        self._conn = None
        self._init_db()

    def _init_db(self):
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            import sqlite3
            self._conn = sqlite3.connect(self._db_path)
            self._conn.execute("""CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY, value TEXT, ttl REAL,
                created REAL, hits INTEGER DEFAULT 0
            )""")
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.commit()
        except ImportError:
            self._conn = None

    def get(self, key: str) -> Any:
        if not self._conn:
            return None
        cursor = self._conn.execute(
            "SELECT value, created, ttl FROM cache WHERE key = ?", [key])
        row = cursor.fetchone()
        if row is None:
            return None
        val_str, created, ttl = row
        if time.time() - created > ttl:
            self._conn.execute("DELETE FROM cache WHERE key = ?", [key])
            self._conn.commit()
            return None
        self._conn.execute("UPDATE cache SET hits = hits + 1 WHERE key = ?",
                           [key])
        self._conn.commit()
        try:
            return json.loads(val_str)
        except (json.JSONDecodeError, TypeError):
            return val_str

    def set(self, key: str, value: Any, ttl: float) -> None:
        if not self._conn:
            return
        val_str = json.dumps(value) if not isinstance(value, (str, bytes)) else value
        self._conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, ttl, created) VALUES (?, ?, ?, ?)",
            [key, val_str, ttl, time.time()])
        self._conn.commit()

    def delete(self, key: str) -> bool:
        if not self._conn:
            return False
        cursor = self._conn.execute("DELETE FROM cache WHERE key = ?", [key])
        self._conn.commit()
        return cursor.rowcount > 0

    def clear(self) -> None:
        if not self._conn:
            return
        self._conn.execute("DELETE FROM cache")
        self._conn.commit()

    def stats(self) -> dict:
        if not self._conn:
            return {"backend": "sqlite", "error": "no connection"}
        cursor = self._conn.execute("SELECT COUNT(*) FROM cache")
        count = cursor.fetchone()[0]
        return {"backend": "sqlite", "entries": count,
                "path": self._db_path}


class CacheEngine:
    """Moteur de cache avec backends interchangeables.

    Par défaut : MemoryBackend. Peut basculer sur SQLiteBackend
    pour la persistance entre redémarrages.
    """

    def __init__(self, backend: str = "memory",
                 db_path: str | None = None,
                 max_size: int = 1000,
                 default_ttl: float = 300.0):
        self._default_ttl = default_ttl
        self._backend: CacheBackend
        if backend == "sqlite":
            self._backend = SQLiteBackend(db_path)
        else:
            self._backend = MemoryBackend(max_size)
        self.network = LeaderNetwork()

    @property
    def backend(self) -> CacheBackend:
        return self._backend

    def get(self, key: str, default: Any = None) -> Any:
        val = self._backend.get(key)
        return val if val is not None else default

    def set(self, key: str, value: Any,
            ttl: float | None = None) -> None:
        self._backend.set(key, value, ttl or self._default_ttl)

    def delete(self, key: str) -> bool:
        return self._backend.delete(key)

    def clear(self) -> None:
        self._backend.clear()

    def get_or_set(self, key: str, factory: callable,
                   ttl: float | None = None) -> Any:
        val = self._backend.get(key)
        if val is not None:
            return val
        val = factory()
        self._backend.set(key, val, ttl or self._default_ttl)
        return val

    def get_stats(self) -> dict:
        return self._backend.stats()

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "stats")
        if action == "get":
            val = self.get(input_data.get("key", ""),
                           input_data.get("default"))
            return {"status": "ok", "key": input_data.get("key"),
                    "value": val, "hit": val is not None}
        elif action == "set":
            self.set(input_data.get("key", ""),
                     input_data.get("value"),
                     input_data.get("ttl"))
            return {"status": "ok"}
        elif action == "delete":
            deleted = self.delete(input_data.get("key", ""))
            return {"status": "ok", "deleted": deleted}
        elif action == "clear":
            self.clear()
            return {"status": "ok"}
        elif action == "get_or_set":
            val = self.get_or_set(
                input_data.get("key", ""),
                lambda: input_data.get("factory_value"),
                input_data.get("ttl"))
            return {"status": "ok", "key": input_data.get("key"),
                    "value": val}
        return self.get_stats()
