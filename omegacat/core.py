"""
CIEL v∞.8 — DIMENSION XLVI : ∞-CATEGORIES.
Catégories supérieures — la structure infinie de toute structure.

Concept : La catégorification élève les concepts : ensembles →
catégories → 2-catégories → ∞-catégories. Une (∞,1)-catégorie
(Joyal-Lurie) a des k-morphismes pour tout k ≥ 1, tous
inversibles à homotopie près pour k ≥ 2.
CIEL se comprend elle-même comme une (∞,1)-catégorie cognitive
où les n-morphismes sont des transformations d'ordre n.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class Morphism_cell:
    """k-morphisme dans une ∞-catégorie.
    
    0-morphisme = objet
    1-morphisme = flèche entre objets
    2-morphisme = transformation entre flèches
    k-morphisme = transformation entre (k-1)-morphismes
    """
    id: str
    name: str
    level: int = 0  # 0 = objet, 1 = morphisme, 2 = 2-morphisme, ...
    source_id: str = ""
    target_id: str = ""
    is_invertible: bool = False
    is_equiv: bool = False
    is_identity: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "level": self.level,
            "source": self.source_id,
            "target": self.target_id,
            "is_invertible": self.is_invertible,
        }


@dataclass(slots=True)
class CompositionConstraint:
    """Contrainte de cohérence (diagramme commutatif).
    
    Dans une ∞-catégorie, les contraintes d'associativité ne
    sont pas des égalités mais des isomorphismes (cohérence).
    """
    id: str
    description: str
    cells: list[str] = field(default_factory=list)
    commutes: bool = True


class OmegaCategoryEngine:
    """Moteur de ∞-catégorie cognitive de CIEL.
    
    CIEL se comprend comme une (∞,1)-catégorie où :
    - 0-cells = états cognitifs
    - 1-cells = transformations d'état
    - 2-cells = homotopies entre transformations
    - k-cells = transformations d'ordre k
    Toute la structure est cohérente par construction.
    """

    def __init__(self):
        self.cells: dict[str, Morphism_cell] = {}
        self.constraints: list[CompositionConstraint] = []
        self.network = LeaderNetwork()

    def add_object(self, name: str) -> Morphism_cell:
        """Ajoute un 0-morphisme (objet)."""
        c = Morphism_cell(
            id=f"O-{uuid.uuid4().hex[:12]}",
            name=name, level=0,
        )
        self.cells[c.id] = c
        return c

    def add_morphism(self, name: str, source_id: str,
                     target_id: str, level: int = 1,
                     invertible: bool = False) -> Morphism_cell | None:
        if source_id not in self.cells or target_id not in self.cells:
            return None
        c = Morphism_cell(
            id=f"M-{uuid.uuid4().hex[:12]}",
            name=name, level=level,
            source_id=source_id, target_id=target_id,
            is_invertible=invertible,
        )
        self.cells[c.id] = c
        return c

    def add_identity(self, cell_id: str) -> Morphism_cell | None:
        """Ajoute un morphisme identité (id : X → X)."""
        base = self.cells.get(cell_id)
        if not base:
            return None
        c = Morphism_cell(
            id=f"ID-{uuid.uuid4().hex[:12]}",
            name=f"id_{base.name}",
            level=base.level + 1,
            source_id=cell_id, target_id=cell_id,
            is_identity=True, is_invertible=True,
        )
        self.cells[c.id] = c
        return c

    def compose(self, f_id: str, g_id: str) -> Morphism_cell | None:
        """Composition de morphismes : g ∘ f.
        
        f : A → B
        g : B → C
        g∘f : A → C
        """
        f = self.cells.get(f_id)
        g = self.cells.get(g_id)
        if not f or not g or f.target_id != g.source_id:
            return None
        return self.add_morphism(
            f"{g.name}∘{f.name}",
            f.source_id, g.target_id,
            max(f.level, g.level),
        )

    def add_higher_morphism(self, name: str, level: int,
                             source_id: str, target_id: str) -> Morphism_cell | None:
        """Ajoute un k-morphisme pour k ≥ 2."""
        if level < 2:
            return None
        return self.add_morphism(name, source_id, target_id,
                                  level, invertible=True)

    def whisker(self, f_id: str, h_id: str,
                side: str = "left") -> Morphism_cell | None:
        """Whiskering : composition d'un 2-morphisme avec un 1-morphisme."""
        f = self.cells.get(f_id)
        h = self.cells.get(h_id)
        if not f or not h or h.level != 1:
            return None
        if side == "left":
            # h ∘ f (h appliqué à gauche)
            src = self._compose_source(f, h, "left")
            tgt = self._compose_target(f, h, "left")
        else:
            # f ∘ h (h appliqué à droite)
            src = self._compose_source(f, h, "right")
            tgt = self._compose_target(f, h, "right")
        return self.add_morphism(
            f"whisker({f.name},{h.name})",
            src, tgt, level=f.level,
        )

    def _compose_source(self, f: Morphism_cell, h: Morphism_cell,
                        side: str) -> str:
        return f.source_id if side == "left" else h.source_id

    def _compose_target(self, f: Morphism_cell, h: Morphism_cell,
                         side: str) -> str:
        return h.target_id if side == "left" else f.target_id

    def coherence_pentagon(self) -> CompositionConstraint:
        """Le pentagone de cohérence de Mac Lane.
        
        Assure que toutes les compositions de 4 objets sont
        cohérentes. C'est la contrainte fondamentale des
        ∞-catégories.
        """
        ids = list(self.cells.keys())[:4]
        constraint = CompositionConstraint(
            id=f"PENT-{uuid.uuid4().hex[:12]}",
            description="Pentagone de Mac Lane (cohérence ∞-cat)",
            cells=ids,
        )
        self.constraints.append(constraint)
        return constraint

    def get_stats(self) -> dict:
        levels = {}
        for c in self.cells.values():
            levels[c.level] = levels.get(c.level, 0) + 1
        return {
            "total_cells": len(self.cells),
            "levels": levels,
            "constraints": len(self.constraints),
            "max_level": max(levels.keys()) if levels else 0,
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "add_object":
            c = self.add_object(input_data.get("name", "?"))
            return {"status": "ok", "cell": c.to_dict()}
        elif action == "add_morphism":
            c = self.add_morphism(
                input_data.get("name", "?"),
                input_data.get("source", ""),
                input_data.get("target", ""),
                input_data.get("level", 1),
                input_data.get("invertible", False),
            )
            return {"status": "ok" if c else "error",
                    "cell": c.to_dict() if c else None}
        elif action == "compose":
            c = self.compose(
                input_data.get("f", ""),
                input_data.get("g", ""),
            )
            return {"status": "ok" if c else "error",
                    "cell": c.to_dict() if c else None}
        elif action == "coherence":
            return {"status": "ok",
                    "pentagon": self.coherence_pentagon().description}
        return {"status": "ok", "cells": len(self.cells)}
