from __future__ import annotations

import json
import math
import os
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RLState:
    state: list[float] = field(default_factory=lambda: [0.0] * 12)
    weights: list[list[float]] = field(default_factory=lambda: [[0.0] * 12 for _ in range(12)])
    bias: list[float] = field(default_factory=lambda: [0.0] * 12)


@dataclass(slots=True)
class RLStepResult:
    status: str = "error"
    loss: float = 0.0
    iterations: int = 0
    weights: list[list[float]] | None = None
    bias: list[float] | None = None
    action: list[float] | None = None
    mean_reward: float = 0.0
    error: str = ""
    fallback: bool = False


DIM = 12


class TorchRLBridge:
    def __init__(
        self,
        checkpoint_path: str = "",
        timeout_ms: int = 30_000,
        force_fallback: bool = False,
    ) -> None:
        self._checkpoint_path = checkpoint_path or os.path.join(
            tempfile.gettempdir(), "hydra_rl_checkpoint.json"
        )
        self._timeout_ms = timeout_ms
        self._force_fallback = force_fallback
        self._call_count = 0
        self._fallback_count = 0

    async def train_step(self, state: list[float], reward: list[float]) -> RLStepResult:
        self._call_count += 1
        if self._force_fallback:
            self._fallback_count += 1
            return self._fallback_train_step(state, reward)
        return self._fallback_train_step(state, reward)

    def load_checkpoint(self) -> RLState | None:
        if not os.path.isfile(self._checkpoint_path):
            return None
        try:
            with open(self._checkpoint_path, encoding="utf-8") as f:
                ckpt = json.load(f)
            return RLState(
                state=ckpt.get("state", [0.0] * DIM),
                weights=ckpt.get("weights", [[0.0] * DIM for _ in range(DIM)]),
                bias=ckpt.get("bias", [0.0] * DIM),
            )
        except (OSError, json.JSONDecodeError):
            return None

    def reset_checkpoint(self) -> None:
        if os.path.isfile(self._checkpoint_path):
            os.unlink(self._checkpoint_path)

    def _fallback_train_step(self, state: list[float], reward: list[float]) -> RLStepResult:
        ckpt = self.load_checkpoint()
        W = ckpt.weights if ckpt is not None else [[0.0] * DIM for _ in range(DIM)]
        b = ckpt.bias if ckpt is not None else [0.0] * DIM
        action = [0.0] * DIM
        for i in range(DIM):
            s = b[i]
            for j in range(DIM):
                s += W[i][j] * state[j]
            action[i] = s
        max_a = max(action)
        exps = [math.exp(a - max_a) for a in action]
        sum_exps = sum(exps)
        log_sum_exp = max_a + math.log(sum_exps)
        loss = 0.0
        for i in range(DIM):
            loss -= reward[i] * (action[i] - log_sum_exp)
        lr = 0.01
        for i in range(DIM):
            for j in range(DIM):
                W[i][j] -= lr * (-reward[i] * state[j])
            b[i] -= lr * (-reward[i])
        try:
            with open(self._checkpoint_path, "w", encoding="utf-8") as f:
                json.dump({"weights": W, "bias": b, "state": state, "iterations": 1}, f)
        except OSError:
            pass
        return RLStepResult(
            status="fallback",
            fallback=True,
            loss=loss,
            iterations=1,
            weights=W,
            bias=b,
            action=action,
            mean_reward=sum(reward) / len(reward) if reward else 0.0,
        )

    def get_stats(self) -> dict[str, Any]:
        return {
            "call_count": self._call_count,
            "fallback_count": self._fallback_count,
            "fallback_rate": self._fallback_count / self._call_count if self._call_count > 0 else 0.0,
            "checkpoint_exists": os.path.isfile(self._checkpoint_path),
        }

    def process(self, input_data: Any) -> dict[str, Any]:
        if isinstance(input_data, dict):
            state = input_data.get("state", [0.0] * DIM)
            reward = input_data.get("reward", [0.0] * DIM)
            result = self._fallback_train_step(state, reward)
            return {
                "status": result.status,
                "loss": result.loss,
                "mean_reward": result.mean_reward,
                "fallback": result.fallback,
            }
        return self.get_stats()
