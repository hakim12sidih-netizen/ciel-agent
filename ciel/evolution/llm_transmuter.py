from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from ciel.evolution.transmutation_budget import TransmutationBudget, BudgetCheck


@dataclass(slots=True)
class TransmutationResult:
    status: str
    file_path: str
    reason: str = ""
    proposal_id: str = ""
    duration_ms: float = 0.0
    patch_size_bytes: int = 0


@dataclass(slots=True)
class ArchitecturalGene:
    id: str = ""
    module_name: str = ""
    interfaces: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    complexity: float = 0.0
    mutation_rate: float = 0.5
    generation: int = 0
    last_transmutation: float = 0.0
    fitness: float = 0.5
    is_vital: bool = False


class LLMTransmuter:
    def __init__(
        self,
        llm_complete_fn: Callable[[str], str] | None = None,
        aegis_verify_fn: Callable[[str, str], bool] | None = None,
        budget: TransmutationBudget | None = None,
        base_path: str = "",
    ) -> None:
        self._llm_complete = llm_complete_fn
        self._aegis_verify = aegis_verify_fn
        self._budget = budget or TransmutationBudget()
        self._base_path = base_path or os.getcwd()
        self._genes: dict[str, ArchitecturalGene] = {}
        self._transmutation_count = 0

    async def transmutate(self, file_path: str, intent: str) -> TransmutationResult:
        start = time.time()
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(self._base_path, file_path)
        self._transmutation_count += 1

        budget_check = self._budget.check(abs_path, depth=0)
        if not budget_check.allowed:
            return TransmutationResult(
                status="rejected_by_budget",
                file_path=abs_path,
                reason=budget_check.message,
                duration_ms=(time.time() - start) * 1000,
            )

        if not os.path.isfile(abs_path):
            return TransmutationResult(
                status="apply_failed",
                file_path=abs_path,
                reason="File not found",
                duration_ms=(time.time() - start) * 1000,
            )

        try:
            with open(abs_path, encoding="utf-8") as f:
                current_code = f.read()
        except OSError as e:
            return TransmutationResult(
                status="apply_failed",
                file_path=abs_path,
                reason=f"Cannot read file: {e}",
                duration_ms=(time.time() - start) * 1000,
            )

        if self._llm_complete is None:
            return TransmutationResult(
                status="llm_error",
                file_path=abs_path,
                reason="No LLM client available",
                duration_ms=(time.time() - start) * 1000,
            )

        prompt = self._build_prompt(current_code, intent, file_path)
        proposed_code = self._llm_complete(prompt)
        if not proposed_code:
            return TransmutationResult(
                status="llm_error",
                file_path=abs_path,
                reason="LLM returned empty response",
                duration_ms=(time.time() - start) * 1000,
            )

        if self._aegis_verify is not None and not self._aegis_verify(abs_path, proposed_code):
            return TransmutationResult(
                status="rejected_by_aegis",
                file_path=abs_path,
                reason="Aegis verification failed",
                patch_size_bytes=len(proposed_code),
                duration_ms=(time.time() - start) * 1000,
            )

        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(proposed_code)
        except OSError as e:
            return TransmutationResult(
                status="apply_failed",
                file_path=abs_path,
                reason=f"Cannot write file: {e}",
                duration_ms=(time.time() - start) * 1000,
            )

        self._budget.record_transmutation(abs_path)
        return TransmutationResult(
            status="applied",
            file_path=abs_path,
            patch_size_bytes=len(proposed_code),
            duration_ms=(time.time() - start) * 1000,
        )

    def _build_prompt(self, code: str, intent: str, file_path: str) -> str:
        return (
            f"You are a code mutation engine. Improve this module.\n\n"
            f"INTENT: {intent}\nFILE: {file_path}\n\n"
            f"CURRENT CODE:\n{code}\n\n"
            f"CONSTRAINTS: No eval/exec, no infinite loops, preserve all exports. "
            f"Return ONLY the new code, no markdown fences."
        )

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_transmutations": self._transmutation_count,
            "budget": self._budget.get_stats(),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        return self.get_stats()
