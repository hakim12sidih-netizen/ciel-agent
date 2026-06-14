"""
CIEL — KnowledgeGraph MemoryProvider.

Integrates the Kuzu-backed KnowledgeGraph into CIEL's MemoryProvider ABC.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from ciel.memory import MemoryProvider, MemoryEntry, MemoryManager
from ciel.memory.knowledge_graph.core import KnowledgeGraph, Entity, Relationship


def _mem_to_entity(entry: MemoryEntry) -> Entity:
    return Entity(
        id=f"mem:{entry.id}",
        type=f"memory:{entry.type}",
        name=entry.content[:80],
        properties={
            "content": entry.content,
            "source": entry.source,
            "importance": entry.importance,
            "tags": entry.tags,
        },
        created_at=entry.timestamp,
        updated_at=entry.timestamp,
    )


def _entity_to_mem(entity: Entity) -> MemoryEntry:
    props = entity.properties
    return MemoryEntry(
        id=entity.id.replace("mem:", "", 1) if entity.id.startswith("mem:") else entity.id,
        content=props.get("content", entity.name),
        type=entity.type.replace("memory:", "", 1) if entity.type.startswith("memory:") else entity.type,
        source=props.get("source", "knowledge_graph"),
        timestamp=entity.created_at,
        importance=props.get("importance", 0.5),
        tags=props.get("tags", []),
    )


class KnowledgeGraphProvider(MemoryProvider):
    """MemoryProvider backed by Kuzu KnowledgeGraph.

    Stores memory entries as Entity nodes and relationships between them.
    Enables graph traversal, path finding, and semantic search.
    """

    def __init__(self, db_path: str | Path = "~/.ciel/data/knowledge.db"):
        if str(db_path) == ":memory:":
            self._kg = KnowledgeGraph(":memory:")
        else:
            resolved = Path(db_path).expanduser().resolve()
            resolved.parent.mkdir(parents=True, exist_ok=True)
            self._kg = KnowledgeGraph(str(resolved))
        self._session_id: str | None = None

    def name(self) -> str:
        return "knowledge_graph"

    def initialize(self, session_id: str) -> bool:
        self._session_id = session_id
        session_entity = self._kg.get_entity(f"session:{session_id}")
        if session_entity is None:
            self._kg.create_entity(
                f"session:{session_id}",
                "session",
                f"Session {session_id[:8]}",
                {"created": time.time()},
            )
        return True

    def store(self, entry: MemoryEntry) -> bool:
        entity = _mem_to_entity(entry)
        self._kg.create_entity(entity.id, entity.type, entity.name, entity.properties,
                               upsert=True)
        if self._session_id:
            self._kg.create_relationship(
                f"session:{self._session_id}",
                entity.id,
                "contains",
                {"timestamp": time.time()},
            )
        return True

    def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        results = self._kg.search(query, limit=limit)
        return [_entity_to_mem(r.entity) for r in results]

    def forget(self, entry_id: str) -> bool:
        return self._kg.delete_entity(f"mem:{entry_id}")

    def list_by_type(self, type_: str, limit: int = 50) -> list[MemoryEntry]:
        entities = self._kg.list_entities(type=f"memory:{type_}", limit=limit)
        return [_entity_to_mem(e) for e in entities]

    def search_similar(self, query: str, threshold: float = 0.3,
                       limit: int = 10) -> list[MemoryEntry]:
        results = self._kg.search(query, limit=limit)
        return [_entity_to_mem(r.entity) for r in results if r.score >= threshold]

    def shutdown(self) -> None:
        self._kg.close()

    def statistics(self) -> dict:
        stats = self._kg.stats()
        stats["provider"] = "knowledge_graph"
        return stats
