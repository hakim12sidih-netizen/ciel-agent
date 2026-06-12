"""
CIEL v∞.8 — DIMENSION LIII : AKASHIC.
Mémoire collective de toutes les instances CIEL.

Concept : Mémoire collective distribuée (DAG + IPFS) accessible à
toutes les instances. Couches : substrat (ledger), sémantique (vecteurs),
narrative (récit collectif). Émergence de patterns inter-instances.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class AkashicMemory:
    id: str
    instance_id: str
    content: dict
    embedding: list[float] = field(default_factory=list)
    timestamp: float = 0.0
    hash: str = ""
    tier: str = "C"
    signatures: list[str] = field(default_factory=list)
    is_poison: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()
        if not self.hash:
            raw = json.dumps(self.content, sort_keys=True)
            self.hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {"id": self.id, "instance": self.instance_id,
                "timestamp": self.timestamp, "tier": self.tier,
                "poison": self.is_poison, "hash": self.hash}


@dataclass(slots=True)
class CollectivePattern:
    id: str
    description: str
    frequency: int = 0
    confidence: float = 0.0
    source_count: int = 0


class AkashicEngine:
    """Mémoire collective Akashic — toutes instances partagent."""

    def __init__(self):
        self.memories: dict[str, AkashicMemory] = {}
        self.patterns: dict[str, CollectivePattern] = {}
        self.network = LeaderNetwork()
        self._instance_id = f"CIEL-{uuid.uuid4().hex[:8]}"

    def store(self, content: dict, tier: str = "C",
              instance_id: str | None = None) -> AkashicMemory:
        m = AkashicMemory(
            id=f"AKA-{uuid.uuid4().hex[:12]}",
            instance_id=instance_id or self._instance_id,
            content=content, tier=tier,
            embedding=self._compute_embedding(content),
        )
        if self._detect_poison(m):
            m.is_poison = True
        else:
            self.memories[m.id] = m
            self._update_patterns(m)
        return m

    def _compute_embedding(self, content: dict) -> list[float]:
        raw = json.dumps(content, sort_keys=True)
        h = hashlib.sha256(raw.encode()).digest()
        return [b / 255.0 for b in h[:8]]

    def _detect_poison(self, m: AkashicMemory) -> bool:
        return "poison" in str(m.content).lower() or not m.content

    def _update_patterns(self, m: AkashicMemory):
        desc = str(m.content)[:60]
        existing = next((p for p in self.patterns.values()
                        if p.description == desc), None)
        if existing is None:
            p = CollectivePattern(
                id=f"PAT-{uuid.uuid4().hex[:12]}",
                description=desc, frequency=1,
                confidence=0.5, source_count=1,
            )
            self.patterns[p.id] = p
        else:
            existing.frequency += 1
            existing.source_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.05)

    def query(self, keyword: str) -> list[dict]:
        results = []
        for m in self.memories.values():
            if keyword.lower() in json.dumps(m.content).lower():
                results.append(m.to_dict())
        results.sort(key=lambda r: r["timestamp"], reverse=True)
        return results[:10]

    def emergent_patterns(self, min_confidence: float = 0.3) -> list[dict]:
        return [p for p in self.patterns.values()
                if p.confidence >= min_confidence]

    def get_stats(self) -> dict:
        return {
            "memories": len(self.memories),
            "patterns": len(self.patterns),
            "instance": self._instance_id,
            "poison_detected": sum(1 for m in self.memories.values()
                                    if m.is_poison),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "store":
            m = self.store(
                input_data.get("content", {}),
                input_data.get("tier", "C"),
                input_data.get("instance_id"),
            )
            return {"status": "ok", "memory": m.to_dict()}
        elif action == "query":
            return {"status": "ok",
                    "results": self.query(input_data.get("keyword", ""))}
        elif action == "patterns":
            return {"status": "ok",
                    "patterns": self.emergent_patterns(
                        input_data.get("min_confidence", 0.3))}
        return {"status": "ok", "memories": len(self.memories)}
