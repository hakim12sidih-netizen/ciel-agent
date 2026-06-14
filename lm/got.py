from __future__ import annotations

import math
import random
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ThoughtGraph:
    nodes: dict[str, "ThoughtVertex"] = field(default_factory=dict)
    edges: list[tuple[str, str, str]] = field(default_factory=list)  # (from, to, label)

    def add_node(self, content: str, vertex_type: str = "thought") -> str:
        vid = str(uuid.uuid4())[:8]
        self.nodes[vid] = ThoughtVertex(id=vid, content=content, vertex_type=vertex_type)
        return vid

    def add_edge(self, from_id: str, to_id: str, label: str = "leads_to") -> None:
        if from_id in self.nodes and to_id in self.nodes:
            self.edges.append((from_id, to_id, label))

    def get_children(self, vid: str) -> list[ThoughtVertex]:
        return [self.nodes[e[1]] for e in self.edges if e[0] == vid and e[1] in self.nodes]

    def get_parents(self, vid: str) -> list[ThoughtVertex]:
        return [self.nodes[e[0]] for e in self.edges if e[1] == vid and e[0] in self.nodes]

    def merge_nodes(self, ids: list[str], label: str = "merged") -> str:
        content = " | ".join(self.nodes[i].content for i in ids if i in self.nodes)
        mid = self.add_node(content, vertex_type=label)
        for i in ids:
            if i in self.nodes:
                parents = self.get_parents(i)
                for p in parents:
                    self.add_edge(p.id, mid)
                children = self.get_children(i)
                for c in children:
                    self.add_edge(mid, c.id)
        for i in ids:
            if i in self.nodes:
                self.nodes.pop(i, None)
        self.edges = [(a, b, l) for a, b, l in self.edges if a not in ids and b not in ids]
        return mid

    def topo_sort(self) -> list[ThoughtVertex]:
        visited: set[str] = set()
        result: list[ThoughtVertex] = []
        def dfs(vid: str) -> None:
            if vid in visited:
                return
            visited.add(vid)
            for c in self.get_children(vid):
                dfs(c.id)
            result.append(self.nodes[vid])
        for vid in self.nodes:
            dfs(vid)
        return list(reversed(result))


@dataclass(slots=True)
class ThoughtVertex:
    id: str
    content: str
    vertex_type: str = "thought"
    value: float = 0.0
    visits: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class GraphOfThoughts:
    """Graph of Thoughts — raisonnement en graphe avec fusion/agrégation.

    Permet le branching, le merging, le backtracking, et l'agrégation
    de chemins de raisonnement multiples dans un graphe orienté.
    """

    def __init__(self) -> None:
        self.graph = ThoughtGraph()
        self._generator: Callable[[str], list[str]] | None = None
        self._evaluator: Callable[[str], float] | None = None

    def set_generator(self, generator: Callable[[str], list[str]]) -> None:
        self._generator = generator

    def set_evaluator(self, evaluator: Callable[[str], float]) -> None:
        self._evaluator = evaluator

    def generate(self, context: str, n: int = 3) -> list[str]:
        if self._generator:
            return self._generator(context)
        return [f"Raisonnement {i}: {context[:30]}..." for i in range(n)]

    def evaluate(self, thought: str) -> float:
        if self._evaluator:
            return self._evaluator(thought)
        return random.random()

    def reason(self, problem: str, max_steps: int = 5) -> ThoughtGraph:
        self.graph = ThoughtGraph()
        root_id = self.graph.add_node(problem, vertex_type="problem")
        frontier: list[str] = [root_id]

        for step in range(max_steps):
            new_frontier: list[str] = []
            for vid in frontier:
                node = self.graph.nodes.get(vid)
                if not node:
                    continue
                thoughts = self.generate(node.content)
                for t in thoughts:
                    child_id = self.graph.add_node(t, vertex_type="thought")
                    self.graph.add_edge(vid, child_id)
                    child = self.graph.nodes[child_id]
                    child.value = self.evaluate(t)
                    new_frontier.append(child_id)
                    if "conclusion" in t.lower() or "réponse" in t.lower():
                        child.vertex_type = "conclusion"
            if new_frontier:
                # Occasional merge of complementary thoughts
                if len(new_frontier) >= 3 and step % 2 == 0:
                    merge_group = new_frontier[:3]
                    merged_id = self.graph.merge_nodes(merge_group, label="synthesis")
                    new_frontier = [merged_id] + new_frontier[3:]
            frontier = new_frontier
            if not frontier:
                break
        return self.graph

    def best_path(self) -> list[ThoughtVertex]:
        leaves = [n for n in self.graph.nodes.values() if not self.graph.get_children(n.id)]
        if not leaves:
            return []
        best = max(leaves, key=lambda n: n.value)
        path = [best]
        while True:
            parents = self.graph.get_parents(path[-1].id)
            if not parents:
                break
            path.append(max(parents, key=lambda n: n.value))
        return list(reversed(path))

    def aggregate(self) -> str:
        topo = self.graph.topo_sort()
        return "\n".join(f"[{v.vertex_type}] {v.content}" for v in topo)

    def n_paths(self) -> int:
        leaves = [n for n in self.graph.nodes.values() if not self.graph.get_children(n.id)]
        return len(leaves)
