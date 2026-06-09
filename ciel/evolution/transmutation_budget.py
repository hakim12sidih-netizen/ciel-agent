from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BudgetConfig:
    max_transmutations: int = 5
    window_ms: float = 3_600_000.0
    max_depth: int = 3
    per_file_cooldown_ms: float = 300_000.0
    allowed_paths: list[str] = field(default_factory=lambda: ["src/evolution/"])
    forbidden_paths: list[str] = field(default_factory=lambda: [
        "src/index.ts", "tsconfig.json", "package.json",
        "package-lock.json", ".env",
    ])


@dataclass(slots=True)
class BudgetCheck:
    allowed: bool
    reason: str = ""
    message: str = ""
    current_count: int = 0
    cooldown_remaining_ms: float = 0.0


class TransmutationBudget:
    def __init__(self, config: BudgetConfig | None = None) -> None:
        self._config = config or BudgetConfig()
        self._timestamps: list[float] = []
        self._per_file_timestamps: dict[str, float] = {}

    def check(
        self,
        file_path: str,
        depth: int = 0,
        lock_check: bool = False,
    ) -> BudgetCheck:
        for forbidden in self._config.forbidden_paths:
            if forbidden in file_path:
                return BudgetCheck(
                    allowed=False,
                    reason="FORBIDDEN",
                    message=f"File {file_path} is in the forbidden list ({forbidden})",
                )
        in_whitelist = any(p in file_path for p in self._config.allowed_paths)
        if not in_whitelist:
            return BudgetCheck(
                allowed=False,
                reason="WHITELIST",
                message=f"File {file_path} is not in allowed paths",
            )
        if depth > self._config.max_depth:
            return BudgetCheck(
                allowed=False,
                reason="DEPTH_EXCEEDED",
                message=f"Depth {depth} exceeds max {self._config.max_depth}",
            )
        self._purge_old_timestamps()
        if len(self._timestamps) >= self._config.max_transmutations:
            return BudgetCheck(
                allowed=False,
                reason="RATE_LIMIT",
                message=f"Rate limit: {len(self._timestamps)}/{self._config.max_transmutations}",
                current_count=len(self._timestamps),
            )
        last_for_file = self._per_file_timestamps.get(file_path)
        if last_for_file is not None:
            elapsed = time.time() * 1000 - last_for_file
            if elapsed < self._config.per_file_cooldown_ms:
                remaining = self._config.per_file_cooldown_ms - elapsed
                return BudgetCheck(
                    allowed=False,
                    reason="COOLDOWN",
                    message=f"Cooldown active: {remaining / 1000:.0f}s remaining",
                    cooldown_remaining_ms=remaining,
                )
        return BudgetCheck(allowed=True, current_count=len(self._timestamps))

    def record_transmutation(self, file_path: str) -> None:
        now = time.time() * 1000
        self._timestamps.append(now)
        self._per_file_timestamps[file_path] = now

    def get_stats(self) -> dict[str, Any]:
        self._purge_old_timestamps()
        return {
            "transmutations_in_window": len(self._timestamps),
            "window_ms": self._config.window_ms,
            "max_transmutations": self._config.max_transmutations,
            "files_touched": list(self._per_file_timestamps.keys()),
        }

    def reset(self) -> None:
        self._timestamps.clear()
        self._per_file_timestamps.clear()

    def _purge_old_timestamps(self) -> None:
        cutoff = time.time() * 1000 - self._config.window_ms
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict):
            fp = input_data.get("file_path", "")
            if fp:
                bc = self.check(fp)
                return {
                    "allowed": bc.allowed,
                    "reason": bc.reason,
                    "message": bc.message,
                }
        return self.get_stats()
