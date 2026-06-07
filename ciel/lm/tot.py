from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SearchStrategy(Enum):
    BFS = "bfs"
    DFS = "dfs"
    BEAM = "beam"
    MCTS = "mcts"
    BEST_FIRST = "best_first"


@dataclass(slots=True)
class ThoughtNode:
    id: str
    content: str
    parent: ThoughtNode | None = None
    children: list[ThoughtNode] = field(default_factory=list)
    value: float = 0.0
    visits: int = 0
    depth: int = 0
    is_terminal: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_child(self, child: ThoughtNode) -> None:
        child.parent = self
        child.depth = self.depth + 1
        self.children.append(child)

    def ucb_score(self, exploration: float = 1.4) -> float:
        if self.visits == 0:
            return float("inf")
        if self.parent is None:
            return self.value / self.visits
        exploit = self.value / self.visits
        explore = exploration * math.sqrt(math.log(self.parent.visits + 1) / self.visits)
        return exploit + explore

    def path_to_root(self) -> list[ThoughtNode]:
        path = []
        node: ThoughtNode | None = self
        while node:
            path.append(node)
            node = node.parent
        return list(reversed(path))


class TreeOfThoughts:
    """Tree of Thoughts — recherche arborescente dans l'espace des pensées.

    BFS/DFS/MCTS pour explorer plusieurs chemins de raisonnement.
    """

    def __init__(
        self,
        max_depth: int = 5,
        branching_factor: int = 3,
        strategy: SearchStrategy = SearchStrategy.BFS,
        beam_width: int = 5,
    ) -> None:
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.strategy = strategy
        self.beam_width = beam_width
        self.root = ThoughtNode(id="root", content="")
        self._evaluator: Callable[[str], float] | None = None
        self._generator: Callable[[str, int], list[str]] | None = None

    def set_evaluator(self, evaluator: Callable[[str], float]) -> None:
        self._evaluator = evaluator

    def set_generator(self, generator: Callable[[str, int], list[str]]) -> None:
        self._generator = generator

    def generate_thoughts(self, context: str, n: int) -> list[str]:
        if self._generator:
            return self._generator(context, n)
        return [f"Pensée {i} à partir de: {context[:30]}..." for i in range(n)]

    def evaluate_thought(self, thought: str) -> float:
        if self._evaluator:
            return self._evaluator(thought)
        return random.random()

    def search(self, problem: str) -> ThoughtNode:
        self.root = ThoughtNode(id="root", content=problem)
        match self.strategy:
            case SearchStrategy.BFS:
                return self._bfs()
            case SearchStrategy.DFS:
                return self._dfs()
            case SearchStrategy.BEAM:
                return self._beam()
            case SearchStrategy.MCTS:
                return self._mcts()
            case SearchStrategy.BEST_FIRST:
                return self._best_first()

    def _bfs(self) -> ThoughtNode:
        queue: list[ThoughtNode] = [self.root]
        best = self.root
        while queue and queue[0].depth < self.max_depth:
            node = queue.pop(0)
            thoughts = self.generate_thoughts(node.content, self.branching_factor)
            for t in thoughts:
                child = ThoughtNode(id=f"{node.id}_{len(node.children)}", content=t)
                child.value = self.evaluate_thought(t)
                node.add_child(child)
                if child.value > best.value:
                    best = child
                if child.depth < self.max_depth:
                    queue.append(child)
        return best

    def _dfs(self) -> ThoughtNode:
        stack: list[ThoughtNode] = [self.root]
        best = self.root
        while stack:
            node = stack.pop()
            if node.depth >= self.max_depth or node.is_terminal:
                continue
            thoughts = self.generate_thoughts(node.content, self.branching_factor)
            for t in thoughts:
                child = ThoughtNode(id=f"{node.id}_{len(node.children)}", content=t)
                child.value = self.evaluate_thought(t)
                node.add_child(child)
                if child.value > best.value:
                    best = child
                stack.append(child)
        return best

    def _beam(self) -> ThoughtNode:
        candidates: list[ThoughtNode] = [self.root]
        best = self.root
        for _ in range(self.max_depth):
            next_candidates: list[ThoughtNode] = []
            for node in candidates:
                thoughts = self.generate_thoughts(node.content, self.branching_factor)
                for t in thoughts:
                    child = ThoughtNode(id=f"{node.id}_{len(node.children)}", content=t)
                    child.value = self.evaluate_thought(t)
                    node.add_child(child)
                    next_candidates.append(child)
                    if child.value > best.value:
                        best = child
            next_candidates.sort(key=lambda n: n.value, reverse=True)
            candidates = next_candidates[:self.beam_width]
            if not candidates:
                break
        return best

    def _mcts(self, iterations: int = 50) -> ThoughtNode:
        for _ in range(iterations):
            node = self._select(self.root)
            if node.depth < self.max_depth and not node.is_terminal:
                node = self._expand(node)
            reward = self._simulate(node)
            self._backpropagate(node, reward)
        return max(self._collect_leaves(self.root), key=lambda n: n.visits, default=self.root)

    def _select(self, node: ThoughtNode) -> ThoughtNode:
        while node.children and node.depth < self.max_depth:
            node = max(node.children, key=lambda c: c.ucb_score())
        return node

    def _expand(self, node: ThoughtNode) -> ThoughtNode:
        thoughts = self.generate_thoughts(node.content, self.branching_factor)
        for t in thoughts:
            child = ThoughtNode(id=f"{node.id}_{len(node.children)}", content=t)
            child.value = self.evaluate_thought(t)
            node.add_child(child)
        return random.choice(node.children) if node.children else node

    def _simulate(self, node: ThoughtNode) -> float:
        return node.value

    def _backpropagate(self, node: ThoughtNode, reward: float) -> None:
        while node:
            node.visits += 1
            node.value += reward
            node = node.parent

    def _collect_leaves(self, node: ThoughtNode) -> list[ThoughtNode]:
        if not node.children:
            return [node]
        leaves = []
        for c in node.children:
            leaves.extend(self._collect_leaves(c))
        return leaves

    def _best_first(self) -> ThoughtNode:
        import heapq
        heap: list[tuple[float, ThoughtNode]] = [(0.0, self.root)]
        best = self.root
        while heap:
            neg_val, node = heapq.heappop(heap)
            if node.depth >= self.max_depth:
                continue
            thoughts = self.generate_thoughts(node.content, self.branching_factor)
            for t in thoughts:
                child = ThoughtNode(id=f"{node.id}_{len(node.children)}", content=t)
                child.value = self.evaluate_thought(t)
                node.add_child(child)
                if child.value > best.value:
                    best = child
                heapq.heappush(heap, (-child.value, child))
        return best
