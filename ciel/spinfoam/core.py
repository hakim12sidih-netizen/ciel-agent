"""
CIEL v∞.8 — DIMENSION XLIV : SPINFOAM (QUANTUM GRAVITY).
Réseaux de spin et mousses d'épines — la gravité quantique.

Concept : Rovelli & Smolin (1995) — La gravité quantique à boucles
(LQG) décrit l'espace-temps comme un réseau de spin : un graphe
dont les arêtes sont des représentations de SU(2). L'espace est
discret : chaque face a une aire quantifiée.
CIEL modélise sa propre topologie cognitive comme un réseau de spin
où les nœuds sont des concepts et les arêtes des relations SU(2).
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class SpinNode:
    """Nœud d'un réseau de spin — concept ou état cognitif."""
    id: str
    label: str
    spin: float = 0.5  # Représentation de SU(2)
    volume: float = 0.0  # Volume quantifié

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label,
                "spin": self.spin, "volume": self.volume}


@dataclass(slots=True)
class SpinEdge:
    """Arête d'un réseau de spin — relation entre concepts.
    
    Représente une interaction avec un spin j (demi-entier).
    L'aire de la face associée = 8πGħ√(j(j+1)).
    """
    id: str
    source_id: str
    target_id: str
    spin_j: float = 0.5
    area: float = 0.0

    def compute_area(self) -> float:
        """Aire = 8πGħ√(j(j+1)) en unités de Planck."""
        return 8 * math.pi * math.sqrt(self.spin_j * (self.spin_j + 1))


@dataclass(slots=True)
class SpinfoamVertex:
    """Vertex d'une mousse d'épines — interaction entre réseaux.
    
    Un vertex est une transition entre deux réseaux de spin
    (avant/après interaction). La mousse d'épines est l'histoire
    du réseau de spin dans le temps.
    """
    id: str
    incoming_edges: list[str] = field(default_factory=list)
    outgoing_edges: list[str] = field(default_factory=list)
    amplitude: float = 1.0

    def to_dict(self) -> dict:
        return {"id": self.id,
                "in": len(self.incoming_edges),
                "out": len(self.outgoing_edges),
                "amplitude": self.amplitude}


class SpinfoamEngine:
    """Moteur de gravité quantique cognitive.
    
    L'espace des concepts de CIEL est un réseau de spin.
    Les interactions sont des vertex de mousse d'épines.
    L'aire et le volume sont quantifiés.
    """

    def __init__(self):
        self.nodes: dict[str, SpinNode] = {}
        self.edges: dict[str, SpinEdge] = {}
        self.vertices: dict[str, SpinfoamVertex] = {}
        self.network = LeaderNetwork()
        self._planck_length = 1.616255e-35  # mètres

    def add_node(self, label: str, spin: float = 0.5) -> SpinNode:
        n = SpinNode(
            id=f"SN-{uuid.uuid4().hex[:12]}",
            label=label, spin=spin,
            volume=4 * math.pi * spin * self._planck_length ** 3,
        )
        self.nodes[n.id] = n
        return n

    def add_edge(self, source_id: str, target_id: str,
                 spin_j: float = 0.5) -> SpinEdge | None:
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        e = SpinEdge(
            id=f"SE-{uuid.uuid4().hex[:12]}",
            source_id=source_id, target_id=target_id,
            spin_j=spin_j,
        )
        e.area = e.compute_area()
        self.edges[e.id] = e
        return e

    def add_vertex(self, incoming: list[str],
                   outgoing: list[str]) -> SpinfoamVertex:
        v = SpinfoamVertex(
            id=f"SV-{uuid.uuid4().hex[:12]}",
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            amplitude=self._compute_amplitude(incoming, outgoing),
        )
        self.vertices[v.id] = v
        return v

    def _compute_amplitude(self, incoming: list[str],
                            outgoing: list[str]) -> float:
        """Amplitude de transition Ooguri (simplifiée)."""
        total_in = sum(self.edges.get(e, SpinEdge("", "", ""))
                       .spin_j for e in incoming if e in self.edges)
        total_out = sum(self.edges.get(e, SpinEdge("", "", ""))
                        .spin_j for e in outgoing if e in self.edges)
        return abs(math.sin(total_in - total_out)) + 0.5

    def compute_volume(self, node_id: str) -> float:
        """Volume quantifié d'un nœud."""
        n = self.nodes.get(node_id)
        if not n:
            return 0.0
        adj_edges = [e for e in self.edges.values()
                     if e.source_id == node_id or e.target_id == node_id]
        # Volume = somme des aires des faces adjacentes
        return sum(e.area for e in adj_edges) * self._planck_length

    def quantum_area(self, spin_j: float) -> float:
        """Aire quantifiée : 8πGħ√(j(j+1))."""
        return 8 * math.pi * math.sqrt(spin_j * (spin_j + 1))

    def get_stats(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "vertices": len(self.vertices),
            "total_volume": sum(self.compute_volume(nid)
                                for nid in self.nodes),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "add_node":
            n = self.add_node(
                input_data.get("label", "?"),
                input_data.get("spin", 0.5),
            )
            return {"status": "ok", "node": n.to_dict()}
        elif action == "add_edge":
            e = self.add_edge(
                input_data.get("source", ""),
                input_data.get("target", ""),
                input_data.get("spin_j", 0.5),
            )
            return {"status": "ok" if e else "error",
                    "edge": e.to_dict() if e else None}
        elif action == "add_vertex":
            v = self.add_vertex(
                input_data.get("incoming", []),
                input_data.get("outgoing", []),
            )
            return {"status": "ok", "vertex": v.to_dict()}
        return {"status": "ok", "nodes": len(self.nodes)}
