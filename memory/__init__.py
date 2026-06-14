"""
CIEL v1.0 — Memory System : interface et backends de mémoire.

Composant CIEL natif — gestionnaire de mémoire.
Architecture Provider ABC :
  - MemoryProvider : classe de base abstraite
  - MemoryManager : orchestrateur singleton
  - Backends : builtin, honcho, mem0, hindsight, etc.
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


@dataclass(slots=True)
class MemoryEntry:
    id: str
    content: str
    type: str  # "fact", "conversation", "skill", "preference"
    source: str
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5  # 0.0-1.0
    tags: list[str] = field(default_factory=list)
    embedding: list[float] | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "content": self.content, "type": self.type,
            "source": self.source, "timestamp": self.timestamp,
            "importance": self.importance, "tags": self.tags,
        }


class MemoryProvider(ABC):
    """Abstract Base Class pour les providers de mémoire CIEL."""

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def initialize(self, session_id: str) -> bool:
        ...

    def is_available(self) -> bool:
        return True

    def store(self, entry: MemoryEntry) -> bool:
        raise NotImplementedError

    def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        raise NotImplementedError

    def forget(self, entry_id: str) -> bool:
        raise NotImplementedError

    def list_by_type(self, type_: str, limit: int = 50) -> list[MemoryEntry]:
        raise NotImplementedError

    def shutdown(self) -> None:
        pass


class BuiltinMemoryProvider(MemoryProvider):
    """Provider mémoire par défaut (stockage JSON local)."""

    def __init__(self, storage_dir: str | Path = "data/memory"):
        self._storage = Path(storage_dir)
        self._storage.mkdir(parents=True, exist_ok=True)
        self._session_id: str | None = None
        self._entries: list[MemoryEntry] = []
        self._dirty = False

    def name(self) -> str:
        return "builtin"

    def initialize(self, session_id: str) -> bool:
        self._session_id = session_id
        session_file = self._storage / f"{session_id}.json"
        if session_file.exists():
            data = json.loads(session_file.read_text(encoding="utf-8"))
            self._entries = [MemoryEntry(**e) for e in data.get("entries", [])]
        return True

    def store(self, entry: MemoryEntry) -> bool:
        self._entries.append(entry)
        self._dirty = True
        self._flush()
        return True

    def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        query_lower = query.lower()
        scored = []
        for e in self._entries:
            score = 0
            if query_lower in e.content.lower():
                score += 1
            for tag in e.tags:
                if query_lower in tag.lower():
                    score += 0.5
            score *= e.importance
            if score > 0:
                scored.append((score, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    def forget(self, entry_id: str) -> bool:
        self._entries = [e for e in self._entries if e.id != entry_id]
        self._dirty = True
        self._flush()
        return True

    def list_by_type(self, type_: str, limit: int = 50) -> list[MemoryEntry]:
        return [e for e in self._entries if e.type == type_][:limit]

    def _flush(self) -> None:
        if not self._dirty or not self._session_id:
            return
        session_file = self._storage / f"{self._session_id}.json"
        data = {"session_id": self._session_id, "entries": [e.to_dict() for e in self._entries]}
        session_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._dirty = False

    def statistics(self) -> dict:
        types = {}
        for e in self._entries:
            types[e.type] = types.get(e.type, 0) + 1
        return {
            "total_entries": len(self._entries),
            "by_type": types,
            "avg_importance": sum(e.importance for e in self._entries) / max(1, len(self._entries)),
        }


class MemoryManager:
    """Orchestrateur mémoire CIEL.

    Gère la hiérarchie des providers :
      - builtin : toujours actif
      - externes : un seul provider externe autorisé
    """

    def __init__(self):
        self.providers: list[MemoryProvider] = [BuiltinMemoryProvider()]
        self.network = LeaderNetwork()

    def add_provider(self, provider: MemoryProvider) -> bool:
        # Un seul provider externe
        if len(self.providers) >= 2:
            return False
        self.providers.append(provider)
        return True

    def initialize_all(self, session_id: str) -> bool:
        success = True
        for p in self.providers:
            if not p.initialize(session_id):
                success = False
        return success

    def store(self, entry: MemoryEntry) -> bool:
        results = [p.store(entry) for p in self.providers if hasattr(p, 'store')]
        self.network.emit("memory.stored", {
            "entry_id": entry.id, "type": entry.type
        })
        return any(results)

    def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        all_results = []
        for p in self.providers:
            try:
                results = p.recall(query, limit)
                all_results.extend(results)
            except NotImplementedError:
                pass
        all_results.sort(key=lambda e: e.importance, reverse=True)
        return all_results[:limit]

    def forget(self, entry_id: str) -> bool:
        results = [p.forget(entry_id) for p in self.providers if hasattr(p, 'forget')]
        return any(results)

    def shutdown_all(self) -> None:
        for p in self.providers:
            p.shutdown()

    def statistics(self) -> dict:
        stats = {}
        for p in self.providers:
            if hasattr(p, 'statistics'):
                stats[p.name()] = p.statistics()
        return stats


def create_memory(content: str, type_: str = "fact", source: str = "ciel",
                  importance: float = 0.5, tags: list[str] | None = None) -> MemoryEntry:
    return MemoryEntry(
        id=f"MEM-{uuid.uuid4().hex[:12]}",
        content=content, type=type_, source=source,
        importance=importance, tags=tags or [],
    )
