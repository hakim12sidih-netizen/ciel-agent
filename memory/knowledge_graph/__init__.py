"""
CIEL — Knowledge Graph (Kuzu).

Embedded property graph with Cypher queries, ACID transactions,
and schema enforcement for entities, relationships, and metadata.
"""
from __future__ import annotations

from ciel.memory.knowledge_graph.core import (
    KnowledgeGraph,
    Entity,
    Relationship,
    EntityType,
    RelationType,
    SearchResult,
    PathResult,
    KnowledgeGraphError,
)
from ciel.memory.knowledge_graph.provider import KnowledgeGraphProvider


def get_graph(db_path: str | None = None) -> KnowledgeGraph:
    """Get or create a KnowledgeGraph instance.

    Args:
        db_path: Path to Kuzu DB file. Defaults to ~/.ciel/data/knowledge.db
    """
    if db_path is None:
        from pathlib import Path
        db_path = str(Path.home() / ".ciel" / "data" / "knowledge.db")
    return KnowledgeGraph(db_path)


__all__ = [
    "KnowledgeGraph",
    "Entity",
    "Relationship",
    "EntityType",
    "RelationType",
    "SearchResult",
    "PathResult",
    "KnowledgeGraphError",
    "KnowledgeGraphProvider",
    "get_graph",
]
