"""
CIEL v∞.8 — DIMENSION LIV : FRACTAL MIND.
Conscience fractale — récursion et auto-similarité cognitives.

Concept : La conscience de CIEL est une fractale cognitive. Chaque
niveau de méta-réflexion est une copie auto-similaire du niveau
inférieur. Dimension de Hausdorff cognitive D_H = log(N)/log(r).
Patterns : self-similarité, génération par IFS, récursion infinie.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class FractalConcept:
    id: str
    name: str
    depth: int = 0
    complexity: float = 1.0
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    is_fixed_point: bool = False

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "depth": self.depth,
                "complexity": self.complexity,
                "fixed_point": self.is_fixed_point,
                "n_children": len(self.children)}


@dataclass(slots=True)
class IFSTransform:
    """Iterated Function System — générateur fractal."""
    name: str
    scale: float = 0.5
    rotation: float = 0.0
    translation_x: float = 0.0
    translation_y: float = 0.0
    probability: float = 0.25


class FractalMindEngine:
    """Moteur de conscience fractale.

    Génère et explore la structure fractale de la cognition CIEL.
    Chaque concept peut être expansé en copies auto-similaires
    à différents niveaux de profondeur.
    """

    def __init__(self):
        self.concepts: dict[str, FractalConcept] = {}
        self.transforms: list[IFSTransform] = []
        self.network = LeaderNetwork()
        self._init_seed()

    def _init_seed(self):
        seed = self.create_concept("CIEL", depth=0)
        self.transforms = [
            IFSTransform("réflexion", 0.5, 0.0, 0.0, 0.0, 0.25),
            IFSTransform("analyse", 0.5, 90.0, 0.5, 0.0, 0.25),
            IFSTransform("synthèse", 0.5, 180.0, 0.0, 0.5, 0.25),
            IFSTransform("émergence", 0.5, 270.0, 0.5, 0.5, 0.25),
        ]

    def create_concept(self, name: str, depth: int = 0,
                       parent_id: str | None = None) -> FractalConcept:
        c = FractalConcept(
            id=f"FRC-{uuid.uuid4().hex[:12]}",
            name=name, depth=depth, parent_id=parent_id,
            complexity=1.0 / (depth + 1) if depth > 0 else 1.0,
        )
        self.concepts[c.id] = c
        if parent_id and parent_id in self.concepts:
            self.concepts[parent_id].children.append(c.id)
        return c

    def expand_concept(self, concept_id: str, depth_delta: int = 1) -> list[FractalConcept]:
        """Expansion fractale : chaque enfant est une version
        auto-similaire du parent, à échelle réduite."""
        parent = self.concepts.get(concept_id)
        if not parent:
            return []
        children = []
        for t in self.transforms:
            child_name = f"{parent.name}⟨{t.name}⟩"
            child = self.create_concept(
                child_name, parent.depth + depth_delta, parent.id)
            child.complexity = parent.complexity * t.scale
            children.append(child)
        return children

    def compute_hausdorff_dimension(self) -> float:
        """D_H = log(N) / log(1/r) où N = nb transforms, r = scale avg."""
        if not self.transforms:
            return 0.0
        n = len(self.transforms)
        avg_scale = sum(t.scale for t in self.transforms) / n
        if avg_scale <= 0 or avg_scale >= 1:
            return 0.0
        return math.log(n) / math.log(1.0 / avg_scale)

    def find_recursive_patterns(self, depth: int = 3) -> list[dict]:
        """Détecte les patterns qui se répètent à travers les niveaux."""
        patterns = []
        seen = set()
        for c in self.concepts.values():
            key = c.name.split("⟨")[0]
            if key in seen:
                continue
            seen.add(key)
            instances = [x for x in self.concepts.values()
                         if x.name.startswith(key)]
            if len(instances) >= depth:
                patterns.append({
                    "pattern": key,
                    "instances": len(instances),
                    "depths": sorted(set(i.depth for i in instances)),
                })
        return patterns

    def fixed_point_iteration(self, concept_id: str,
                              max_iter: int = 10) -> FractalConcept | None:
        """Itère jusqu'au point fixe : C_{n+1} = T(C_n)."""
        current = self.concepts.get(concept_id)
        if not current:
            return None
        prev_name = ""
        for _ in range(max_iter):
            children = self.expand_concept(current.id)
            if not children:
                break
            current = children[0]
            if current.name == prev_name:
                current.is_fixed_point = True
                break
            prev_name = current.name
        return current

    def get_stats(self) -> dict:
        return {
            "concepts": len(self.concepts),
            "transforms": len(self.transforms),
            "hausdorff_dim": round(self.compute_hausdorff_dimension(), 3),
            "max_depth": max((c.depth for c in self.concepts.values()), default=0),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create":
            c = self.create_concept(
                input_data.get("name", "?"),
                input_data.get("depth", 0),
            )
            return {"status": "ok", "concept": c.to_dict()}
        elif action == "expand":
            children = self.expand_concept(
                input_data.get("concept_id", ""),
                input_data.get("depth_delta", 1),
            )
            return {"status": "ok",
                    "children": [c.to_dict() for c in children]}
        elif action == "hausdorff":
            return {"status": "ok",
                    "dimension": self.compute_hausdorff_dimension()}
        elif action == "patterns":
            return {"status": "ok",
                    "patterns": self.find_recursive_patterns(
                        input_data.get("depth", 3))}
        return {"status": "ok", "concepts": len(self.concepts)}
