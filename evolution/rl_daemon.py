from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class RLBenchmarkResult:
    genome_id: str
    fitness: float
    duration_ms: float
    success: bool
    polyglot_used: bool
    docker_synergy: bool


class RLDaemon:
    def __init__(
        self,
        llm_complete_fn: Callable[[str], str] | None = None,
        interval_ms: int = 60_000,
    ) -> None:
        self._llm_complete = llm_complete_fn
        self._interval_ms = interval_ms
        self._task: asyncio.Task | None = None
        self._is_testing = False
        self._results: list[RLBenchmarkResult] = []
        self._genomes: list[Any] = []

    def set_genomes(self, genomes: list[Any]) -> None:
        self._genomes = genomes

    async def start(self) -> None:
        if self._task is not None:
            raise RuntimeError("[RL Daemon] already started")
        async def _loop() -> None:
            while True:
                await asyncio.sleep(self._interval_ms / 1000.0)
                if self._is_testing or not self._genomes:
                    continue
                await self._benchmark_next()
        self._task = asyncio.create_task(_loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _benchmark_next(self) -> None:
        self._is_testing = True
        try:
            genome = self._genomes.pop(0) if self._genomes else None
            if genome is None:
                return
            genome_id = getattr(genome, "id", "unknown")
            challenges = [
                "Write a Rust function that computes the nth Fibonacci number.",
                "Write a Python script that scrapes a URL and prints the title.",
                "Write a Go program that sorts an array of 100 random integers.",
            ]
            task = random.choice(challenges)
            start_time = time.time()
            success = False
            polyglot_used = False
            if self._llm_complete is not None:
                result = self._llm_complete(task)
                success = "SUCCESS" in result or "out" in result
            duration_ms = (time.time() - start_time) * 1000
            fitness = 0.0
            if success:
                fitness += 200.0
            fitness += 100_000.0 / max(duration_ms, 1.0)
            docker_affinity = getattr(genome, "params", None)
            docker_synergy = polyglot_used and (docker_affinity is not None and getattr(docker_affinity, "docker_affinity", 0) > 0.6)
            r = RLBenchmarkResult(
                genome_id=genome_id, fitness=fitness,
                duration_ms=duration_ms, success=success,
                polyglot_used=polyglot_used, docker_synergy=docker_synergy,
            )
            self._results.append(r)
        finally:
            self._is_testing = False

    def get_results(self) -> list[RLBenchmarkResult]:
        return list(self._results)

    def process(self, input_data: Any) -> dict[str, Any]:
        return {
            "benchmarks_completed": len(self._results),
            "queued_genomes": len(self._genomes),
        }
