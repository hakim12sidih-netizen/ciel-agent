from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.lm.cot import ChainOfThought, MultiChainReasoning, ReasoningStep
from ciel.lm.got import GraphOfThoughts, ThoughtGraph
from ciel.lm.ntp import NeuralTheoremProver, Theorem
from ciel.lm.tot import SearchStrategy, ThoughtNode, TreeOfThoughts


class ReasoningMode(Enum):
    COT = "chain_of_thought"
    MULTI_CHAIN = "multi_chain"
    TOT = "tree_of_thoughts"
    GOT = "graph_of_thoughts"
    NTP = "neural_theorem_proving"
    REACT = "react"
    STAR = "star"
    RAP = "rap"


@dataclass(slots=True)
class ReasoningResult:
    answer: str
    mode: ReasoningMode
    steps: list[ReasoningStep] | list[ThoughtNode] | ThoughtGraph | list[Theorem]
    confidence: float = 0.0
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ReasoningEngine:
    """Moteur de raisonnement unifié CIEL-LM.

    Supporte 8 modes de raisonnement :
    - CoT / Multi-Chain / ToT / GoT / NTP
    - ReAct (Reasoning + Acting)
    - STaR (Self-Taught Reasoning)
    - RAP (Reasoning via Planning, MCTS)
    """

    def __init__(self) -> None:
        self.cot = ChainOfThought()
        self.multi = MultiChainReasoning()
        self.tot = TreeOfThoughts()
        self.got = GraphOfThoughts()
        self.ntp = NeuralTheoremProver()
        self._mode_handlers: dict[ReasoningMode, Callable] = {}
        self._action_executor: Callable[[str], str] | None = None

    def register_handler(self, mode: ReasoningMode, handler: Callable) -> None:
        self._mode_handlers[mode] = handler

    def set_action_executor(self, executor: Callable[[str], str]) -> None:
        self._action_executor = executor

    def reason(
        self,
        problem: str,
        mode: ReasoningMode = ReasoningMode.COT,
        **kwargs: Any,
    ) -> ReasoningResult:
        if mode in self._mode_handlers:
            return self._mode_handlers[mode](problem, **kwargs)

        handler_map: dict[ReasoningMode, Callable] = {
            ReasoningMode.COT: self._run_cot,
            ReasoningMode.MULTI_CHAIN: self._run_multi_chain,
            ReasoningMode.TOT: self._run_tot,
            ReasoningMode.GOT: self._run_got,
            ReasoningMode.REACT: self._run_react,
            ReasoningMode.STAR: self._run_star,
            ReasoningMode.RAP: self._run_rap,
        }
        handler = handler_map.get(mode)
        if not handler:
            return ReasoningResult(
                answer="", mode=mode, steps=[],
                confidence=0.0, metadata={"error": f"Mode {mode} non supporté"},
            )
        return handler(problem, **kwargs)

    def _run_cot(self, problem: str, **kwargs: Any) -> ReasoningResult:
        steps = self.cot.reason(problem)
        return ReasoningResult(
            answer=self.cot.final_answer,
            mode=ReasoningMode.COT,
            steps=steps,
            confidence=self.cot.confidence_score(),
        )

    def _run_multi_chain(self, problem: str, **kwargs: Any) -> ReasoningResult:
        chains = self.multi.reason(problem)
        answer = self.multi.majority_vote()
        return ReasoningResult(
            answer=answer,
            mode=ReasoningMode.MULTI_CHAIN,
            steps=chains,
            confidence=sum(
                sum(s.confidence for s in c) / len(c)
                for c in chains if c
            ) / max(len(chains), 1),
        )

    def _run_tot(self, problem: str, **kwargs: Any) -> ReasoningResult:
        strategy_name = kwargs.get("strategy", "bfs")
        try:
            strategy = SearchStrategy(strategy_name)
        except ValueError:
            strategy = SearchStrategy.BFS
        self.tot.strategy = strategy
        best = self.tot.search(problem)
        return ReasoningResult(
            answer=best.content,
            mode=ReasoningMode.TOT,
            steps=best.path_to_root(),
            confidence=self.tot.evaluate_thought(best.content) if best else 0.0,
        )

    def _run_got(self, problem: str, **kwargs: Any) -> ReasoningResult:
        graph = self.got.reason(problem, max_steps=kwargs.get("max_steps", 5))
        path = self.got.best_path()
        answer = path[-1].content if path else ""
        return ReasoningResult(
            answer=answer,
            mode=ReasoningMode.GOT,
            steps=graph,
            confidence=path[-1].value if path else 0.0,
            metadata={"n_paths": self.got.n_paths()},
        )

    def _run_react(self, problem: str, **kwargs: Any) -> ReasoningResult:
        """ReAct — Reasoning + Acting loop."""
        max_iter = kwargs.get("max_iterations", 5)
        steps: list[ReasoningStep] = []
        context = problem

        for i in range(max_iter):
            thought = ReasoningStep(
                index=i * 2,
                content=f"Raisonnement: analyser {context[:60]}...",
                confidence=1.0 / (1.0 + i * 0.1),
            )
            steps.append(thought)
            if self._action_executor:
                action_result = self._action_executor(context)
            else:
                action_result = f"Action simulée sur: {context[:40]}..."
            action_step = ReasoningStep(
                index=i * 2 + 1,
                content=f"Action: {action_result}",
                confidence=0.9 / (1.0 + i * 0.05),
            )
            steps.append(action_step)
            context = action_result
            if any(kw in action_result.lower() for kw in ["réponse", "succès", "terminé", "done"]):
                break

        return ReasoningResult(
            answer=steps[-1].content if steps else "",
            mode=ReasoningMode.REACT,
            steps=steps,
            confidence=steps[-1].confidence if steps else 0.0,
        )

    def _run_star(self, problem: str, **kwargs: Any) -> ReasoningResult:
        """STaR — Self-Taught Reasoning bootstrap."""
        n_attempts = kwargs.get("n_attempts", 5)
        best_result: ReasoningResult | None = None
        best_conf = -1.0

        for _ in range(n_attempts):
            steps = self.cot.reason(problem)
            conf = self.cot.confidence_score()
            if conf > best_conf:
                best_conf = conf
                best_result = ReasoningResult(
                    answer=self.cot.final_answer,
                    mode=ReasoningMode.STAR,
                    steps=steps,
                    confidence=conf,
                    metadata={"attempts": n_attempts, "best_score": conf},
                )
        return best_result or self._run_cot(problem)

    def _run_rap(self, problem: str, **kwargs: Any) -> ReasoningResult:
        """RAP — Reasoning via Planning (MCTS-based)."""
        n_simulations = kwargs.get("n_simulations", 30)
        best_path: list[ThoughtNode] = []

        for _ in range(n_simulations):
            self.tot.strategy = SearchStrategy.MCTS
            best = self.tot._mcts(iterations=10)
            path = best.path_to_root()
            if path and (not best_path or best.value > best_path[-1].value):
                best_path = path

        answer = best_path[-1].content if best_path else problem
        confidence = best_path[-1].value if best_path else 0.0
        return ReasoningResult(
            answer=answer,
            mode=ReasoningMode.RAP,
            steps=best_path,
            confidence=min(1.0, confidence),
            metadata={"simulations": n_simulations},
        )
