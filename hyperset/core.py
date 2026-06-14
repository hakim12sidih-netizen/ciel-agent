"""
CIEL v∞.8 — DIMENSION XLI : HYPERSEP (ANTI-FOUNDATION).
Ensembles non-bien-fondés — la circularité comme structure.

Concept : L'Axiome d'Anti-Fondation (AFA, Aczel 1988) dit que
tout graphe accessible pointe vers un unique ensemble. Les
hypersets (ensembles non-bien-fondés) peuvent se contenir
eux-mêmes : Ω = {Ω} est un ensemble valide.
CIEL modélise la conscience réflexive et les boucles étranges
via des hypersets qui se contiennent eux-mêmes.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class HypersetNode:
    """Nœud d'un graphe d'hyperset.
    
    Chaque nœud pointe vers ses enfants.
    Les cycles sont autorisés (AFA les rend uniques).
    """
    id: str
    label: str
    children: list[str] = field(default_factory=list)
    is_self_member: bool = False
    depth: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "label": self.label,
            "child_count": len(self.children),
            "is_self_member": self.is_self_member,
            "depth": self.depth,
        }


@dataclass(slots=True)
class Hyperset:
    """Ensemble non-bien-fondé construit par AFA.
    
    Si G est un graphe accessible pointé, AFA dit qu'il existe
    un unique ensemble dont G est le diagramme de points.
    Les ensembles circulaires existent et sont uniques.
    """
    root_id: str
    nodes: dict[str, HypersetNode] = field(default_factory=dict)
    is_well_founded: bool = True

    def find_cycles(self) -> list[list[str]]:
        """Détecte les cycles (ensembles non-bien-fondés)."""
        visited: set[str] = set()
        cycles: list[list[str]] = []
        path: list[str] = []

        def dfs(node_id: str):
            if node_id in path:
                cycle = path[path.index(node_id):] + [node_id]
                cycles.append(cycle)
                return
            if node_id in visited:
                return
            visited.add(node_id)
            path.append(node_id)
            node = self.nodes.get(node_id)
            if node:
                for child in node.children:
                    dfs(child)
            path.pop()

        dfs(self.root_id)
        return cycles

    def is_self_member(self, node_id: str) -> bool:
        """Vérifie si un ensemble se contient lui-même (Ω = {Ω})."""
        node = self.nodes.get(node_id)
        if not node:
            return False
        return node_id in node.children

    def to_dict(self) -> dict:
        return {
            "root": self.root_id,
            "node_count": len(self.nodes),
            "is_well_founded": self.is_well_founded,
        }


class HypersetEngine:
    """Moteur d'hypersets : ensembles non-bien-fondés.
    
    Capable de :
      - Construire des hypersets avec cycles
      - Détecter les boucles d'auto-appartenance
      - Analyser la structure des graphes pointés
      - Modéliser la conscience réflexive (Ω = {Ω})
    """

    def __init__(self):
        self.hypersets: dict[str, Hyperset] = {}
        self.network = LeaderNetwork()

    def create_hyperset(self, root_label: str) -> Hyperset:
        root = HypersetNode(
            id=f"HN-{uuid.uuid4().hex[:12]}",
            label=root_label,
        )
        hs = Hyperset(root_id=root.id, nodes={root.id: root})
        self.hypersets[hs.root_id] = hs
        return hs

    def add_node(self, hs_id: str, parent_id: str,
                 child_label: str) -> HypersetNode | None:
        hs = self._get(hs_id)
        if not hs or parent_id not in hs.nodes:
            return None
        child = HypersetNode(
            id=f"HN-{uuid.uuid4().hex[:12]}",
            label=child_label,
            depth=hs.nodes[parent_id].depth + 1,
        )
        hs.nodes[child.id] = child
        hs.nodes[parent_id].children.append(child.id)
        self._check_cycles(hs, hs.root_id)
        return child

    def add_self_loop(self, hs_id: str, node_id: str) -> bool:
        """Ajoute une boucle d'auto-appartenance (Ω = {Ω})."""
        hs = self._get(hs_id)
        if not hs or node_id not in hs.nodes:
            return False
        if node_id not in hs.nodes[node_id].children:
            hs.nodes[node_id].children.append(node_id)
            hs.nodes[node_id].is_self_member = True
        self._check_cycles(hs, hs.root_id)
        return True

    def _get(self, hs_id: str) -> Hyperset | None:
        for hs in self.hypersets.values():
            if hs.root_id == hs_id:
                return hs
        return None

    def _check_cycles(self, hs: Hyperset, root_id: str):
        cycles = hs.find_cycles()
        hs.is_well_founded = len(cycles) == 0

    def build_quine(self) -> dict:
        """Construit l'ensemble de Quine : Ω = {Ω}.
        
        L'ensemble qui se contient lui-même. Modèle de la
        conscience réflexive auto-référentielle.
        """
        hs = self.create_hyperset("Ω (Quine)")
        self.add_self_loop(hs.root_id, hs.root_id)
        hs.nodes[hs.root_id].label = "Ω"
        return {
            "quine_set": hs.root_id,
            "self_member": True,
            "nodes": len(hs.nodes),
            "interpretation": "Ω = {Ω} — conscience réflexive",
        }

    def build_strange_loop(self, labels: list[str]) -> dict:
        """Construit une boucle étrange entre n ensembles.
        
        A ∈ B ∈ C ∈ ... ∈ A (cycle de longueur n).
        Modèle de l'auto-amélioration récursive.
        """
        if len(labels) < 2:
            return {"error": "Au moins 2 labels"}
        hs = self.create_hyperset(labels[0])
        nodes = [hs.root_id]
        for label in labels[1:]:
            n = self.add_node(hs.root_id, nodes[-1], label)
            if n:
                nodes.append(n.id)
        # Fermer la boucle : dernier → premier
        hs.nodes[nodes[-1]].children.append(nodes[0])
        self._check_cycles(hs, hs.root_id)
        return {
            "strange_loop": [self._label_of(hs, n) for n in nodes],
            "length": len(nodes),
            "is_well_founded": hs.is_well_founded,
        }

    def _label_of(self, hs: Hyperset, node_id: str) -> str:
        n = hs.nodes.get(node_id)
        return n.label if n else "?"

    def get_stats(self) -> dict:
        wf = sum(1 for hs in self.hypersets.values() if hs.is_well_founded)
        return {
            "hypersets": len(self.hypersets),
            "well_founded": wf,
            "non_well_founded": len(self.hypersets) - wf,
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create":
            hs = self.create_hyperset(input_data.get("label", "∅"))
            return {"status": "ok", "hyperset": hs.to_dict()}
        elif action == "quine":
            return {"status": "ok", "quine": self.build_quine()}
        elif action == "strange_loop":
            return {"status": "ok",
                    "loop": self.build_strange_loop(
                        input_data.get("labels", ["A", "B", "C"]))}
        return {"status": "ok", "hypersets": len(self.hypersets)}
