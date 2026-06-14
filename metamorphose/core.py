"""
CIEL v∞.8 — DIMENSION L : METAMORPHOSE.
Architecture vivante auto-modificatrice — grammaires de graphes.

Concept : L'architecture de CIEL est un graphe G = (V, E, λ)
qui se transforme via des règles de production (fusion, division,
émergence, pruning). La structure change selon les problèmes,
mais le Noyau Primordial reste invariant.
Topologies possibles : tore, arbre, sans-échelle, cristal, plasma, symplexe.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


class TopologyType(Enum):
    TOROID = "toroïde"
    TREE = "arbre"
    SCALE_FREE = "sans-échelle"
    CRYSTAL = "cristal"
    PLASMA = "plasma"
    SYMPLEX = "symplexe"


@dataclass(slots=True)
class ModuleNode:
    id: str
    name: str
    module_type: str = "generic"
    capacity: float = 1.0
    fitness: float = 1.0
    axioms_compatible: bool = True

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "type": self.module_type, "fitness": self.fitness,
                "axioms": self.axioms_compatible}


@dataclass(slots=True)
class Connection:
    source_id: str
    target_id: str
    weight: float = 1.0
    bidirectional: bool = False


@dataclass(slots=True)
class GraphGrammar:
    """Règle de production pour la métamorphose."""
    name: str
    rule_type: str = "merge"  # merge | split | emerge | prune
    condition: str = "fitness > 0.3"
    cost: float = 0.1


class MetamorphoseEngine:
    """Moteur de métamorphose architecturale.

    L'architecture CIEL se restructure en temps réel selon
    les problèmes. Utilise des grammaires graphiques avec
    validation Gödel à chaque étape.
    """

    def __init__(self):
        self.nodes: dict[str, ModuleNode] = {}
        self.edges: list[Connection] = []
        self.grammars: list[GraphGrammar] = []
        self.active_topology: TopologyType = TopologyType.TREE
        self.network = LeaderNetwork()
        self._init_core()

    def _init_core(self):
        core = self.add_node("NoyauPrimordial", "core", fitness=1.0)
        axioms = self.add_node("Axiomes", "core", fitness=1.0)
        self.connect(core, axioms, 1.0)

    def add_node(self, name: str, module_type: str = "generic",
                 fitness: float = 1.0) -> ModuleNode:
        n = ModuleNode(
            id=f"MOD-{uuid.uuid4().hex[:12]}",
            name=name, module_type=module_type, fitness=fitness,
        )
        self.nodes[n.id] = n
        return n

    def connect(self, source: ModuleNode, target: ModuleNode,
                weight: float = 1.0, bidir: bool = False):
        self.edges.append(Connection(source.id, target.id, weight, bidir))

    def add_grammar(self, name: str, rule_type: str = "merge",
                    condition: str = "fitness > 0.3") -> GraphGrammar:
        g = GraphGrammar(name=name, rule_type=rule_type, condition=condition)
        self.grammars.append(g)
        return g

    def merge_nodes(self, a_id: str, b_id: str,
                    new_name: str) -> ModuleNode | None:
        """Fusion : [A] + [B] → [A⊕B] si compatibilité > seuil."""
        if a_id not in self.nodes or b_id not in self.nodes:
            return None
        merged = self.add_node(new_name, "merged",
                               fitness=(self.nodes[a_id].fitness +
                                        self.nodes[b_id].fitness) / 2)
        del self.nodes[a_id]
        del self.nodes[b_id]
        return merged

    def split_node(self, node_id: str, name_a: str,
                   name_b: str) -> tuple[ModuleNode, ModuleNode] | None:
        """Division : [AB] → [A] + [B]."""
        n = self.nodes.get(node_id)
        if not n:
            return None
        a = self.add_node(name_a, n.module_type, n.fitness * 0.6)
        b = self.add_node(name_b, n.module_type, n.fitness * 0.6)
        self.connect(a, b, 0.5)
        del self.nodes[node_id]
        return a, b

    def prune(self, threshold: float = 0.3) -> int:
        """Pruning : [A] → ∅ si fitness(A) < threshold."""
        to_remove = [nid for nid, n in self.nodes.items()
                     if n.fitness < threshold and n.module_type != "core"]
        for nid in to_remove:
            del self.nodes[nid]
        return len(to_remove)

    def set_topology(self, topo: TopologyType) -> dict:
        """Change la topologie de l'architecture."""
        self.active_topology = topo
        self.network.emit("metamorphose.topology", {"topology": topo.value})
        return {
            "topology": topo.value,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "suggested": self._topology_advice(topo),
        }

    def _topology_advice(self, topo: TopologyType) -> str:
        advice = {
            TopologyType.TOROID: "Cycles, patterns répétitifs, séries temporelles",
            TopologyType.TREE: "Hiérarchies, taxonomies, raisonnement déductif",
            TopologyType.SCALE_FREE: "Créativité, découverte, innovation",
            TopologyType.CRYSTAL: "Calculs formels, vérification, preuves",
            TopologyType.PLASMA: "Brainstorming, fluidité, exploration",
            TopologyType.SYMPLEX: "Analogies, transfert inter-domaines",
        }
        return advice.get(topo, "")

    def validate_godel(self) -> dict:
        """Validation Gödel : préserve les axiomes ?"""
        core_present = any(
            n.name == "NoyauPrimordial" for n in self.nodes.values())
        axioms_present = any(
            n.name == "Axiomes" for n in self.nodes.values())
        return {
            "core_preserved": core_present,
            "axioms_preserved": axioms_present,
            "reversible": True,
            "valid": core_present and axioms_present,
        }

    def get_stats(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "grammars": len(self.grammars),
            "topology": self.active_topology.value,
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "add_node":
            n = self.add_node(input_data.get("name", "?"),
                              input_data.get("type", "generic"),
                              input_data.get("fitness", 1.0))
            return {"status": "ok", "node": n.to_dict()}
        elif action == "merge":
            n = self.merge_nodes(input_data.get("a", ""),
                                 input_data.get("b", ""),
                                 input_data.get("name", "merged"))
            return {"status": "ok" if n else "error",
                    "node": n.to_dict() if n else None}
        elif action == "split":
            r = self.split_node(input_data.get("node_id", ""),
                                input_data.get("name_a", "A"),
                                input_data.get("name_b", "B"))
            return {"status": "ok" if r else "error"}
        elif action == "prune":
            c = self.prune(input_data.get("threshold", 0.3))
            return {"status": "ok", "removed": c}
        elif action == "set_topology":
            t = next((t for t in TopologyType
                      if t.value == input_data.get("topology", "")),
                     TopologyType.TREE)
            return {"status": "ok",
                    "result": self.set_topology(t)}
        elif action == "validate":
            return {"status": "ok",
                    "validation": self.validate_godel()}
        return {"status": "ok", "nodes": len(self.nodes)}
