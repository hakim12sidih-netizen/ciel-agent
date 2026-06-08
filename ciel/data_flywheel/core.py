from __future__ import annotations

import hashlib
import time
import zlib
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DataTier(Enum):
    PLATINUM = "platinum"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"


@dataclass(slots=True)
class DataPacket:
    id: str
    source: str
    tier: DataTier
    content: dict[str, Any]
    timestamp: float
    size_bytes: int = 0
    checksum: str = ""
    agent_id: str = ""

    def __post_init__(self) -> None:
        raw = str(self.content).encode()
        self.size_bytes = len(raw)
        self.checksum = hashlib.sha256(raw).hexdigest()[:16]


@dataclass(slots=True)
class DataValue:
    relevance: float
    uniqueness: float
    freshness: float
    quality: float

    @property
    def score(self) -> float:
        return self.relevance * self.uniqueness * self.freshness * self.quality


class DataFlywheel:
    """Volant de Données — pipeline auto-amplifiant 6 étapes."""

    def __init__(self) -> None:
        self._queue: dict[DataTier, list[DataPacket]] = {
            DataTier.PLATINUM: [], DataTier.GOLD: [],
            DataTier.SILVER: [], DataTier.BRONZE: [],
        }
        self._processed: list[DataPacket] = []
        self._value_scores: dict[str, list[float]] = defaultdict(list)
        self._total_ingested: int = 0

    def ingest(self, packet: DataPacket) -> DataValue:
        dv = DataValue(
            relevance=min(1.0, len(packet.content) / 100),
            uniqueness=1.0 / (1.0 + len(self._processed) * 0.001),
            freshness=1.0 - (time.time() - packet.timestamp) / 86400,
            quality=min(1.0, packet.size_bytes / 1024),
        )
        self._queue[packet.tier].append(packet)
        self._value_scores[packet.source].append(dv.score)
        self._total_ingested += 1
        return dv

    def process_tier(self, tier: DataTier) -> list[dict[str, Any]]:
        packets = self._queue[tier]
        results = []
        for p in packets:
            self._processed.append(p)
            results.append({"id": p.id, "source": p.source, "tier": p.tier.value, "size": p.size_bytes})
        self._queue[tier] = []
        return results

    def process_all(self) -> dict[str, int]:
        counts = {}
        for tier in DataTier:
            processed = self.process_tier(tier)
            counts[tier.value] = len(processed)
        return counts

    def get_stats(self) -> dict[str, Any]:
        queue_total = sum(len(q) for q in self._queue.values())
        return {
            "total_ingested": self._total_ingested,
            "total_processed": len(self._processed),
            "queue_size": queue_total,
            "avg_value": sum(sum(v) for v in self._value_scores.values()) / max(self._total_ingested, 1),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "ingest":
            tier_str = str(data.get("tier", "bronze")).upper()
            try:
                tier = DataTier(tier_str.lower())
            except ValueError:
                return {"success": False, "error": f"unknown tier '{tier_str}'"}
            packet = DataPacket(
                id=str(hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]),
                source=str(data.get("source", "unknown")),
                tier=tier,
                content=data.get("content", {}),
                timestamp=time.time(),
                agent_id=str(data.get("agent_id", "")),
            )
            dv = self.ingest(packet)
            return {"success": True, "packet_id": packet.id, "value_score": dv.score}

        elif action == "process":
            counts = self.process_all()
            return {"success": True, "processed": counts}

        elif action == "stats":
            return {"success": True, "action": "stats", **self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
