"""
KarmicMemory - Persistent Consequence Tracking
Stores lessons learned that survive clone death.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class KarmicEngram:
    """Memory of a lesson learned"""
    id: str
    concept: str
    lesson_learned: str
    emotional_resonance: float  # 0-1
    generation_discovered: int
    embedding: list[float] = field(default_factory=list)
    timestamp: float = field(default_factory=lambda: __import__("time").time())


@dataclass(slots=True)
class KarmicMemory:
    """
    KarmicMemory - Persistent Consequence Tracking
    Stores lessons that survive clone death.
    """
    storage_path: str = "./.titan/karma"
    engrams: dict[str, KarmicEngram] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize karmic memory"""
        self._init_storage()
        self._load_karma()
        logger.info(
            f"[Karmic Memory] 🌌 Mémoire Akashique connectée. "
            f"Engrammes: {len(self.engrams)}"
        )

    def _init_storage(self) -> None:
        """Initialize storage directory"""
        os.makedirs(self.storage_path, exist_ok=True)

    def _load_karma(self) -> None:
        """Load karmic records from disk"""
        file_path = os.path.join(self.storage_path, "akashic_records.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    for item in data:
                        engram = KarmicEngram(
                            id=item["id"],
                            concept=item["concept"],
                            lesson_learned=item["lesson_learned"],
                            emotional_resonance=item["emotional_resonance"],
                            generation_discovered=item["generation_discovered"],
                            embedding=item.get("embedding", []),
                            timestamp=item.get("timestamp", 0)
                        )
                        self.engrams[engram.id] = engram
            except Exception as e:
                logger.error(f"[Karmic Memory] Erreur lors de la lecture: {e}")

    def _save_karma(self) -> None:
        """Save karmic records to disk"""
        file_path = os.path.join(self.storage_path, "akashic_records.json")
        with open(file_path, "w") as f:
            data = []
            for engram in self.engrams.values():
                data.append({
                    "id": engram.id,
                    "concept": engram.concept,
                    "lesson_learned": engram.lesson_learned,
                    "emotional_resonance": engram.emotional_resonance,
                    "generation_discovered": engram.generation_discovered,
                    "embedding": engram.embedding,
                    "timestamp": engram.timestamp,
                })
            json.dump(data, f, indent=2)

    def engrave(
        self,
        concept: str,
        lesson_learned: str,
        generation: int,
        emotional_resonance: float = 0.5,
    ) -> str:
        """Record a lesson learned"""
        engram_id = f"krm_{str(uuid4()).split('-')[0]}"
        engram = KarmicEngram(
            id=engram_id,
            concept=concept,
            lesson_learned=lesson_learned,
            emotional_resonance=emotional_resonance,
            generation_discovered=generation,
        )

        self.engrams[engram_id] = engram
        self._save_karma()
        logger.debug(f"[Karmic Memory] 🔮 Nouvel engramme gravé: {concept}")
        return engram_id

    def record_birth(self, clone_id: str, genome: Any) -> str:
        """Record clone birth"""
        genome_str = str(genome)[:500]
        return self.engrave(
            f"Clone Birth {clone_id}",
            genome_str,
            0,
            0.6
        )

    def recall(self, query: str, limit: int = 3) -> list[KarmicEngram]:
        """Recall memories matching query (basic keyword matching)"""
        query_words = query.lower().split()

        scored = []
        for engram in self.engrams.values():
            score = 0.0
            text = f"{engram.concept} {engram.lesson_learned}".lower()
            for word in query_words:
                if word in text:
                    score += 1.0
            score += engram.emotional_resonance
            scored.append((engram, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [engram for engram, _ in scored[:limit]]

    def get_global_wisdom_summary(self) -> str:
        """Get summary of top wisdom"""
        if not self.engrams:
            return "Aucune sagesse karmique accumulée."

        sorted_engrams = sorted(
            self.engrams.values(),
            key=lambda e: e.emotional_resonance,
            reverse=True
        )[:5]

        return "\n".join(
            f"- [Gen {e.generation_discovered}] {e.concept}: {e.lesson_learned}"
            for e in sorted_engrams
        )

    def process(self, input_data: Any) -> dict[str, Any]:
        """
        Process memory request.
        CIEL compatibility method.
        """
        if isinstance(input_data, dict):
            action = input_data.get("action", "status")
            if action == "summary":
                return {"summary": self.get_global_wisdom_summary()}
        
        return {
            "engrams": len(self.engrams),
            "status": "ready"
        }
