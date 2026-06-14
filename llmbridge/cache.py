"""LLM response cache — déduplication et mise en cache des requêtes."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("ciel.llmbridge.cache")


class LLMCache:
    """Cache simple pour les réponses LLM (basé sur hash des messages)."""

    def __init__(self, cache_dir: str = ""):
        self._cache_dir = Path(cache_dir or "~/.ciel/cache/llm").expanduser()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory: dict[str, dict[str, Any]] = {}
        self._load()

    def _key(self, messages: list, model: str = "", temperature: float = 0.7) -> str:
        raw = json.dumps([messages, model, temperature], sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, messages: list, model: str = "", temperature: float = 0.7) -> str | None:
        key = self._key(messages, model, temperature)
        entry = self._memory.get(key)
        if entry:
            entry["hits"] = entry.get("hits", 0) + 1
            log.debug("Cache hit: %s", key[:8])
            return entry["response"]
        return None

    def set(self, messages: list, response: str, model: str = "",
            temperature: float = 0.7, ttl: int = 3600) -> None:
        key = self._key(messages, model, temperature)
        self._memory[key] = {
            "response": response,
            "created_at": time.time(),
            "ttl": ttl,
            "hits": 0,
        }
        self._save()

    def clear(self) -> None:
        self._memory.clear()
        self._save()
        log.info("LLM cache cleared")

    def stats(self) -> dict[str, Any]:
        total = len(self._memory)
        hits = sum(e.get("hits", 0) for e in self._memory.values())
        return {"total": total, "hits": hits}

    def _load(self) -> None:
        cache_file = self._cache_dir / "cache.json"
        if cache_file.exists():
            try:
                self._memory = json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                self._memory = {}

    def _save(self) -> None:
        cache_file = self._cache_dir / "cache.json"
        cache_file.write_text(json.dumps(self._memory, indent=2), encoding="utf-8")
