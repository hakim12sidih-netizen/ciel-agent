"""
CIEL v∞.9 — Plugin Bytecode Cache.
Compile, cache, and lazy-load compiled plugin bytecode.
"""
from __future__ import annotations

import os
import sys
import py_compile
import hashlib
import time
import marshal
import importlib.util
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


__all__ = [
    "BytecodeCache", "CacheEntry", "CacheStats",
    "get_cache",
]


CACHE_DIR = Path.home() / ".ciel" / "cache" / "plugins"
CACHE_VERSION = 2
MAX_CACHE_SIZE = 500 * 1024 * 1024  # 500MB
MAX_ENTRY_SIZE = 50 * 1024 * 1024  # 50MB


@dataclass
class CacheEntry:
    plugin_name: str
    plugin_version: str
    source_hash: str
    bytecode: bytes
    compiled_at: float
    size: int
    python_version: str
    cache_version: int = CACHE_VERSION

    def to_dict(self) -> dict:
        return {
            "plugin_name": self.plugin_name,
            "plugin_version": self.plugin_version,
            "source_hash": self.source_hash,
            "size": self.size,
            "compiled_at": self.compiled_at,
            "python_version": self.python_version,
            "cache_version": self.cache_version,
        }


@dataclass
class CacheStats:
    entries: int = 0
    total_size: int = 0
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    oldest: float = 0
    newest: float = 0


def _source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def _py_ver_str() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


class BytecodeCache:
    def __init__(self, cache_dir: str | Path | None = None):
        self._cache_dir = Path(cache_dir or CACHE_DIR).expanduser().resolve()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats()
        self._load_index()

    def _index_path(self) -> Path:
        return self._cache_dir / "index.json"

    def _entry_path(self, plugin_name: str, source_hash: str) -> Path:
        return self._cache_dir / f"{plugin_name}@{source_hash}.pyc"

    def _load_index(self):
        idx_path = self._index_path()
        if not idx_path.exists():
            return
        try:
            import json
            data = json.loads(idx_path.read_text())
            for entry in data.get("entries", []):
                key = f"{entry['plugin_name']}@{entry['source_hash']}"
                self._index[key] = CacheEntry(**entry)
            self._stats.entries = len(self._index)
            self._stats.total_size = sum(e.size for e in self._index.values())
            if self._index:
                times = [e.compiled_at for e in self._index.values()]
                self._stats.oldest = min(times)
                self._stats.newest = max(times)
        except Exception:
            self._index.clear()

    def _save_index(self):
        import json
        idx_path = self._index_path()
        data = {
            "version": CACHE_VERSION,
            "entries": [e.to_dict() for e in self._index.values()],
        }
        idx_path.write_text(json.dumps(data, indent=2))

    def get(self, plugin_name: str, source: str) -> bytes | None:
        key = f"{plugin_name}@{_source_hash(source)}"
        with self._lock:
            entry = self._index.get(key)
            if not entry:
                self._stats.misses += 1
                return None

            pyc_path = self._entry_path(plugin_name, entry.source_hash)
            if not pyc_path.exists():
                self._index.pop(key, None)
                self._stats.misses += 1
                return None

            if entry.python_version != _py_ver_str():
                pyc_path.unlink(missing_ok=True)
                self._index.pop(key, None)
                self._save_index()
                self._stats.misses += 1
                return None

            self._stats.hits += 1
            return pyc_path.read_bytes()

    def put(self, plugin_name: str, source: str, version: str,
            bytecode: bytes):
        if len(bytecode) > MAX_ENTRY_SIZE:
            return

        key = f"{plugin_name}@{_source_hash(source)}"
        with self._lock:
            self._evict_if_needed(len(bytecode))

            entry = CacheEntry(
                plugin_name=plugin_name,
                plugin_version=version,
                source_hash=_source_hash(source),
                bytecode=bytecode,
                compiled_at=time.time(),
                size=len(bytecode),
                python_version=_py_ver_str(),
            )

            pyc_path = self._entry_path(plugin_name, entry.source_hash)
            pyc_path.write_bytes(bytecode)
            self._index[key] = entry
            self._stats.total_size += len(bytecode)
            self._stats.entries = len(self._index)
            self._stats.newest = entry.compiled_at
            self._save_index()

    def _evict_if_needed(self, needed: int):
        while self._stats.total_size + needed > MAX_CACHE_SIZE and self._index:
            oldest_key = min(self._index.keys(),
                             key=lambda k: self._index[k].compiled_at)
            oldest = self._index.pop(oldest_key)
            pyc_path = self._entry_path(oldest.plugin_name, oldest.source_hash)
            pyc_path.unlink(missing_ok=True)
            self._stats.total_size -= oldest.size
            self._stats.evictions += 1

    def invalidate(self, plugin_name: str):
        with self._lock:
            keys = [k for k in self._index if k.startswith(f"{plugin_name}@")]
            for k in keys:
                entry = self._index.pop(k)
                pyc_path = self._entry_path(plugin_name, entry.source_hash)
                pyc_path.unlink(missing_ok=True)
                self._stats.total_size -= entry.size
                self._stats.evictions += 1
            self._stats.entries = len(self._index)
            self._save_index()

    def clear(self):
        with self._lock:
            for pyc in self._cache_dir.glob("*.pyc"):
                pyc.unlink(missing_ok=True)
            self._index.clear()
            idx_path = self._index_path()
            if idx_path.exists():
                idx_path.unlink()
            self._stats = CacheStats()

    def get_stats(self) -> dict:
        with self._lock:
            hit_rate = (self._stats.hits / (self._stats.hits + self._stats.misses) * 100
                        if (self._stats.hits + self._stats.misses) > 0 else 0)
            return {
                "entries": self._stats.entries,
                "total_size": self._stats.total_size,
                "total_size_mb": round(self._stats.total_size / (1024 * 1024), 2),
                "max_size_mb": MAX_CACHE_SIZE / (1024 * 1024),
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "hit_rate_pct": round(hit_rate, 1),
                "evictions": self._stats.evictions,
                "cache_dir": str(self._cache_dir),
            }


_cache_singleton: BytecodeCache | None = None
_cache_lock = threading.Lock()


def get_cache(cache_dir: str | Path | None = None) -> BytecodeCache:
    global _cache_singleton
    if _cache_singleton is None:
        with _cache_lock:
            if _cache_singleton is None:
                _cache_singleton = BytecodeCache(cache_dir)
    return _cache_singleton


def compile_and_cache(source: str, plugin_name: str,
                      version: str = "0.0.0",
                      cache: BytecodeCache | None = None) -> bytes:
    c = cache or get_cache()

    cached = c.get(plugin_name, source)
    if cached:
        return cached

    compiled = compile(source, f"<plugin:{plugin_name}>", "exec")
    bytecode = marshal.dumps(compiled)

    c.put(plugin_name, source, version, bytecode)
    return bytecode
