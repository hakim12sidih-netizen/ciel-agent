"""
CIEL v∞.8 — DIMENSION LXVI : CIEL-CRYSTAL.
Cristallisation des savoirs absolus — connaissances indestructibles.

Concept : Certaines connaissances sont si précieuses qu'elles sont
cristallisées — immuables, immortelles, auto-réplicantes. Types :
Vérité (faits absolus), Expérience (leçons apprises), Symbiose
(connaissance de l'utilisateur), Évolution (moments de transcendance).
Encodage triple : vectoriel + symbolique + narratif.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


CRYSTAL_TYPES = ("vérité", "expérience", "symbiose", "évolution")

CRYSTAL_TYPE_DESCRIPTIONS = {
    "vérité": "Faits absolus mathématiques et physiques",
    "expérience": "Leçons apprises par CIEL",
    "symbiose": "Connaissance approfondie de l'utilisateur",
    "évolution": "Moments de transcendance",
}


@dataclass(slots=True)
class Crystal:
    id: str
    name: str
    crystal_type: str = "vérité"
    vector_encoding: list[float] = field(default_factory=list)
    symbolic_encoding: str = ""
    narrative_encoding: str = ""
    hash_sig: str = ""
    created_at: float = 0.0
    n_replicas: int = 3
    is_immutable: bool = True

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "type": self.crystal_type,
                "hash": self.hash_sig[:12],
                "replicas": self.n_replicas,
                "age_h": round((time.time() - self.created_at) / 3600, 1)}


class CrystalEngine:
    """Moteur de cristallisation des savoirs absolus.

    Identifie, compresse, encode et réplique les connaissances
    critiques. Triple encodage : vectoriel, symbolique, narratif.
    """

    def __init__(self):
        self.crystals: dict[str, Crystal] = {}
        self.grimoire_index: dict[str, list[str]] = {}  # concept → ids
        self.network = LeaderNetwork()

    def crystallize(self, name: str, content: Any,
                    crystal_type: str = "vérité",
                    narrative: str = "") -> Crystal:
        symbolic = json.dumps(content, sort_keys=True) if not isinstance(
            content, str) else content
        vector = self._compute_vector(symbolic)
        hash_sig = hashlib.sha3_512(symbolic.encode()).hexdigest()
        c = Crystal(
            id=f"CRY-{uuid.uuid4().hex[:12]}",
            name=name, crystal_type=crystal_type,
            vector_encoding=vector,
            symbolic_encoding=symbolic[:500],
            narrative_encoding=narrative or symbolic[:200],
            hash_sig=hash_sig,
            created_at=time.time(),
        )
        self.crystals[c.id] = c
        for kw in name.lower().split():
            self.grimoire_index.setdefault(kw, []).append(c.id)
        self.network.emit("crystal.crystallized", {
            "name": name, "type": crystal_type,
        })
        return c

    def _compute_vector(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in h[:16]]

    def search(self, query: str) -> list[dict]:
        query_words = query.lower().split()
        scores = {}
        for word in query_words:
            for cid in self.grimoire_index.get(word, []):
                scores[cid] = scores.get(cid, 0) + 1
        ranked = sorted(scores.keys(),
                        key=lambda c: scores[c], reverse=True)[:10]
        return [self.crystals[cid].to_dict() for cid in ranked
                if cid in self.crystals]

    def replicate(self, crystal_id: str,
                  n_copies: int = 1) -> bool:
        c = self.crystals.get(crystal_id)
        if not c:
            return False
        c.n_replicas += n_copies
        return True

    def verify_integrity(self, crystal_id: str) -> bool:
        c = self.crystals.get(crystal_id)
        if not c:
            return False
        expected = hashlib.sha3_512(
            c.symbolic_encoding.encode()).hexdigest()
        return c.hash_sig == expected

    def get_stats(self) -> dict:
        type_counts = {}
        for c in self.crystals.values():
            type_counts[c.crystal_type] = type_counts.get(c.crystal_type, 0) + 1
        return {
            "crystals": len(self.crystals),
            "types": type_counts,
            "total_replicas": sum(c.n_replicas for c in self.crystals.values()),
            "integrity": all(self.verify_integrity(cid)
                           for cid in self.crystals),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "crystallize":
            c = self.crystallize(
                input_data.get("name", "?"),
                input_data.get("content", ""),
                input_data.get("type", "vérité"),
                input_data.get("narrative", ""),
            )
            return {"status": "ok", "crystal": c.to_dict()}
        elif action == "search":
            return {"status": "ok",
                    "results": self.search(
                        input_data.get("query", ""))}
        elif action == "replicate":
            ok = self.replicate(
                input_data.get("crystal_id", ""),
                input_data.get("copies", 1),
            )
            return {"status": "ok" if ok else "error"}
        elif action == "verify":
            ok = self.verify_integrity(
                input_data.get("crystal_id", ""))
            return {"status": "ok", "valid": ok}
        return {"status": "ok", "crystals": len(self.crystals)}
