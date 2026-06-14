from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReasoningStep:
    index: int
    content: str
    confidence: float = 1.0
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ChainOfThought:
    """Chain of Thought — raisonnement linéaire pas-à-pas.

    Décompose un problème en étapes intermédiaires.
    """

    def __init__(
        self,
        max_steps: int = 10,
        stop_early: bool = True,
    ) -> None:
        self.max_steps = max_steps
        self.stop_early = stop_early
        self.steps: list[ReasoningStep] = []
        self.final_answer: str = ""
        self._step_generator: Callable[[str, int], str] | None = None

    def set_step_generator(self, generator: Callable[[str, int], str]) -> None:
        self._step_generator = generator

    def generate_step(self, problem: str, step_idx: int) -> str:
        if self._step_generator:
            return self._step_generator(problem, step_idx)
        return f"Étape {step_idx + 1} du raisonnement pour: {problem[:50]}..."

    def reason(self, problem: str) -> list[ReasoningStep]:
        self.steps = []
        for i in range(self.max_steps):
            content = self.generate_step(problem, i)
            step = ReasoningStep(index=i, content=content, confidence=1.0 / (1.0 + i * 0.1))
            self.steps.append(step)
            if self.stop_early and any(kw in content.lower() for kw in ["donc", "finalement", "conclusion", "réponse"]):
                break
        self.final_answer = self.steps[-1].content if self.steps else ""
        return self.steps

    def aggregate(self) -> str:
        return "\n".join(f"{i+1}. {s.content}" for i, s in enumerate(self.steps))

    def confidence_score(self) -> float:
        if not self.steps:
            return 0.0
        return sum(s.confidence for s in self.steps) / len(self.steps)


class MultiChainReasoning(ChainOfThought):
    """Multi-Chain — plusieurs chemins de raisonnement indépendants."""

    def __init__(self, n_chains: int = 3, max_steps: int = 10) -> None:
        super().__init__(max_steps=max_steps, stop_early=False)
        self.n_chains = n_chains
        self.chains: list[list[ReasoningStep]] = []

    def reason(self, problem: str) -> list[list[ReasoningStep]]:
        self.chains = []
        for c in range(self.n_chains):
            ChainOfThought.__init__(self, max_steps=self.max_steps, stop_early=False)
            self.chains.append(super().reason(problem))
        return self.chains

    def majority_vote(self) -> str:
        if not self.chains or not self.chains[0]:
            return ""
        answers = [c[-1].content for c in self.chains if c]
        return max(set(answers), key=answers.count)
