from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class NEATNode:
    id: int
    node_type: str  # "input", "hidden", "output"
    activation: str = "sigmoid"
    bias: float = 0.0
    response: float = 1.0


@dataclass(slots=True)
class NEATConnection:
    innov: int
    from_node: int
    to_node: int
    weight: float
    enabled: bool = True


@dataclass(slots=True)
class NEATGenome:
    nodes: dict[int, NEATNode]
    connections: dict[int, NEATConnection]
    fitness: float = -float("inf")
    adjusted_fitness: float = -float("inf")
    species_id: int = -1


@dataclass(slots=True, frozen=True)
class NEATParams:
    n_inputs: int = 3
    n_outputs: int = 1
    population_size: int = 150
    generations: int = 100
    compatibility_threshold: float = 3.0
    compatibility_c1: float = 1.0
    compatibility_c2: float = 1.0
    compatibility_c3: float = 0.4
    survival_threshold: float = 0.2
    add_connection_rate: float = 0.05
    add_node_rate: float = 0.03
    crossover_rate: float = 0.7
    mutation_rate: float = 0.8
    weight_mutation_rate: float = 0.8
    weight_replacement_rate: float = 0.1
    weight_max: float = 3.0


class NEAT:
    """NeuroEvolution of Augmenting Topologies."""

    def __init__(
        self,
        evaluate: Callable[[NEATGenome], float],
        params: NEATParams | None = None,
    ) -> None:
        self.evaluate = evaluate
        self.params = params or NEATParams()
        self.population: list[NEATGenome] = []
        self.species: dict[int, list[int]] = {}
        self.global_innov: int = 0
        self.global_node: int = 0
        self.best_genome: NEATGenome | None = None
        self.best_fitness: float = -float("inf")
        self.history: list[float] = []
        self.generation = 0

    def _create_minimal_genome(self) -> NEATGenome:
        nodes: dict[int, NEATNode] = {}
        conns: dict[int, NEATConnection] = {}
        n_in = self.params.n_inputs
        n_out = self.params.n_outputs
        for i in range(n_in):
            nodes[i] = NEATNode(id=i, node_type="input")
        for i in range(n_out):
            nodes[n_in + i] = NEATNode(id=n_in + i, node_type="output")
        innov = 0
        for i in range(n_in):
            for j in range(n_out):
                conns[innov] = NEATConnection(innov=innov, from_node=i, to_node=n_in + j, weight=random.uniform(-self.params.weight_max, self.params.weight_max))
                innov += 1
        self.global_innov = max(self.global_innov, innov)
        self.global_node = n_in + n_out
        return NEATGenome(nodes=nodes, connections=conns)

    def initialize(self) -> None:
        self.population = [self._create_minimal_genome() for _ in range(self.params.population_size)]

    def forward(self, genome: NEATGenome, inputs: list[float]) -> list[float]:
        node_values: dict[int, float] = {}
        for nid, node in genome.nodes.items():
            if node.node_type == "input":
                idx = int(nid)
                node_values[nid] = inputs[idx] if idx < len(inputs) else 0.0
        ordered: list[int] = []
        visited: set[int] = set()
        def dfs(nid: int) -> None:
            if nid in visited:
                return
            visited.add(nid)
            for conn in genome.connections.values():
                if conn.to_node == nid and conn.enabled:
                    dfs(conn.from_node)
            ordered.append(nid)
        for nid in genome.nodes:
            dfs(nid)
        for nid in ordered:
            if nid in node_values:
                continue
            if genome.nodes[nid].node_type == "output" or genome.nodes[nid].node_type == "hidden":
                total = genome.nodes[nid].bias
                for conn in genome.connections.values():
                    if conn.to_node == nid and conn.enabled and conn.from_node in node_values:
                        total += conn.weight * node_values[conn.from_node]
                if genome.nodes[nid].activation == "sigmoid":
                    node_values[nid] = 1.0 / (1.0 + math.exp(-total * genome.nodes[nid].response))
                elif genome.nodes[nid].activation == "tanh":
                    node_values[nid] = math.tanh(total * genome.nodes[nid].response)
                elif genome.nodes[nid].activation == "relu":
                    node_values[nid] = max(0.0, total * genome.nodes[nid].response)
                else:
                    node_values[nid] = total
        outputs = []
        for nid, node in genome.nodes.items():
            if node.node_type == "output":
                outputs.append(node_values.get(nid, 0.0))
        return outputs

    def _compatibility_distance(self, g1: NEATGenome, g2: NEATGenome) -> float:
        n_excess = 0
        n_disjoint = 0
        weight_diff = 0.0
        n_matching = 0
        max_innov = max(c.innov for c in g1.connections.values()) if g1.connections else 0
        innovs2 = set(g2.connections.keys())
        for innov, c1 in g1.connections.items():
            if innov in innovs2:
                n_matching += 1
                weight_diff += abs(c1.weight - g2.connections[innov].weight)
            elif innov > max_innov - 1:
                n_excess += 1
            else:
                n_disjoint += 1
        n_total = max(len(g1.connections), len(g2.connections))
        n_total = max(n_total, 1)
        return (self.params.compatibility_c1 * n_excess / n_total +
                self.params.compatibility_c2 * n_disjoint / n_total +
                self.params.compatibility_c3 * (weight_diff / max(1, n_matching)))

    def _speciate(self) -> None:
        self.species = {}
        for i, genome in enumerate(self.population):
            found = False
            for sid, members in self.species.items():
                rep_idx = members[0]
                if self._compatibility_distance(genome, self.population[rep_idx]) < self.params.compatibility_threshold:
                    self.species[sid].append(i)
                    genome.species_id = sid
                    found = True
                    break
            if not found:
                new_sid = len(self.species)
                self.species[new_sid] = [i]
                genome.species_id = new_sid

    def _crossover(self, g1: NEATGenome, g2: NEATGenome) -> NEATGenome:
        if g2.fitness > g1.fitness:
            g1, g2 = g2, g1
        child = NEATGenome(
            nodes={nid: NEATNode(id=nid, node_type=n.node_type, activation=n.activation, bias=n.bias, response=n.response)
                   for nid, n in g1.nodes.items()},
            connections={}
        )
        for innov, c1 in g1.connections.items():
            if innov in g2.connections:
                c2 = g2.connections[innov]
                weight = c1.weight if random.random() < 0.5 else c2.weight
                enabled = c1.enabled and c2.enabled
                if (not c1.enabled or not c2.enabled) and random.random() < 0.75:
                    enabled = False
            else:
                weight = c1.weight
                enabled = c1.enabled
            child.connections[innov] = NEATConnection(innov=innov, from_node=c1.from_node, to_node=c1.to_node, weight=weight, enabled=enabled)
        return child

    def _mutate(self, genome: NEATGenome) -> None:
        if random.random() > self.params.mutation_rate:
            return
        # Weight mutation
        for conn in genome.connections.values():
            if random.random() < self.params.weight_mutation_rate:
                if random.random() < self.params.weight_replacement_rate:
                    conn.weight = random.uniform(-self.params.weight_max, self.params.weight_max)
                else:
                    conn.weight += random.gauss(0, 0.5)
                conn.weight = max(-self.params.weight_max, min(self.params.weight_max, conn.weight))
        # Add connection
        if random.random() < self.params.add_connection_rate:
            possible = []
            for fnid in genome.nodes:
                for tnid in genome.nodes:
                    if fnid == tnid:
                        continue
                    if any(c.from_node == fnid and c.to_node == tnid for c in genome.connections.values()):
                        continue
                    if genome.nodes[fnid].node_type == "output" and genome.nodes[tnid].node_type == "input":
                        continue
                    possible.append((fnid, tnid))
            if possible:
                fnid, tnid = random.choice(possible)
                self.global_innov += 1
                genome.connections[self.global_innov] = NEATConnection(
                    innov=self.global_innov, from_node=fnid, to_node=tnid,
                    weight=random.uniform(-self.params.weight_max, self.params.weight_max)
                )
        # Add node
        if random.random() < self.params.add_node_rate and genome.connections:
            conn = random.choice(list(genome.connections.values()))
            conn.enabled = False
            new_nid = self.global_node
            self.global_node += 1
            genome.nodes[new_nid] = NEATNode(id=new_nid, node_type="hidden")
            self.global_innov += 1
            genome.connections[self.global_innov] = NEATConnection(innov=self.global_innov, from_node=conn.from_node, to_node=new_nid, weight=1.0)
            self.global_innov += 1
            genome.connections[self.global_innov] = NEATConnection(innov=self.global_innov, from_node=new_nid, to_node=conn.to_node, weight=conn.weight)

    def step(self) -> None:
        for genome in self.population:
            genome.fitness = self.evaluate(genome)
            if genome.fitness > self.best_fitness:
                self.best_fitness = genome.fitness
                self.best_genome = genome
        self._speciate()
        offspring: list[NEATGenome] = []
        for sid, members in self.species.items():
            species_pop = [self.population[i] for i in members]
            species_pop.sort(key=lambda g: g.fitness, reverse=True)
            n_survive = max(1, int(len(species_pop) * self.params.survival_threshold))
            survivors = species_pop[:n_survive]
            offspring.append(survivors[0])
            while len(offspring) < self.params.population_size * len(members) / max(1, len(self.population)):
                if len(survivors) >= 2 and random.random() < self.params.crossover_rate:
                    p1, p2 = random.sample(survivors, 2)
                    child = self._crossover(p1, p2)
                else:
                    child = NEATGenome(
                        nodes={nid: NEATNode(id=nid, node_type=n.node_type, activation=n.activation, bias=n.bias, response=n.response)
                               for nid, n in random.choice(survivors).nodes.items()},
                        connections={}
                    )
                    for innov, c in random.choice(survivors).connections.items():
                        child.connections[innov] = NEATConnection(innov=innov, from_node=c.from_node, to_node=c.to_node, weight=c.weight, enabled=c.enabled)
                self._mutate(child)
                offspring.append(child)
                if len(offspring) >= self.params.population_size:
                    break
        self.population = offspring[:self.params.population_size]
        self.history.append(self.best_fitness)
        self.generation += 1

    def run(self, generations: int | None = None) -> NEATGenome:
        if not self.population:
            self.initialize()
        g = generations or self.params.generations
        for _ in range(g):
            self.step()
        return self.best_genome


class HyperNEAT(NEAT):
    """HyperNEAT — CPPN encodes connectivity patterns."""

    def __init__(
        self,
        evaluate: Callable[[NEATGenome], float],
        params: NEATParams | None = None,
        substrate_dims: tuple[int, int] = (4, 4),
    ) -> None:
        super().__init__(evaluate, params)
        self.substrate_dims = substrate_dims
        self.cppn: NEATGenome | None = None

    def query_cppn(self, cppn: NEATGenome, x1: float, y1: float, x2: float, y2: float) -> float:
        outputs = self.forward(cppn, [x1, y1, x2, y2, math.sqrt((x2 - x1)**2 + (y2 - y1)**2)])
        return outputs[0] if outputs else 0.0

    def develop_substrate(self, cppn: NEATGenome) -> NEATGenome:
        genome = NEATGenome(nodes={}, connections={})
        nid = 0
        w, h = self.substrate_dims
        for y in range(h):
            for x in range(w):
                genome.nodes[nid] = NEATNode(id=nid, node_type="input")
                nid += 1
        for y in range(h):
            for x in range(w):
                genome.nodes[nid] = NEATNode(id=nid, node_type="output")
                nid += 1
        innov = 0
        for iy in range(h):
            for ix in range(w):
                in_idx = iy * w + ix
                for oy in range(h):
                    for ox in range(w):
                        out_idx = h * w + oy * w + ox
                        x1, y1 = ix / w, iy / h
                        x2, y2 = ox / w, oy / h
                        weight = self.query_cppn(cppn, x1, y1, x2, y2)
                        if abs(weight) > 0.1:
                            genome.connections[innov] = NEATConnection(innov=innov, from_node=in_idx, to_node=out_idx, weight=weight)
                            innov += 1
        return genome
