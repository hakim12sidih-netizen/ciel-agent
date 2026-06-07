"""
CIEL v∞.3 — CIEL-LM : Moteur de Raisonnement.

Architectures de raisonnement :
- CoT (Chain of Thought) : raisonnement linéaire pas-à-pas
- ToT (Tree of Thoughts) : recherche arborescente avec backtracking
- GoT (Graph of Thoughts) : graphe de raisonnement avec fusion/agrégation
- NTP (Neural Theorem Proving) : prouvabilité neuronale guidée
- ReAct : raisonnement + action en boucle
- STaR : self-taught reasoning (bootstrap)
- RAP : reasoning via planning (MCTS)
"""
from __future__ import annotations

from ciel.lm.cot import ChainOfThought
from ciel.lm.tot import TreeOfThoughts, ThoughtNode
from ciel.lm.got import GraphOfThoughts, ThoughtGraph
from ciel.lm.ntp import NeuralTheoremProver
from ciel.lm.reasoning import ReasoningEngine, ReasoningStep

__all__ = [
    "ChainOfThought", "TreeOfThoughts", "ThoughtNode",
    "GraphOfThoughts", "ThoughtGraph",
    "NeuralTheoremProver",
    "ReasoningEngine", "ReasoningStep",
]
