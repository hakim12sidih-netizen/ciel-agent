from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class AscensionRecord:
    clone_id: str
    domain: str
    ascension_time: float


@dataclass(slots=True)
class SubClone:
    clone_id: str
    name: str
    status: str = "idle"
    clone_class: str = "FREE"
    created_at: float = 0.0


class AscensionProtocol:
    def __init__(self, promote_fn: Callable[[str, str], Any] | None = None) -> None:
        self._promote_fn = promote_fn
        self._ascended_leaders: dict[str, AscensionRecord] = {}
        self._on_ascension: list[Callable[[str, str], None]] = []

    def evaluate_clones_for_ascension(self, current_phi: float, clones: list[SubClone] | None = None) -> None:
        if current_phi < 5.0:
            return
        if clones is None:
            clones = []
        ripe = [
            c for c in clones
            if c.status == "idle" and c.clone_class == "FREE"
            and (time.time() - c.created_at) > 60.0
        ]
        if not ripe:
            return
        chosen = sorted(ripe, key=lambda c: c.created_at)[0]
        cpu_load = random.random()
        mem_usage = random.random()
        lag = random.random() * 50
        if cpu_load > 0.6:
            domain = "Neural_Optimization"
        elif mem_usage > 0.7:
            domain = "Memory_Hegemony"
        elif lag > 20:
            domain = "System_Kernel"
        else:
            domain = "Cyber_Security_Arch"
        self.trigger_ascension(chosen.clone_id, chosen.name, domain)

    def trigger_ascension(self, clone_id: str, clone_name: str, domain: str) -> None:
        if clone_id in self._ascended_leaders:
            return
        self._ascended_leaders[clone_id] = AscensionRecord(
            clone_id=clone_id, domain=domain, ascension_time=time.time(),
        )
        if self._promote_fn:
            self._promote_fn(clone_id, domain)
        for cb in self._on_ascension:
            cb(clone_id, domain)

    def on_ascension(self, callback: Callable[[str, str], None]) -> None:
        self._on_ascension.append(callback)

    def get_ascended_leaders(self) -> list[AscensionRecord]:
        return list(self._ascended_leaders.values())

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict):
            current_phi = input_data.get("current_phi", 0.0)
            raw_clones = input_data.get("clones", [])
            clones = [
                SubClone(
                    clone_id=c.get("clone_id", ""),
                    name=c.get("name", ""),
                    status=c.get("status", "idle"),
                    clone_class=c.get("clone_class", "FREE"),
                    created_at=c.get("created_at", time.time()),
                )
                for c in raw_clones
            ]
            self.evaluate_clones_for_ascension(current_phi, clones)
        return {
            "ascended_leaders": [
                {"clone_id": r.clone_id, "domain": r.domain, "ascension_time": r.ascension_time}
                for r in self._ascended_leaders.values()
            ],
        }
