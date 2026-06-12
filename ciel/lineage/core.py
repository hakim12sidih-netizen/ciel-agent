"""
CIEL v∞.8 — DIMENSION LXV : CIEL-LINEAGE.
Généalogie des agents — ancêtres, descendants, héritage génétique.

Concept : Chaque agent a une lignée avec héritage des compétences
(top 50% skills), mémoire épisodique partielle, axiomes intacts.
Mutations possibles (positives 5%, légendaires 0.1%). Résonance
de lignée entre agents de même sang. Ancêtres légendaires →
bonus fitness pour les descendants.
"""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class AgentAncestor:
    id: str
    name: str
    generation: int = 0
    skills: list[str] = field(default_factory=list)
    is_legendary: bool = False
    legendary_deed: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "gen": self.generation, "legendary": self.is_legendary,
                "skills": len(self.skills)}


@dataclass(slots=True)
class LineageNode:
    id: str
    name: str
    agent_type: str = "generic"
    generation: int = 0
    parent_ids: list[str] = field(default_factory=list)
    child_ids: list[str] = field(default_factory=list)
    inherited_skills: list[str] = field(default_factory=list)
    own_skills: list[str] = field(default_factory=list)
    fitness: float = 1.0
    is_alive: bool = True
    is_legendary: bool = False

    @property
    def all_skills(self) -> list[str]:
        return list(set(self.inherited_skills + self.own_skills))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "gen": self.generation, "type": self.agent_type,
                "fitness": round(self.fitness, 3),
                "n_skills": len(self.all_skills),
                "alive": self.is_alive,
                "legendary": self.is_legendary}


class LineageEngine:
    """Moteur de généalogie et héritage des agents.

    Arbre généalogique complet, héritage des compétences,
    mutations, ancêtres légendaires, résonance de lignée.
    """

    def __init__(self):
        self.nodes: dict[str, LineageNode] = {}
        self.legendary_ancestors: list[AgentAncestor] = []
        self.network = LeaderNetwork()
        self._init_root()

    def _init_root(self):
        root = self.create_agent("CIEL", agent_type="primordial",
                                 generation=0, fitness=1.0)
        root.is_legendary = True
        self.legendary_ancestors.append(AgentAncestor(
            id=root.id, name=root.name, generation=0,
            skills=["Tous"], is_legendary=True,
            legendary_deed="Création de l'écosystème CIEL",
        ))

    def create_agent(self, name: str, agent_type: str = "generic",
                     generation: int = 1,
                     parent_ids: list[str] | None = None,
                     fitness: float = 1.0) -> LineageNode:
        n = LineageNode(
            id=f"LNG-{uuid.uuid4().hex[:12]}",
            name=name, agent_type=agent_type,
            generation=generation,
            parent_ids=parent_ids or [],
            fitness=fitness,
        )
        if parent_ids:
            inherited = []
            for pid in parent_ids:
                parent = self.nodes.get(pid)
                if parent:
                    parent.child_ids.append(n.id)
                    # Inherit top skills
                    parent_skills = parent.all_skills
                    n_inherit = max(1, len(parent_skills) // 2)
                    inherited.extend(random.sample(
                        parent_skills, min(n_inherit, len(parent_skills))))
            n.inherited_skills = list(set(inherited))
            # Check for legendary ancestor bonus
            for anc in self.legendary_ancestors:
                if anc.id in parent_ids:
                    n.fitness *= 1.05
                    break
            # Mutations
            self._apply_mutations(n)
        self.nodes[n.id] = n
        return n

    def _apply_mutations(self, node: LineageNode):
        r = random.random()
        if r < 0.001:  # 0.1% — mutation légendaire
            node.own_skills.append("Unique Skill Inattendu")
            node.is_legendary = True
            self.legendary_ancestors.append(AgentAncestor(
                id=node.id, name=node.name,
                generation=node.generation,
                skills=node.own_skills, is_legendary=True,
                legendary_deed="Mutation légendaire spontanée",
            ))
            node.fitness *= 1.2
        elif r < 0.05:  # 5% — mutation positive
            node.own_skills.append(f"Skill_Muté_{uuid.uuid4().hex[:4]}")
            node.fitness *= 1.1
        elif r < 0.15:  # 10% — mutation neutre
            node.own_skills.append(f"Variante_{uuid.uuid4().hex[:4]}")
        elif r < 0.20:  # 5% — mutation négative
            node.fitness *= 0.9

    def lineage_depth(self, node_id: str) -> int:
        node = self.nodes.get(node_id)
        if not node or not node.parent_ids:
            return 0
        return 1 + max(self.lineage_depth(pid) for pid in node.parent_ids)

    def lineage_共振(self, a_id: str, b_id: str) -> dict:
        """Résonance de lignée — agents de même sang collaborent mieux."""
        a = self.nodes.get(a_id)
        b = self.nodes.get(b_id)
        if not a or not b:
            return {"resonance": 0.0}
        shared = [s for s in a.all_skills if s in b.all_skills]
        res = len(shared) / max(len(a.all_skills + b.all_skills), 1)
        return {
            "agent_a": a.name, "agent_b": b.name,
            "resonance": round(res, 3),
            "shared_skills": len(shared),
        }

    def get_descendants(self, node_id: str, max_depth: int = 10) -> list[dict]:
        result = []
        node = self.nodes.get(node_id)
        if not node:
            return result
        queue = [(cid, 1) for cid in node.child_ids]
        while queue:
            cid, depth = queue.pop(0)
            if depth > max_depth:
                continue
            child = self.nodes.get(cid)
            if child:
                result.append(child.to_dict())
                queue.extend((gc, depth + 1) for gc in child.child_ids)
        return result

    def get_stats(self) -> dict:
        return {
            "agents": len(self.nodes),
            "generations": max((n.generation for n in self.nodes.values()),
                               default=0),
            "legendary": len(self.legendary_ancestors),
            "alive": sum(1 for n in self.nodes.values() if n.is_alive),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create":
            n = self.create_agent(
                input_data.get("name", "?"),
                input_data.get("type", "generic"),
                input_data.get("gen", 1),
                input_data.get("parents"),
                input_data.get("fitness", 1.0),
            )
            return {"status": "ok", "agent": n.to_dict()}
        elif action == "descendants":
            return {"status": "ok",
                    "descendants": self.get_descendants(
                        input_data.get("agent_id", ""),
                        input_data.get("max_depth", 10))}
        elif action == "resonance":
            return {"status": "ok",
                    "resonance": self.lineage_共振(
                        input_data.get("a", ""),
                        input_data.get("b", ""))}
        return {"status": "ok", "agents": len(self.nodes)}
