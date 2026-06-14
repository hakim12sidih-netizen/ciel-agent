"""
CIEL — Knowledge Graph Core (Kuzu backend).

Embedded property graph with Cypher, ACID, schema enforcement,
entity/relationship CRUD, fuzzy search, path finding, bulk ops.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import kuzu

# ── Types ────────────────────────────────────────────────

EntityType = str
RelationType = str


@dataclass
class Entity:
    id: str
    type: EntityType
    name: str
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Entity:
        return cls(**d)


@dataclass
class Relationship:
    id: str
    type: RelationType
    source_id: str
    target_id: str
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Relationship:
        return cls(**d)


@dataclass
class SearchResult:
    entity: Entity
    score: float = 0.0
    matched_property: str = ""


@dataclass
class PathResult:
    nodes: list[Entity]
    edges: list[Relationship]
    length: int = 0
    total_weight: float = 0.0


class KnowledgeGraphError(Exception):
    pass


# ── Schema ───────────────────────────────────────────────

NODE_TABLE = "Entity"
EDGE_TABLE = "Relationship"


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


def _serialize(v: Any) -> str:
    return json.dumps(v, default=str)


def _deserialize(s: str) -> dict:
    return json.loads(s) if s else {}


def _node_kwargs(e: Entity) -> dict[str, Any]:
    """Parameter dict for CREATE/MERGE/SET with Kuzu-compatible names."""
    return {
        "id": e.id,
        "type": e.type,
        "name": e.name,
        "props": _serialize(e.properties),
        "ca": e.created_at,
        "ua": e.updated_at,
    }


def _entity_from_struct(s: dict) -> Entity:
    return Entity(
        id=s["id"],
        type=s["type"],
        name=s["name"],
        properties=_deserialize(s.get("properties", "{}")),
        created_at=s.get("created_at", 0.0),
        updated_at=s.get("updated_at", 0.0),
    )


def _rel_from_struct(r: dict, sid: str, tid: str) -> Relationship:
    return Relationship(
        id=r["id"],
        type=r["type"],
        source_id=sid,
        target_id=tid,
        properties=_deserialize(r.get("properties", "{}")),
        weight=r.get("weight", 1.0),
        created_at=r.get("created_at", 0.0),
    )


# ── Knowledge Graph ─────────────────────────────────────


class KnowledgeGraph:
    def __init__(self, db_path: str | Path = ":memory:"):
        self._db_path = str(Path(db_path).resolve()) if str(db_path) != ":memory:" else ":memory:"
        self._db = kuzu.Database(self._db_path)
        self._conn = kuzu.Connection(self._db)
        self._init_schema()

    def _init_schema(self) -> None:
        for stmt in [
            f"CREATE NODE TABLE IF NOT EXISTS {NODE_TABLE}("
            f"id STRING, type STRING, name STRING, properties STRING, "
            f"created_at DOUBLE, updated_at DOUBLE, PRIMARY KEY(id))",
            f"CREATE REL TABLE IF NOT EXISTS {EDGE_TABLE}("
            f"FROM {NODE_TABLE} TO {NODE_TABLE}, "
            f"id STRING, type STRING, properties STRING, "
            f"weight DOUBLE, created_at DOUBLE)",
        ]:
            try:
                self._conn.execute(stmt)
            except RuntimeError:
                pass

    @property
    def path(self) -> str:
        return self._db_path

    @property
    def is_in_memory(self) -> bool:
        return self._db_path == ":memory:"

    # ── Entity CRUD ──────────────────────────────────────

    def create_entity(self, id: str | None, type: EntityType, name: str,
                      properties: dict[str, Any] | None = None,
                      upsert: bool = False) -> Entity:
        entity = Entity(
            id=id or _new_id(),
            type=type, name=name,
            properties=properties or {},
        )
        kw = _node_kwargs(entity)
        if upsert:
            self._conn.execute(
                f"MERGE (e:{NODE_TABLE} {{id: $id}}) "
                f"SET e.type = $type, e.name = $name, "
                f"e.properties = $props, e.created_at = $ca, e.updated_at = $ua",
                kw,
            )
        else:
            self._conn.execute(
                f"CREATE (e:{NODE_TABLE} {{id: $id, type: $type, name: $name, "
                f"properties: $props, created_at: $ca, updated_at: $ua}})",
                kw,
            )
        return entity

    def get_entity(self, entity_id: str) -> Entity | None:
        r = self._conn.execute(
            f"MATCH (e:{NODE_TABLE}) WHERE e.id = $id RETURN e",
            {"id": entity_id},
        )
        if not r.has_next():
            return None
        return _entity_from_struct(r.get_next()[0])

    def update_entity(self, entity_id: str,
                      properties: dict[str, Any] | None = None,
                      name: str | None = None) -> Entity | None:
        existing = self.get_entity(entity_id)
        if existing is None:
            return None
        if name is not None:
            existing.name = name
        if properties is not None:
            existing.properties.update(properties)
        existing.updated_at = time.time()
        kw = _node_kwargs(existing)
        self._conn.execute(
            f"MATCH (e:{NODE_TABLE}) WHERE e.id = $id "
            f"SET e.name = $name, e.properties = $props, e.updated_at = $ua",
            {"id": kw["id"], "name": kw["name"],
             "props": kw["props"], "ua": kw["ua"]},
        )
        return existing

    def delete_entity(self, entity_id: str) -> bool:
        self._conn.execute(
            f"MATCH (s:{NODE_TABLE})-[r:{EDGE_TABLE}]->(t:{NODE_TABLE}) "
            f"WHERE s.id = $id OR t.id = $id DELETE r",
            {"id": entity_id},
        )
        r = self._conn.execute(
            f"MATCH (e:{NODE_TABLE}) WHERE e.id = $id DELETE e RETURN count(*)",
            {"id": entity_id},
        )
        return r.has_next() and r.get_next()[0] > 0

    def list_entities(self, type: EntityType | None = None,
                      limit: int = 100, offset: int = 0) -> list[Entity]:
        if type:
            r = self._conn.execute(
                f"MATCH (e:{NODE_TABLE}) WHERE e.type = $type "
                f"RETURN e SKIP $offset LIMIT $limit",
                {"type": type, "offset": offset, "limit": limit},
            )
        else:
            r = self._conn.execute(
                f"MATCH (e:{NODE_TABLE}) RETURN e SKIP $offset LIMIT $limit",
                {"offset": offset, "limit": limit},
            )
        out = []
        while r.has_next():
            out.append(_entity_from_struct(r.get_next()[0]))
        return out

    def count_entities(self, type: EntityType | None = None) -> int:
        if type:
            r = self._conn.execute(
                f"MATCH (e:{NODE_TABLE}) WHERE e.type = $type RETURN count(*)",
                {"type": type},
            )
        else:
            r = self._conn.execute(f"MATCH (e:{NODE_TABLE}) RETURN count(*)")
        return r.get_next()[0] if r.has_next() else 0

    # ── Relationship CRUD ────────────────────────────────

    def create_relationship(self, source_id: str, target_id: str,
                            type: RelationType,
                            properties: dict[str, Any] | None = None,
                            weight: float = 1.0) -> Relationship | None:
        if self.get_entity(source_id) is None or self.get_entity(target_id) is None:
            return None
        rel_id = _new_id()
        self._conn.execute(
            f"MATCH (s:{NODE_TABLE}), (t:{NODE_TABLE}) "
            f"WHERE s.id = $sid AND t.id = $tid "
            f"CREATE (s)-[r:{EDGE_TABLE} {{id: $rid, type: $rt, "
            f"properties: $props, weight: $w, created_at: $ca}}]->(t)",
            {
                "sid": source_id, "tid": target_id,
                "rid": rel_id, "rt": type,
                "props": _serialize(properties or {}),
                "w": weight, "ca": time.time(),
            },
        )
        return Relationship(
            id=rel_id, type=type,
            source_id=source_id, target_id=target_id,
            properties=properties or {}, weight=weight,
        )

    def get_relationships(self, entity_id: str,
                          direction: str = "both",
                          type: RelationType | None = None,
                          limit: int = 50) -> list[Relationship]:
        if direction == "out":
            clause = f"MATCH (s:{NODE_TABLE})-[r:{EDGE_TABLE}]->(t:{NODE_TABLE}) WHERE s.id = $id"
        elif direction == "in":
            clause = f"MATCH (s:{NODE_TABLE})-[r:{EDGE_TABLE}]->(t:{NODE_TABLE}) WHERE t.id = $id"
        else:
            clause = (f"MATCH (s:{NODE_TABLE})-[r:{EDGE_TABLE}]->(t:{NODE_TABLE}) "
                      f"WHERE (s.id = $id OR t.id = $id)")
        params: dict[str, Any] = {"id": entity_id}
        if type:
            clause += " AND r.type = $rt"
            params["rt"] = type
        clause += " RETURN s.id, r, t.id"

        raw = self._conn.execute(clause, params)
        rels = []
        while raw.has_next():
            row = raw.get_next()
            sid, rel_struct, tid = row[0], row[1], row[2]
            rels.append(_rel_from_struct(rel_struct, sid, tid))
        return rels

    def delete_relationship(self, rel_id: str) -> bool:
        r = self._conn.execute(
            f"MATCH (s:{NODE_TABLE})-[r:{EDGE_TABLE}]->(t:{NODE_TABLE}) "
            f"WHERE r.id = $id DELETE r RETURN count(*)",
            {"id": rel_id},
        )
        return r.has_next() and r.get_next()[0] > 0

    # ── Search ───────────────────────────────────────────

    def search(self, query: str, type: EntityType | None = None,
               limit: int = 20) -> list[SearchResult]:
        ql = query.lower()
        if type:
            r = self._conn.execute(
                f"MATCH (e:{NODE_TABLE}) WHERE e.type = $type "
                f"AND (LOWER(e.name) CONTAINS $q "
                f"OR LOWER(e.properties) CONTAINS $q) "
                f"RETURN e LIMIT $limit",
                {"q": ql, "type": type, "limit": limit},
            )
        else:
            r = self._conn.execute(
                f"MATCH (e:{NODE_TABLE}) WHERE LOWER(e.name) CONTAINS $q "
                f"OR LOWER(e.properties) CONTAINS $q "
                f"RETURN e LIMIT $limit",
                {"q": ql, "limit": limit},
            )
        results = []
        while r.has_next():
            entity = _entity_from_struct(r.get_next()[0])
            score = 0.0
            if ql in entity.name.lower():
                score += 1.0
                if entity.name.lower().startswith(ql):
                    score += 0.5
            ps = json.dumps(entity.properties).lower()
            if ql in ps:
                score += 0.3 * (ps.count(ql) / max(1, len(ps)))
            results.append(SearchResult(
                entity=entity, score=score,
                matched_property="name" if ql in entity.name.lower() else "properties",
            ))
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    # ── Path finding ─────────────────────────────────────

    def find_shortest_path(self, source_id: str, target_id: str,
                           max_depth: int = 5) -> PathResult | None:
        try:
            r = self._conn.execute(
                f"MATCH p = (s:{NODE_TABLE})-[{EDGE_TABLE}*1..{max_depth}]-(t:{NODE_TABLE}) "
                f"WHERE s.id = $sid AND t.id = $tid AND s.id <> t.id "
                f"RETURN nodes(p) AS ns, relationships(p) AS rs, length(p) AS len "
                f"ORDER BY len LIMIT 1",
                {"sid": source_id, "tid": target_id},
            )
            if not r.has_next():
                return None
            row = r.get_next()
            raw_nodes = row[0]
            raw_edges = row[1]
            path_len = row[2]
            nodes = [_entity_from_struct(n) for n in raw_nodes]
            edges = []
            for i, e in enumerate(raw_edges):
                src_id = nodes[i].id
                tgt_id = nodes[i + 1].id
                edges.append(_rel_from_struct(e, src_id, tgt_id))
            return PathResult(
                nodes=nodes, edges=edges, length=path_len,
                total_weight=sum(e.weight for e in edges),
            )
        except RuntimeError as e:
            msg = str(e).lower()
            if "no table" in msg or "no intermediate" in msg:
                return None
            raise

    def find_all_paths(self, source_id: str, target_id: str,
                       max_depth: int = 3) -> list[PathResult]:
        r = self._conn.execute(
            f"MATCH p = (s:{NODE_TABLE})-[{EDGE_TABLE}*1..{max_depth}]-(t:{NODE_TABLE}) "
            f"WHERE s.id = $sid AND t.id = $tid AND s.id <> t.id "
            f"RETURN nodes(p) AS ns, relationships(p) AS rs, length(p) AS len "
            f"LIMIT 50",
            {"sid": source_id, "tid": target_id},
        )
        paths = []
        while r.has_next():
            row = r.get_next()
            raw_nodes = row[0]
            raw_edges = row[1]
            nodes = [_entity_from_struct(n) for n in raw_nodes]
            edges = [_rel_from_struct(e, e["_src"], e["_dst"]) for e in raw_edges]
            paths.append(PathResult(
                nodes=nodes, edges=edges, length=row[2],
                total_weight=sum(e.weight for e in edges),
            ))
        paths.sort(key=lambda p: p.total_weight)
        return paths

    # ── Neighbors ────────────────────────────────────────

    def get_neighbors(self, entity_id: str, depth: int = 1,
                      type: EntityType | None = None,
                      limit: int = 50) -> list[Entity]:
        if type:
            r = self._conn.execute(
                f"MATCH (e:{NODE_TABLE})-[{EDGE_TABLE}*1..{depth}]-(n:{NODE_TABLE}) "
                f"WHERE e.id = $id AND n.type = $type AND n.id <> $id "
                f"RETURN DISTINCT n LIMIT $limit",
                {"id": entity_id, "type": type, "limit": limit},
            )
        else:
            r = self._conn.execute(
                f"MATCH (e:{NODE_TABLE})-[{EDGE_TABLE}*1..{depth}]-(n:{NODE_TABLE}) "
                f"WHERE e.id = $id AND n.id <> $id "
                f"RETURN DISTINCT n LIMIT $limit",
                {"id": entity_id, "limit": limit},
            )
        out = []
        while r.has_next():
            out.append(_entity_from_struct(r.get_next()[0]))
        return out

    # ── Bulk ─────────────────────────────────────────────

    def bulk_create_entities(self, entities: list[Entity]) -> int:
        count = 0
        for e in entities:
            try:
                self.create_entity(e.id, e.type, e.name, e.properties)
                count += 1
            except RuntimeError:
                pass
        return count

    def bulk_create_relationships(self, rels: list[Relationship]) -> int:
        count = 0
        for r in rels:
            if self.create_relationship(r.source_id, r.target_id, r.type,
                                        r.properties, r.weight):
                count += 1
        return count

    def export_json(self, path: str | Path | None = None) -> dict:
        entities = self.list_entities(limit=10000)
        all_rels: list[Relationship] = []
        for e in entities:
            all_rels.extend(self.get_relationships(e.id, limit=100))
        return {
            "entities": [e.to_dict() for e in entities],
            "relationships": [r.to_dict() for r in all_rels],
        }

    def import_json(self, data: dict) -> tuple[int, int]:
        e = [Entity.from_dict(d) for d in data.get("entities", [])]
        r = [Relationship.from_dict(d) for d in data.get("relationships", [])]
        return self.bulk_create_entities(e), self.bulk_create_relationships(r)

    # ── Stats ────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "entities": self.count_entities(),
            "relationships": self._count_relationships(),
            "types": self._entity_type_counts(),
        }

    def _count_relationships(self) -> int:
        r = self._conn.execute(f"MATCH ()-[r:{EDGE_TABLE}]-() RETURN count(*)")
        return r.get_next()[0] if r.has_next() else 0

    def _entity_type_counts(self) -> dict[str, int]:
        r = self._conn.execute(
            f"MATCH (e:{NODE_TABLE}) RETURN e.type AS t, count(*) AS c",
        )
        counts: dict[str, int] = {}
        while r.has_next():
            row = r.get_next()
            counts[row[0]] = row[1]
        return counts

    # ── Transactions ─────────────────────────────────────

    def transaction(self) -> KnowledgeGraphTx:
        return KnowledgeGraphTx()

    # ── Lifecycle ────────────────────────────────────────

    def close(self) -> None:
        self._conn.close()
        self._db.close()

    def __enter__(self) -> KnowledgeGraph:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class KnowledgeGraphTx:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: Any) -> None:
        pass
