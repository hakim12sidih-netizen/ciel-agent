"""
Strate 4 — MÉMOIRE : 8 types de mémoire.
  - episodic, semantic, procedural, prospective, emotional, meta, implicit, collective
"""
from __future__ import annotations

from ciel.memory.titan_nvm import TitanNVM, MemoryLevel, MemoryChunk, get_titan_nvm, init_titan_nvm
from ciel.memory.core import (
    MemoryEngine, EpisodicMemory, SemanticMemory, ProceduralMemory,
    ProspectiveMemory, EmotionalMemory, MetaMemory, ImplicitMemory,
    CollectiveMemory, MemoryType,
)

__all__ = [
    "TitanNVM", "MemoryLevel", "MemoryChunk", "get_titan_nvm", "init_titan_nvm",
    "MemoryEngine", "EpisodicMemory", "SemanticMemory", "ProceduralMemory",
    "ProspectiveMemory", "EmotionalMemory", "MetaMemory", "ImplicitMemory",
    "CollectiveMemory", "MemoryType",
]
