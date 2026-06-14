from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class DistillationRecord:
    topic: str
    input_text: str
    reasoning: str
    lecture: str
    output: str
    timestamp: float


class DistillerDaemon:
    def __init__(self, llm_complete_fn: Callable[[str], str] | None = None) -> None:
        self._llm_complete = llm_complete_fn
        self._records: list[DistillationRecord] = []
        self._is_distilling = False
        self._task: asyncio.Task | None = None

    async def start(self, interval_ms: int = 3_600_000) -> None:
        if self._task is not None:
            return
        async def _loop() -> None:
            await asyncio.sleep(30)
            while True:
                await self._perform_distillation_cycle()
                await asyncio.sleep(interval_ms / 1000.0)
        self._task = asyncio.create_task(_loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _perform_distillation_cycle(self) -> None:
        if self._is_distilling:
            return
        self._is_distilling = True
        try:
            topics = [
                "Advanced Software Architecture (Microservices/Event-Driven)",
                "Causal Inference & Counterfactual Synthesis",
                "Metaprogramming & Domain-Specific Languages",
                "Sovereign Data Infrastructure & Decentralized Mesh",
            ]
            topic = random.choice(topics)
            prompt = (
                f"Provide a comprehensive solution on: {topic}. "
                "Include reasoning chain and pedagogical explanation."
            )
            raw = ""
            if self._llm_complete is not None:
                raw = self._llm_complete(prompt)
            if raw:
                self._records.append(DistillationRecord(
                    topic=topic,
                    input_text=prompt,
                    reasoning=raw,
                    lecture="",
                    output=raw,
                    timestamp=time.time(),
                ))
        finally:
            self._is_distilling = False

    def get_records(self) -> list[DistillationRecord]:
        return list(self._records)

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict):
            if input_data.get("trigger", False):
                asyncio.ensure_future(self._perform_distillation_cycle())
        return {
            "distillation_count": len(self._records),
            "latest_topic": self._records[-1].topic if self._records else None,
        }
