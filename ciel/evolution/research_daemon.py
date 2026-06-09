from __future__ import annotations

import asyncio
import random
import re
from typing import Any, Callable


class ResearchDaemon:
    def __init__(
        self,
        llm_complete_fn: Callable[[str], str] | None = None,
        web_search_fn: Callable[[str, int], list[str]] | None = None,
    ) -> None:
        self._llm_complete = llm_complete_fn
        self._web_search = web_search_fn
        self._task: asyncio.Task | None = None
        self._is_researching = False

    async def start(self, interval_ms: int = 900_000) -> None:
        if self._task is not None:
            raise RuntimeError("[Research Daemon] already started")
        async def _loop() -> None:
            await asyncio.sleep(5)
            while True:
                if not self._is_researching:
                    await self._perform_autonomous_research()
                await asyncio.sleep(interval_ms / 1000.0)
        self._task = asyncio.create_task(_loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _perform_autonomous_research(self) -> None:
        self._is_researching = True
        try:
            if self._llm_complete is None:
                return
            curiosity_prompt = (
                "Identify a complex topic in technology, philosophy, or science to research. "
                "Return ONLY the topic name and a short query. Format: Topic | Query"
            )
            curiosity_result = self._llm_complete(curiosity_prompt)
            if "|" not in curiosity_result:
                return
            parts = curiosity_result.split("|", 1)
            topic = parts[0].strip()
            query = parts[1].strip()

            abduction_prompt = f"Generate a bold hypothesis about the future of '{topic}'."
            self._llm_complete(abduction_prompt)

            if self._web_search is not None:
                urls = self._web_search(query, 3)
                url_pattern = re.compile(r"https?://[^\s)]+")
                for url in urls:
                    if url_pattern.match(url):
                        pass
        finally:
            self._is_researching = False

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict) and input_data.get("trigger", False):
            asyncio.ensure_future(self._perform_autonomous_research())
        return {"researching": self._is_researching, "active": self._task is not None}
