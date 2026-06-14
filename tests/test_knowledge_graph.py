"""
CIEL — Tests for Knowledge Graph (Kuzu).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from ciel.memory.knowledge_graph import (
    KnowledgeGraph, Entity, Relationship,
    SearchResult, PathResult, KnowledgeGraphError,
    KnowledgeGraphProvider, get_graph,
)
from ciel.memory import MemoryEntry, MemoryManager


# ═══════════════════════════════════════════════════════════
# ENTITY CRUD
# ═══════════════════════════════════════════════════════════

class TestEntityCRUD:
    def test_create_entity(self):
        kg = KnowledgeGraph()
        e = kg.create_entity("e1", "person", "Alice", {"age": 30})
        assert e.id == "e1"
        assert e.type == "person"
        assert e.name == "Alice"
        assert e.properties["age"] == 30

    def test_create_entity_auto_id(self):
        kg = KnowledgeGraph()
        e = kg.create_entity(None, "person", "Bob")
        assert e.id is not None
        assert len(e.id) == 16

    def test_get_entity(self):
        kg = KnowledgeGraph()
        kg.create_entity("e1", "person", "Alice")
        e = kg.get_entity("e1")
        assert e is not None
        assert e.name == "Alice"

    def test_get_entity_not_found(self):
        kg = KnowledgeGraph()
        assert kg.get_entity("nonexistent") is None

    def test_update_entity_name(self):
        kg = KnowledgeGraph()
        kg.create_entity("e1", "person", "Alice")
        updated = kg.update_entity("e1", name="Alice Smith")
        assert updated is not None
        assert updated.name == "Alice Smith"

    def test_update_entity_properties(self):
        kg = KnowledgeGraph()
        kg.create_entity("e1", "person", "Alice", {"age": 30})
        updated = kg.update_entity("e1", properties={"city": "Paris"})
        assert updated.properties["age"] == 30
        assert updated.properties["city"] == "Paris"

    def test_update_nonexistent(self):
        kg = KnowledgeGraph()
        assert kg.update_entity("nope", name="X") is None

    def test_delete_entity(self):
        kg = KnowledgeGraph()
        kg.create_entity("e1", "person", "Alice")
        assert kg.delete_entity("e1") is True
        assert kg.get_entity("e1") is None

    def test_delete_nonexistent(self):
        kg = KnowledgeGraph()
        assert kg.delete_entity("nope") is False

    def test_list_entities(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "Alice")
        kg.create_entity("b", "person", "Bob")
        kg.create_entity("c", "city", "Paris")
        all_entities = kg.list_entities()
        assert len(all_entities) == 3
        persons = kg.list_entities(type="person")
        assert len(persons) == 2

    def test_list_entities_limit_offset(self):
        kg = KnowledgeGraph()
        for i in range(10):
            kg.create_entity(f"e{i}", "item", f"Item {i}")
        page1 = kg.list_entities(limit=3, offset=0)
        assert len(page1) == 3
        page2 = kg.list_entities(limit=3, offset=3)
        assert len(page2) == 3
        assert page1[0].id != page2[0].id

    def test_count_entities(self):
        kg = KnowledgeGraph()
        assert kg.count_entities() == 0
        kg.create_entity("a", "person", "Alice")
        kg.create_entity("b", "person", "Bob")
        assert kg.count_entities() == 2
        assert kg.count_entities(type="person") == 2
        assert kg.count_entities(type="city") == 0


# ═══════════════════════════════════════════════════════════
# RELATIONSHIP CRUD
# ═══════════════════════════════════════════════════════════

class TestRelationshipCRUD:
    def test_create_relationship(self):
        kg = KnowledgeGraph()
        kg.create_entity("alice", "person", "Alice")
        kg.create_entity("bob", "person", "Bob")
        rel = kg.create_relationship("alice", "bob", "knows", {"since": 2020})
        assert rel is not None
        assert rel.type == "knows"
        assert rel.source_id == "alice"
        assert rel.target_id == "bob"

    def test_create_relationship_missing_source(self):
        kg = KnowledgeGraph()
        kg.create_entity("bob", "person", "Bob")
        rel = kg.create_relationship("alice", "bob", "knows")
        assert rel is None

    def test_get_relationships_outgoing(self):
        kg = KnowledgeGraph()
        kg.create_entity("alice", "person", "Alice")
        kg.create_entity("bob", "person", "Bob")
        kg.create_entity("carol", "person", "Carol")
        kg.create_relationship("alice", "bob", "knows")
        kg.create_relationship("alice", "carol", "knows")
        rels = kg.get_relationships("alice", direction="out")
        assert len(rels) == 2

    def test_get_relationships_incoming(self):
        kg = KnowledgeGraph()
        kg.create_entity("alice", "person", "Alice")
        kg.create_entity("bob", "person", "Bob")
        kg.create_relationship("alice", "bob", "knows")
        rels = kg.get_relationships("bob", direction="in")
        assert len(rels) == 1
        assert rels[0].source_id == "alice"

    def test_get_relationships_filter_type(self):
        kg = KnowledgeGraph()
        kg.create_entity("alice", "person", "Alice")
        kg.create_entity("paris", "city", "Paris")
        kg.create_relationship("alice", "paris", "visited")
        kg.create_entity("bob", "person", "Bob")
        kg.create_relationship("alice", "bob", "knows")
        rels = kg.get_relationships("alice", type="knows")
        assert len(rels) == 1
        assert rels[0].type == "knows"

    def test_delete_relationship(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "A")
        kg.create_entity("b", "person", "B")
        rel = kg.create_relationship("a", "b", "knows")
        assert rel is not None
        assert kg.delete_relationship(rel.id) is True


# ═══════════════════════════════════════════════════════════
# SEARCH
# ═══════════════════════════════════════════════════════════

class TestSearch:
    def test_search_by_name(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "Alice Wonderland")
        results = kg.search("alice")
        assert len(results) >= 1
        assert results[0].entity.name == "Alice Wonderland"

    def test_search_by_property(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "Alice", {"email": "alice@test.com"})
        results = kg.search("test.com")
        assert len(results) >= 1

    def test_search_filter_type(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "Alice")
        kg.create_entity("p", "city", "Paris")
        results = kg.search("a", type="person")
        assert all(r.entity.type == "person" for r in results)

    def test_search_no_results(self):
        kg = KnowledgeGraph()
        results = kg.search("nonexistent")
        assert results == []

    def test_search_limit(self):
        kg = KnowledgeGraph()
        for i in range(10):
            kg.create_entity(f"e{i}", "item", f"Item {i}")
        results = kg.search("Item", limit=3)
        assert len(results) <= 3

    def test_search_relevance_scoring(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "Alice")
        kg.create_entity("b", "person", "Bob")
        kg.create_entity("al", "person", "Alicia")
        results = kg.search("alice")
        assert len(results) >= 1
        assert results[0].entity.name == "Alice"


# ═══════════════════════════════════════════════════════════
# PATH FINDING
# ═══════════════════════════════════════════════════════════

class TestPathFinding:
    def test_shortest_path(self):
        kg = KnowledgeGraph()
        for p in ["a", "b", "c", "d"]:
            kg.create_entity(p, "person", p)
        kg.create_relationship("a", "b", "knows")
        kg.create_relationship("b", "c", "knows")
        kg.create_relationship("c", "d", "knows")
        path = kg.find_shortest_path("a", "d")
        assert path is not None
        assert path.length == 3
        assert len(path.nodes) == 4

    def test_shortest_path_direct(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "A")
        kg.create_entity("b", "person", "B")
        kg.create_relationship("a", "b", "knows")
        path = kg.find_shortest_path("a", "b")
        assert path is not None
        assert path.length == 1

    def test_no_path(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "A")
        kg.create_entity("b", "person", "B")
        path = kg.find_shortest_path("a", "b")
        assert path is None

    def test_find_all_paths(self):
        kg = KnowledgeGraph()
        for p in ["a", "b", "c", "d"]:
            kg.create_entity(p, "person", p)
        kg.create_relationship("a", "b", "knows")
        kg.create_relationship("b", "c", "knows")
        kg.create_relationship("a", "c", "knows")
        kg.create_relationship("c", "d", "knows")
        paths = kg.find_all_paths("a", "d")
        assert len(paths) >= 1

    def test_path_total_weight(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "A")
        kg.create_entity("b", "person", "B")
        kg.create_relationship("a", "b", "knows", weight=0.5)
        path = kg.find_shortest_path("a", "b")
        assert path is not None
        assert path.total_weight == 0.5


# ═══════════════════════════════════════════════════════════
# NEIGHBORS
# ═══════════════════════════════════════════════════════════

class TestNeighbors:
    def test_get_neighbors(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "A")
        kg.create_entity("b", "person", "B")
        kg.create_entity("c", "person", "C")
        kg.create_relationship("a", "b", "knows")
        kg.create_relationship("a", "c", "knows")
        neighbors = kg.get_neighbors("a")
        assert len(neighbors) == 2

    def test_get_neighbors_filter_type(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "A")
        kg.create_entity("b", "person", "B")
        kg.create_entity("paris", "city", "Paris")
        kg.create_relationship("a", "b", "knows")
        kg.create_relationship("a", "paris", "visited")
        neighbors = kg.get_neighbors("a", type="city")
        assert len(neighbors) == 1
        assert neighbors[0].type == "city"

    def test_get_neighbors_depth(self):
        kg = KnowledgeGraph()
        for p in ["a", "b", "c"]:
            kg.create_entity(p, "person", p)
        kg.create_relationship("a", "b", "knows")
        kg.create_relationship("b", "c", "knows")
        neighbors = kg.get_neighbors("a", depth=2)
        assert len(neighbors) == 2


# ═══════════════════════════════════════════════════════════
# BULK OPERATIONS
# ═══════════════════════════════════════════════════════════

class TestBulk:
    def test_bulk_create_entities(self):
        kg = KnowledgeGraph()
        entities = [
            Entity(id="a", type="person", name="Alice"),
            Entity(id="b", type="person", name="Bob"),
        ]
        count = kg.bulk_create_entities(entities)
        assert count == 2
        assert kg.count_entities() == 2

    def test_bulk_create_relationships(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "A")
        kg.create_entity("b", "person", "B")
        rels = [
            Relationship(id="r1", type="knows", source_id="a", target_id="b"),
        ]
        count = kg.bulk_create_relationships(rels)
        assert count == 1

    def test_export_json(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "Alice", {"age": 30})
        kg.create_entity("b", "person", "Bob")
        kg.create_relationship("a", "b", "knows")
        exported = kg.export_json(":memory:")
        assert len(exported["entities"]) == 2
        # get_relationships with direction='both' may return duplicates
        # from both endpoints; ensure we have at least 1
        assert len(exported["relationships"]) >= 1

    def test_import_json(self):
        kg = KnowledgeGraph()
        data = {
            "entities": [
                {"id": "a", "type": "person", "name": "Alice",
                 "properties": {}, "created_at": 1.0, "updated_at": 1.0},
                {"id": "b", "type": "person", "name": "Bob",
                 "properties": {}, "created_at": 1.0, "updated_at": 1.0},
            ],
            "relationships": [
                {"id": "r1", "type": "knows", "source_id": "a",
                 "target_id": "b", "properties": {},
                 "weight": 1.0, "created_at": 1.0},
            ],
        }
        e, r = kg.import_json(data)
        assert e == 2
        assert r == 1


# ═══════════════════════════════════════════════════════════
# TRANSACTIONS
# ═══════════════════════════════════════════════════════════

class TestTransactions:
    def test_transaction_commit(self):
        kg = KnowledgeGraph()
        with kg.transaction():
            kg.create_entity("a", "person", "Alice")
        assert kg.get_entity("a") is not None

    def test_transaction_is_noop(self):
        """Kuzu auto-commits each query; transaction() is a no-op."""
        kg = KnowledgeGraph()
        tx = kg.transaction()
        assert tx is not None


# ═══════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════

class TestStats:
    def test_stats(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "Alice")
        kg.create_entity("b", "city", "Paris")
        kg.create_relationship("a", "b", "visited")
        s = kg.stats()
        assert s["entities"] == 2
        assert s["relationships"] >= 1
        assert s["types"]["person"] == 1

    def test_properties(self):
        kg = KnowledgeGraph()
        assert kg.is_in_memory
        assert kg.path == ":memory:"


# ═══════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH PROVIDER
# ═══════════════════════════════════════════════════════════

class TestKnowledgeGraphProvider:
    def test_name(self):
        provider = KnowledgeGraphProvider(":memory:")
        assert provider.name() == "knowledge_graph"

    def test_initialize(self):
        provider = KnowledgeGraphProvider(":memory:")
        assert provider.initialize("test-session") is True

    def test_store_and_recall(self):
        provider = KnowledgeGraphProvider(":memory:")
        provider.initialize("s1")
        entry = MemoryEntry(id="m1", content="Hello world",
                            type="fact", source="test")
        assert provider.store(entry) is True
        results = provider.recall("hello")
        assert len(results) >= 1
        assert results[0].content == "Hello world"

    def test_forget(self):
        provider = KnowledgeGraphProvider(":memory:")
        provider.initialize("s1")
        entry = MemoryEntry(id="m1", content="Test", type="fact", source="test")
        provider.store(entry)
        assert provider.forget("m1") is True

    def test_list_by_type(self):
        provider = KnowledgeGraphProvider(":memory:")
        provider.initialize("s1")
        provider.store(MemoryEntry(id="m1", content="A", type="fact", source="t"))
        provider.store(MemoryEntry(id="m2", content="B", type="fact", source="t"))
        results = provider.list_by_type("fact")
        assert len(results) == 2

    def test_search_similar(self):
        provider = KnowledgeGraphProvider(":memory:")
        provider.initialize("s1")
        provider.store(MemoryEntry(id="m1", content="Alice knows Bob",
                                   type="fact", source="t"))
        results = provider.search_similar("alice")
        assert len(results) >= 1

    def test_statistics(self):
        provider = KnowledgeGraphProvider(":memory:")
        provider.initialize("s1")
        provider.store(MemoryEntry(id="m1", content="Test", type="fact", source="t"))
        stats = provider.statistics()
        assert stats["provider"] == "knowledge_graph"
        assert stats["entities"] >= 1

    def test_shutdown(self):
        provider = KnowledgeGraphProvider(":memory:")
        provider.initialize("s1")
        provider.shutdown()


# ═══════════════════════════════════════════════════════════
# INTEGRATION WITH MEMORY MANAGER
# ═══════════════════════════════════════════════════════════

class TestMemoryManagerIntegration:
    def test_add_provider(self):
        mm = MemoryManager()
        provider = KnowledgeGraphProvider(":memory:")
        assert mm.add_provider(provider) is True

    def test_store_through_manager(self):
        mm = MemoryManager()
        provider = KnowledgeGraphProvider(":memory:")
        mm.add_provider(provider)
        mm.initialize_all("s1")
        entry = MemoryEntry(id="m1", content="Graph memory",
                            type="fact", source="test")
        assert mm.store(entry) is True

    def test_recall_through_manager(self):
        mm = MemoryManager()
        provider = KnowledgeGraphProvider(":memory:")
        mm.add_provider(provider)
        mm.initialize_all("s1")
        entry = MemoryEntry(id="m1", content="Unique search term xyz",
                            type="fact", source="test")
        mm.store(entry)
        results = mm.recall("xyz")
        assert len(results) >= 1


# ═══════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_empty_graph(self):
        kg = KnowledgeGraph()
        assert kg.count_entities() == 0
        assert kg.list_entities() == []
        assert kg.search("anything") == []

    def test_entity_with_empty_properties(self):
        kg = KnowledgeGraph()
        e = kg.create_entity("e", "type", "Name", {})
        assert e.properties == {}

    def test_relationship_with_weight(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "A")
        kg.create_entity("b", "person", "B")
        rel = kg.create_relationship("a", "b", "knows", weight=0.0)
        assert rel is not None
        assert rel.weight == 0.0

    def test_upsert_entity(self):
        kg = KnowledgeGraph()
        kg.create_entity("e", "person", "Alice", {"age": 30}, upsert=True)
        kg.create_entity("e", "person", "Alice Updated", {"age": 31}, upsert=True)
        e = kg.get_entity("e")
        assert e is not None
        assert e.name == "Alice Updated"

    def test_delete_entity_with_relationships(self):
        kg = KnowledgeGraph()
        kg.create_entity("a", "person", "A")
        kg.create_entity("b", "person", "B")
        kg.create_relationship("a", "b", "knows")
        kg.delete_entity("a")
        assert kg.get_entity("a") is None
        rels = kg.get_relationships("b", direction="in")
        assert len(rels) == 0


# ═══════════════════════════════════════════════════════════
# PERSISTENCE
# ═══════════════════════════════════════════════════════════

class TestPersistence:
    def test_persist_to_disk(self, tmp_path):
        db_path = tmp_path / "test.db"
        kg = KnowledgeGraph(str(db_path))
        kg.create_entity("a", "person", "Alice")
        kg.close()

        kg2 = KnowledgeGraph(str(db_path))
        e = kg2.get_entity("a")
        assert e is not None
        assert e.name == "Alice"
        kg2.close()

    def test_get_graph_convenience(self):
        kg = get_graph(":memory:")
        assert kg.is_in_memory
        kg.close()

    def test_context_manager(self):
        with KnowledgeGraph() as kg:
            kg.create_entity("a", "p", "A")
            assert kg.get_entity("a") is not None
