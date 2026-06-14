from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DataQuality(Enum):
    RAW = "raw"
    CLEANED = "cleaned"
    CURATED = "curated"
    GOLDEN = "golden"


@dataclass(slots=True)
class DataArtifact:
    id: str
    name: str
    content: str
    quality: DataQuality
    checksum: str
    created_at: float
    tags: list[str] = field(default_factory=list)
    version: int = 1


class Curator:
    def __init__(self) -> None:
        self._artifacts: dict[str, DataArtifact] = {}
        self._catalog: dict[str, list[str]] = {}

    def ingest(self, name: str, content: str, tags: list[str] | None = None) -> DataArtifact:
        raw = content.encode()
        cksum = hashlib.sha256(raw).hexdigest()[:16]
        art = DataArtifact(
            id=f"art_{len(self._artifacts)}",
            name=name,
            content=content,
            quality=DataQuality.RAW,
            checksum=cksum,
            created_at=time.time(),
            tags=tags or [],
        )
        self._artifacts[art.id] = art
        for t in art.tags:
            self._catalog.setdefault(t, []).append(art.id)
        return art

    def clean(self, artifact_id: str) -> DataArtifact | None:
        art = self._artifacts.get(artifact_id)
        if not art:
            return None
        art.quality = DataQuality.CLEANED
        art.version += 1
        return art

    def curate(self, artifact_id: str) -> DataArtifact | None:
        art = self._artifacts.get(artifact_id)
        if not art or art.quality == DataQuality.RAW:
            return None
        art.quality = DataQuality.CURATED
        art.version += 1
        return art

    def find_by_tag(self, tag: str) -> list[DataArtifact]:
        ids = self._catalog.get(tag, [])
        return [self._artifacts[i] for i in ids if i in self._artifacts]

    def get_stats(self) -> dict[str, Any]:
        by_q: dict[str, int] = {}
        for a in self._artifacts.values():
            by_q[a.quality.value] = by_q.get(a.quality.value, 0) + 1
        return {"total": len(self._artifacts), "tags": len(self._catalog), "by_quality": by_q}

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}
        action = input_data.get("action", "stats")
        if action == "stats":
            return {"success": True, **self.get_stats()}
        elif action == "ingest":
            art = self.ingest(str(input_data.get("name", "")), str(input_data.get("content", "")))
            return {"success": True, "artifact_id": art.id, "quality": art.quality.value}
        elif action == "clean":
            if self.clean(str(input_data.get("artifact_id", ""))):
                return {"success": True}
            return {"success": False, "error": "artifact not found"}
        return {"success": False, "error": f"unknown action '{action}'"}
