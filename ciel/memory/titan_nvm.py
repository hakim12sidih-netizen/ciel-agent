"""
CIEL v∞.3 — TitanNVM : Mémoire Neural Virtual Memory (inspiré HYDRA).

Gère la hiérarchie de mémoire du CIEL-BRAIN (L1 à L4) :
  - L1_HOT : Registres actifs (mémoire de travail)
  - L2_WARM : Contexte session (mémoire épisodique)
  - L3_BRAIN : Savoir consolidé (mémoire sémantique)
  - L4_ARCHIVE : Archives compressées (mémoire à long terme)
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class MemoryLevel(str, Enum):
    """Niveaux de mémoire CIEL (inspirés HYDRA TitanNVM)."""
    L1_HOT = "L1_HOT"       # Mémoire de travail (registres actifs)
    L2_WARM = "L2_WARM"     # Contexte session (mémoire épisodique)
    L3_BRAIN = "L3_BRAIN"   # Savoir consolidé (mémoire sémantique)
    L4_ARCHIVE = "L4_ARCHIVE" # Archives compressées (long terme)


@dataclass(slots=True)
class MemoryChunk:
    """Un chunk de mémoire avec métadonnées."""
    id: str
    content: Any
    vector: list[float] | None = None
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    access_count: int = 0
    level: str = "L2_WARM"
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5  # 0-1, utilisé pour l'oubli stratégique


class TitanNVM:
    """
    Neural Virtual Memory — Gestion hiérarchique de la mémoire CIEL.
    
    Inspiré de HYDRA TitanNVM (4 niveaux L1-L4).
    Implémentation Python avec persistance optionnelle.
    """
    
    def __init__(self, storage_backend: str = "memory") -> None:
        self._storage: dict[str, dict[str, "MemoryChunk"]] = {
            "L1_HOT": {},
            "L2_WARM": {},
            "L3_BRAIN": {},
            "L4_ARCHIVE": {},
        }
        self._access_order: list[str] = []  # Pour LRU
        self._max_l1_size = 1000  # L1 limitée
        
    def store(
        self,
        content: Any,
        level: str = "L2_WARM",
        vector: list[float] | None = None,
        chunk_id: str | None = None,
        tags: list[str] | None = None,
        importance: float = 0.5
    ) -> str:
        """
        Stocke une information dans le niveau de mémoire spécifié.
        
        Args:
            content: Contenu à stocker (sérialisable)
            level: Niveau mémoire (L1_HOT, L2_WARM, L3_BRAIN, L4_ARCHIVE)
            vector: Embedding optionnel pour recherche sémantique
            chunk_id: ID personnalisé (généré si absent)
            tags: Tags pour recherche
            importance: Importance 0-1 (utilisé pour rétention)
            
        Returns:
            ID du chunk stocké
        """
        chunk_id = chunk_id or str(uuid.uuid4())
        timestamp = int(time.time() * 1000)
        
        chunk = {
            "id": chunk_id,
            "content": content,
            "vector": vector,
            "timestamp": int(time.time() * 1000),
            "access_count": 0,
            "level": level,
            "tags": tags or [],
            "importance": importance
        }
        
        if level not in self._storage:
            level = "L2_WARM"
            
        self._storage[level][chunk_id] = chunk
        
        # Gestion L1 (LRU)
        if level == "L1_HOT":
            self._access_order.append(chunk_id)
            if len(self._access_order) > 1000:
                # Éviction LRU vers L2
                evicted = self._access_order.pop(0)
                evicted_chunk = self._storage["L1_HOT"].pop(evicted, None)
                if evicted_chunk:
                    evicted_chunk["level"] = "L2_WARM"
                    self._storage["L2_WARM"][evicted] = evicted_chunk
        
        return chunk_id
    
    def retrieve(self, chunk_id: str) -> dict | None:
        """
        Récupération intelligente (RAG interne) — cherche L1→L2→L3.
        Met à jour les compteurs d'accès.
        """
        for level in ["L1_HOT", "L2_WARM", "L3_BRAIN", "L4_ARCHIVE"]:
            chunk = self._storage.get(level, {}).get(chunk_id)
            if chunk:
                chunk["access_count"] = chunk.get("access_count", 0) + 1
                chunk["last_access"] = int(time.time() * 1000)
                # Promotion vers L1 si très accédé
                if chunk.get("access_count", 0) > 10 and level != "L1_HOT":
                    self._promote_to_l1(chunk_id, level)
                return chunk
        return None
    
    def _promote_to_l1(self, chunk_id: str, from_level: str) -> None:
        """Promotion d'un chunk vers L1_HOT."""
        if from_level in self._storage and chunk_id in self._storage[from_level]:
            chunk = self._storage[from_level].pop(chunk_id)
            chunk["level"] = "L1_HOT"
            self._storage["L1_HOT"][chunk_id] = chunk
            self._access_order.append(chunk_id)
    
    def search_by_tags(self, tags: list[str], level: str | None = None) -> list[dict]:
        """Recherche par tags (filtrage sémantique simple)."""
        results = []
        levels = [level] if level else ["L1_HOT", "L2_WARM", "L3_BRAIN", "L4_ARCHIVE"]
        for level_name in levels:
            for chunk in self._storage.get(level_name, {}).values():
                if any(tag in chunk.get("tags", []) for tag in tags):
                    results.append(chunk)
        return results
    
    def search_by_vector(self, query_vector: list[float], top_k: int = 10, threshold: float = 0.7) -> list[tuple[float, dict]]:
        """Recherche par similarité cosinus sur les vecteurs."""
        if not query_vector:
            return []
        
        results = []
        for level in ["L1_HOT", "L2_WARM", "L3_BRAIN"]:
            for chunk in self._storage.get(level, {}).values():
                vec = chunk.get("vector")
                if vec and len(vec) == len(query_vector):
                    sim = self._cosine_similarity(query_vector, vec)
                    if sim >= threshold:
                        results.append((sim, chunk))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]
    
    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)
    
    def stats(self) -> dict:
        """Statistiques de la mémoire."""
        return {
            level: len(chunks) for level, chunks in self._storage.items()
        }
    
    def consolidate(self) -> int:
        """
        Consolidation mémoire (inspiré cycle veille-sommeil).
        Déplace les chunks peu accédés vers niveaux inférieurs.
        """
        moved = 0
        now = int(time.time() * 1000)
        for level in ["L1_HOT", "L2_WARM", "L3_BRAIN"]:
            to_move = []
            for chunk_id, chunk in self._storage[level].items():
                last_access = chunk.get("last_access", chunk.get("timestamp", 0))
                access_count = chunk.get("access_count", 0)
                importance = chunk.get("importance", 0.5)
                
                # Critères de démotion
                age_ms = now - last_access
                if (age_ms > 3600000 and access_count < 2 and importance < 0.3) or \
                   (age_ms > 86400000 and access_count < 5):
                    to_move.append(chunk_id)
            
            for chunk_id in to_move:
                chunk = self._storage[level].pop(chunk_id, None)
                if chunk:
                    next_level = {"L1_HOT": "L2_WARM", "L2_WARM": "L3_BRAIN", "L3_BRAIN": "L4_ARCHIVE"}[level]
                    chunk["level"] = next_level
                    self._storage[next_level][chunk_id] = chunk
                    moved += 1
        return moved
    
    def get_stats(self) -> dict:
        return {
            "levels": {level: len(chunks) for level, chunks in self._storage.items()},
            "total_chunks": sum(len(c) for c in self._storage.values()),
            "l1_hot_size": len(self._storage["L1_HOT"]),
        }


# Instance globale (pattern singleton pour le noyau)
_titan_nvm_instance: TitanNVM | None = None


def get_titan_nvm() -> TitanNVM:
    """Retourne l'instance singleton du TitanNVM."""
    global _titan_nvm_instance
    if _titan_nvm_instance is None:
        _titan_nvm_instance = TitanNVM()
    return _titan_nvm_instance


def init_titan_nvm(storage_backend: str = "memory") -> TitanNVM:
    """Initialise le TitanNVM global."""
    global _titan_nvm_instance
    _titan_nvm_instance = TitanNVM(storage_backend)
    return _titan_nvm_instance