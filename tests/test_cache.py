"""Tests for CIEL CacheEngine — TTL cache with memory + SQLite backends."""
from __future__ import annotations

import os
import tempfile
import time

import pytest

from ciel.cache.core import CacheEngine, MemoryBackend, SQLiteBackend


@pytest.fixture
def mem_cache():
    return CacheEngine(backend="memory", max_size=100)


@pytest.fixture
def sqlite_cache():
    tmp = tempfile.mktemp(suffix=".db")
    cache = CacheEngine(backend="sqlite", db_path=tmp)
    yield cache
    try:
        os.remove(tmp)
    except OSError:
        pass


class TestMemoryBackend:
    def test_set_and_get(self, mem_cache):
        mem_cache.set("key1", "value1")
        assert mem_cache.get("key1") == "value1"

    def test_get_missing(self, mem_cache):
        assert mem_cache.get("nonexistent") is None

    def test_get_default(self, mem_cache):
        assert mem_cache.get("nonexistent", "fallback") == "fallback"

    def test_delete(self, mem_cache):
        mem_cache.set("del_key", "x")
        assert mem_cache.delete("del_key") is True
        assert mem_cache.get("del_key") is None

    def test_delete_missing(self, mem_cache):
        assert mem_cache.delete("ghost") is False

    def test_clear(self, mem_cache):
        mem_cache.set("a", 1)
        mem_cache.set("b", 2)
        mem_cache.clear()
        assert mem_cache.get("a") is None

    def test_expiry(self, mem_cache):
        mem_cache.set("exp", "soon", ttl=0.01)
        time.sleep(0.02)
        assert mem_cache.get("exp") is None

    def test_get_or_set(self, mem_cache):
        val = mem_cache.get_or_set("lazy", lambda: 42)
        assert val == 42
        assert mem_cache.get("lazy") == 42

    def test_get_or_set_cached(self, mem_cache):
        mem_cache.set("cached", "original")
        val = mem_cache.get_or_set("cached", lambda: "new")
        assert val == "original"

    def test_max_size_eviction(self, mem_cache):
        for i in range(200):
            mem_cache.set(f"k{i}", i)
        stats = mem_cache.get_stats()
        assert stats["entries"] <= 100

    def test_stats(self, mem_cache):
        mem_cache.set("s1", 1)
        mem_cache.set("s2", 2)
        stats = mem_cache.get_stats()
        assert stats["entries"] == 2
        assert stats["backend"] == "memory"

    def test_hits_increment(self, mem_cache):
        mem_cache.set("hit", "value")
        mem_cache.get("hit")
        mem_cache.get("hit")
        entry = mem_cache._backend._store["hit"]
        assert entry.hits == 2

    def test_process_get(self, mem_cache):
        mem_cache.set("p", "val")
        r = mem_cache.process({"action": "get", "key": "p"})
        assert r["value"] == "val"
        assert r["hit"] is True

    def test_process_set(self, mem_cache):
        r = mem_cache.process({"action": "set", "key": "q",
                                "value": "new"})
        assert r["status"] == "ok"
        assert mem_cache.get("q") == "new"

    def test_process_delete(self, mem_cache):
        mem_cache.set("d", "x")
        r = mem_cache.process({"action": "delete", "key": "d"})
        assert r["deleted"] is True
        assert mem_cache.get("d") is None

    def test_process_clear(self, mem_cache):
        mem_cache.set("a", 1)
        r = mem_cache.process({"action": "clear"})
        assert r["status"] == "ok"
        assert mem_cache.get("a") is None

    def test_process_get_or_set(self, mem_cache):
        r = mem_cache.process({"action": "get_or_set",
                                "key": "factory",
                                "factory_value": "created"})
        assert r["value"] == "created"

    def test_process_stats(self, mem_cache):
        r = mem_cache.process({"action": "stats"})
        assert "entries" in r


class TestSQLiteBackend:
    def test_set_and_get(self, sqlite_cache):
        sqlite_cache.set("sk1", "sqlite_val")
        assert sqlite_cache.get("sk1") == "sqlite_val"

    def test_get_missing(self, sqlite_cache):
        assert sqlite_cache.get("missing") is None

    def test_delete(self, sqlite_cache):
        sqlite_cache.set("del", "x")
        assert sqlite_cache.delete("del") is True
        assert sqlite_cache.get("del") is None

    def test_clear(self, sqlite_cache):
        sqlite_cache.set("a", 1)
        sqlite_cache.clear()
        assert sqlite_cache.get("a") is None

    def test_expiry(self, sqlite_cache):
        sqlite_cache.set("exp", "soon", ttl=0.01)
        time.sleep(0.02)
        assert sqlite_cache.get("exp") is None

    def test_complex_values(self, sqlite_cache):
        data = {"nested": [1, 2, 3], "flag": True}
        sqlite_cache.set("complex", data)
        assert sqlite_cache.get("complex") == data

    def test_stats(self, sqlite_cache):
        sqlite_cache.set("a", 1)
        stats = sqlite_cache.get_stats()
        assert stats["backend"] == "sqlite"

    def test_multiple_keys(self, sqlite_cache):
        for i in range(10):
            sqlite_cache.set(f"mk{i}", i)
        for i in range(10):
            assert sqlite_cache.get(f"mk{i}") == i

    def test_get_or_set(self, sqlite_cache):
        val = sqlite_cache.get_or_set("lazy_sql", lambda: 99)
        assert val == 99
