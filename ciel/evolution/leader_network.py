"""
CIEL v1.0 — LeaderNetwork : bus d'événements pour les agents CIEL.

Migré depuis Hydra (LeaderNetwork), adapté pour CIEL.
Permet aux agents, strates et modules de communiquer
via un pattern publish/subscribe asynchrone.
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class Event:
    type: str
    data: dict[str, Any]
    source: str = "unknown"
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


class LeaderNetwork:
    """Bus d'événements central de CIEL.

    Pattern publish/subscribe avec :
      - Filtrage par type d'événement
      - Historique des événements
      - Métriques de traffic
    """

    _instance: LeaderNetwork | None = None

    def __new__(cls) -> LeaderNetwork:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = defaultdict(list)
            cls._instance._history: list[Event] = []
            cls._instance._max_history = 1000
            cls._instance._event_count = 0
            cls._instance._id = f"NET-{uuid.uuid4().hex[:8]}"
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> str:
        token = f"SUB-{uuid.uuid4().hex[:12]}"
        self._subscribers[event_type].append((token, callback))
        return token

    def unsubscribe(self, token: str) -> bool:
        for event_type in list(self._subscribers.keys()):
            self._subscribers[event_type] = [
                (t, cb) for t, cb in self._subscribers[event_type] if t != token
            ]
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
        return True

    def emit(self, event_type: str, data: dict[str, Any], source: str = "leader_network") -> Event:
        event = Event(type=event_type, data=data, source=source)
        self._event_count += 1
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        for token, callback in self._subscribers.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                print(f"[LeaderNetwork] Error in subscriber {token}: {e}")
        return event

    def get_history(self, event_type: str | None = None, limit: int = 50) -> list[Event]:
        if event_type:
            return [e for e in self._history if e.type == event_type][-limit:]
        return self._history[-limit:]

    def stats(self) -> dict:
        type_counts: dict[str, int] = defaultdict(int)
        for e in self._history:
            type_counts[e.type] += 1
        return {
            "total_events": self._event_count,
            "history_size": len(self._history),
            "subscriber_count": sum(len(subs) for subs in self._subscribers.values()),
            "event_types": dict(type_counts),
        }

    def clear_history(self) -> None:
        self._history.clear()

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None
