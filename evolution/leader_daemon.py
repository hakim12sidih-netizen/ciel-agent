from __future__ import annotations

import asyncio
from typing import Any, Callable


class LeaderDaemon:
    def __init__(
        self,
        llm_complete_fn: Callable[[str], str] | None = None,
        interval_ms: int = 60_000,
    ) -> None:
        self._llm_complete = llm_complete_fn
        self._interval_ms = interval_ms
        self._task: asyncio.Task | None = None
        self._is_processing = False
        self._current_imperial_order: str | None = None
        self._factions: list[Any] = []
        self._population: list[Any] = []

    def set_factions(self, factions: list[Any]) -> None:
        self._factions = factions

    def set_population(self, population: list[Any]) -> None:
        self._population = population

    def set_imperial_order(self, order: str) -> None:
        self._current_imperial_order = order

    async def start(self) -> None:
        if self._task is not None:
            raise RuntimeError("[Leader Daemon] already started")
        async def _loop() -> None:
            while True:
                await asyncio.sleep(self._interval_ms / 1000.0)
                if self._is_processing:
                    continue
                if not self._factions:
                    continue
                self._is_processing = True
                try:
                    for faction in self._factions:
                        objective = self._current_imperial_order or getattr(faction, "will", "")
                        if self._llm_complete is not None and objective:
                            self._llm_complete(
                                f"Leader {getattr(faction, 'title', 'Unknown')}: {objective}"
                            )
                    self._current_imperial_order = None
                finally:
                    self._is_processing = False
        self._task = asyncio.create_task(_loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict):
            order = input_data.get("imperial_order")
            if order:
                self.set_imperial_order(order)
        return {
            "factions_count": len(self._factions),
            "active": self._task is not None,
        }
