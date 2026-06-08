from __future__ import annotations

import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    PROSPECTIVE = "prospective"
    EMOTIONAL = "emotional"
    META = "meta"
    IMPLICIT = "implicit"
    COLLECTIVE = "collective"


@dataclass(slots=True)
class MemoryItem:
    id: str
    content: Any
    timestamp: float = 0.0
    importance: float = 0.5
    tags: list[str] = field(default_factory=list)
    access_count: int = 0


class EpisodicMemory:
    def __init__(self, capacity: int = 1000) -> None:
        self.capacity = capacity
        self._items: list[MemoryItem] = []

    def store(self, item: MemoryItem) -> None:
        self._items.append(item)
        if len(self._items) > self.capacity:
            self._items.pop(0)

    def recall(self, query: str, top_k: int = 5) -> list[MemoryItem]:
        results = [i for i in self._items if query.lower() in str(i.content).lower()]
        return sorted(results, key=lambda i: i.importance, reverse=True)[:top_k]

    def all(self) -> list[MemoryItem]:
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)


class SemanticMemory:
    def __init__(self) -> None:
        self._facts: dict[str, Any] = {}

    def store(self, key: str, value: Any) -> None:
        self._facts[key] = value

    def retrieve(self, key: str) -> Any | None:
        return self._facts.get(key)

    def search(self, prefix: str) -> dict[str, Any]:
        return {k: v for k, v in self._facts.items() if k.startswith(prefix)}

    def __len__(self) -> int:
        return len(self._facts)


class ProceduralMemory:
    def __init__(self) -> None:
        self._procedures: dict[str, dict[str, Any]] = {}

    def store(self, name: str, steps: list[str], **metadata: Any) -> None:
        self._procedures[name] = {"steps": steps, **metadata}

    def execute(self, name: str) -> list[str] | None:
        proc = self._procedures.get(name)
        if not proc:
            return None
        return list(proc["steps"])

    def __len__(self) -> int:
        return len(self._procedures)


class ProspectiveMemory:
    def __init__(self) -> None:
        self._intentions: list[dict[str, Any]] = []

    def add_intention(self, task: str, deadline: float, **metadata: Any) -> None:
        self._intentions.append({"task": task, "deadline": deadline, "done": False, **metadata})

    def check(self, current_time: float) -> list[dict[str, Any]]:
        due = [i for i in self._intentions if not i["done"] and i["deadline"] <= current_time]
        for i in due:
            i["done"] = True
        return due

    def pending(self) -> list[dict[str, Any]]:
        return [i for i in self._intentions if not i["done"]]

    def __len__(self) -> int:
        return len(self._intentions)


class EmotionalMemory:
    def __init__(self) -> None:
        self._emotional_states: list[dict[str, Any]] = []

    def record(self, emotion: str, intensity: float, context: str = "") -> None:
        self._emotional_states.append({
            "emotion": emotion, "intensity": intensity,
            "context": context, "timestamp": time.time(),
        })

    def recent(self, n: int = 5) -> list[dict[str, Any]]:
        return self._emotional_states[-n:]

    def dominant(self) -> str | None:
        if not self._emotional_states:
            return None
        return max(self._emotional_states, key=lambda e: e["intensity"])["emotion"]

    def __len__(self) -> int:
        return len(self._emotional_states)


class MetaMemory:
    def __init__(self) -> None:
        self._calibration: dict[str, float] = defaultdict(float)
        self._confidences: list[dict[str, Any]] = []

    def record_confidence(self, prediction: str, confidence: float, correct: bool) -> None:
        self._confidences.append({
            "prediction": prediction, "confidence": confidence,
            "correct": correct, "timestamp": time.time(),
        })
        key = prediction.split("_")[0] if "_" in prediction else prediction
        n = sum(1 for c in self._confidences if c["prediction"].startswith(key))
        correct_n = sum(1 for c in self._confidences if c["prediction"].startswith(key) and c["correct"])
        self._calibration[key] = correct_n / max(n, 1)

    def calibration(self, domain: str = "") -> float:
        if domain:
            return self._calibration.get(domain, 0.0)
        vals = list(self._calibration.values())
        return sum(vals) / max(len(vals), 1)

    def __len__(self) -> int:
        return len(self._confidences)


class ImplicitMemory:
    def __init__(self) -> None:
        self._patterns: dict[str, float] = {}

    def observe(self, pattern: str, strength: float = 1.0) -> None:
        self._patterns[pattern] = self._patterns.get(pattern, 0.0) + strength

    def strongest(self, top_k: int = 3) -> list[tuple[str, float]]:
        return sorted(self._patterns.items(), key=lambda x: -x[1])[:top_k]

    def __len__(self) -> int:
        return len(self._patterns)


class CollectiveMemory:
    def __init__(self) -> None:
        self._shared: dict[str, dict[str, Any]] = {}

    def share(self, key: str, value: Any, source: str = "") -> None:
        self._shared[key] = {"value": value, "source": source, "timestamp": time.time()}

    def query(self, key: str) -> Any | None:
        entry = self._shared.get(key)
        return entry["value"] if entry else None

    def __len__(self) -> int:
        return len(self._shared)


class MemoryEngine:
    """Moteur mémoire unifié — 8 types de mémoire."""

    def __init__(self) -> None:
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.prospective = ProspectiveMemory()
        self.emotional = EmotionalMemory()
        self.meta = MetaMemory()
        self.implicit = ImplicitMemory()
        self.collective = CollectiveMemory()

    def get_stats(self) -> dict[str, int]:
        return {
            "episodic": len(self.episodic),
            "semantic": len(self.semantic),
            "procedural": len(self.procedural),
            "prospective": len(self.prospective),
            "emotional": len(self.emotional),
            "meta": len(self.meta),
            "implicit": len(self.implicit),
            "collective": len(self.collective),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if not isinstance(input_data, dict):
            return {"success": False, "error": "input must be dict"}

        action = input_data.get("action", "stats")
        data = {k: v for k, v in input_data.items() if k != "action"}

        if action == "store_episodic":
            item = MemoryItem(
                id=f"mem_{len(self.episodic)}_{random.randint(100,999)}",
                content=data.get("content", ""),
                importance=float(data.get("importance", 0.5)),
            )
            self.episodic.store(item)
            return {"success": True, "action": "store_episodic", "id": item.id}

        elif action == "store_semantic":
            self.semantic.store(str(data.get("key", "")), data.get("value"))
            return {"success": True, "action": "store_semantic"}

        elif action == "recall":
            results = self.episodic.recall(str(data.get("query", "")), int(data.get("top_k", 5)))
            return {
                "success": True, "action": "recall",
                "results": [{"id": r.id, "content": r.content} for r in results],
            }

        elif action == "stats":
            return {"success": True, "action": "stats", "memory": self.get_stats()}

        return {"success": False, "error": f"unknown action '{action}'"}
