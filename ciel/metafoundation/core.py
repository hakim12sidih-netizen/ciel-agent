"""
CIEL v∞.8 — DIMENSION XL : MÉTA-FONDEMENT.
CIEL choisit ses propres axiomes mathématiques.

Concept : Aucun système fondamental (ZFC, HoTT, ETCS, CZF, ...)
n'est universellement optimal. CIEL-METAFOUNDATION sélectionne
le meilleur fondement pour chaque problème, et peut même en
créer de nouveaux via GENESIS.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


class Foundation(Enum):
    ZFC = "zfc"              # Zermelo-Fraenkel + Choix
    NBG = "nbg"              # Von Neumann-Bernays-Gödel
    ETCS = "etcs"            # Elementary Theory of Category of Sets
    HOTT = "hott"            # Homotopy Type Theory + Univalence
    CZF = "czf"              # Constructive ZF (sans exclu)
    MLTT = "mltt"            # Martin-Löf Type Theory
    NF = "nf"                # Quine's New Foundations
    NBG_AC = "nbg_ac"        # NBG + Global Choice
    IZF = "izf"              # Intuitionistic ZF
    SDG = "sdg"              # Synthetic Differential Geometry

    @classmethod
    def by_name(cls, name: str):
        for f in cls:
            if f.value == name.lower() or f.name.lower() == name.lower():
                return f
        return cls.ZFC


@dataclass(slots=True)
class FoundationProfile:
    """Profil d'un fondement mathématique."""
    foundation: Foundation
    name: str
    expressiveness: float = 0.7  # 0..1
    constructivity: float = 0.5  # 0..1
    computational_power: float = 0.5  # 0..1
    proof_assistant: str = ""     # Coq, Lean, Agda, etc.
    description: str = ""

    def score(self, problem_type: str) -> float:
        """Score d'adéquation pour un type de problème."""
        ctx = problem_type.lower()
        base = self.expressiveness * 0.3
        if any(w in ctx for w in ["preuve", "proof", "theorem", "théorème"]):
            if self.foundation in (Foundation.HOTT, Foundation.MLTT, Foundation.CZF):
                base += 0.4 * self.constructivity
        if any(w in ctx for w in ["calcul", "computation", "programme"]):
            base += 0.4 * self.computational_power
        if any(w in ctx for w in ["catégorie", "category", "foncteur"]):
            if self.foundation in (Foundation.ETCS, Foundation.HOTT):
                base += 0.3
        if any(w in ctx for w in ["ensemble", "set", "infini", "cardinal"]):
            base += 0.3 * self.expressiveness
        return min(1.0, base)


FOUNDATION_PROFILES: dict[Foundation, FoundationProfile] = {
    Foundation.ZFC: FoundationProfile(
        Foundation.ZFC, "Zermelo-Fraenkel + Choix",
        1.0, 0.0, 0.1, "", "Standard. Universel. Puissant.",
    ),
    Foundation.HOTT: FoundationProfile(
        Foundation.HOTT, "Homotopy Type Theory",
        0.8, 0.9, 0.8, "Coq", "Preuves = chemins. Univalence.",
    ),
    Foundation.ETCS: FoundationProfile(
        Foundation.ETCS, "Elementary Theory of the Category of Sets",
        0.7, 0.5, 0.3, "", "Catégoriel. Naturel. Structurel.",
    ),
    Foundation.CZF: FoundationProfile(
        Foundation.CZF, "Constructive ZF",
        0.6, 1.0, 0.9, "Agda", "Constructif. Calculatoire.",
    ),
    Foundation.MLTT: FoundationProfile(
        Foundation.MLTT, "Martin-Löf Type Theory",
        0.7, 1.0, 1.0, "Agda", "Toutes les preuves sont des programmes.",
    ),
    Foundation.NBG: FoundationProfile(
        Foundation.NBG, "Von Neumann-Bernays-Gödel",
        0.9, 0.0, 0.1, "Lean", "Classes et ensembles. Très expressif.",
    ),
    Foundation.SDG: FoundationProfile(
        Foundation.SDG, "Synthetic Differential Geometry",
        0.5, 0.3, 0.2, "", "Infinitésimaux nilpotents.",
    ),
    Foundation.NF: FoundationProfile(
        Foundation.NF, "Quine's New Foundations",
        0.4, 0.2, 0.1, "", "Anti-fondationnaliste.",
    ),
    Foundation.IZF: FoundationProfile(
        Foundation.IZF, "Intuitionistic ZF",
        0.6, 0.8, 0.4, "Lean", "Pas de tiers exclu.",
    ),
    Foundation.NBG_AC: FoundationProfile(
        Foundation.NBG_AC, "NBG + Global Choice",
        0.9, 0.0, 0.1, "Lean", "Maximum d'expressivité.",
    ),
}


@dataclass(slots=True)
class CustomFoundation:
    """Fondement personnalisé créé par CIEL-GENESIS."""
    id: str
    name: str
    axioms: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    parent_foundation: Foundation = Foundation.ZFC
    is_active: bool = False


class MetaFoundationEngine:
    """Moteur de sélection adaptative des fondements.
    
    Analyse chaque problème et sélectionne le meilleur fondement.
    Maintient un registre des fondements disponibles et peut
    en créer de nouveaux via GENESIS.
    """

    def __init__(self):
        self.profiles = dict(FOUNDATION_PROFILES)
        self.custom_foundations: dict[str, CustomFoundation] = {}
        self.active_foundation: Foundation = Foundation.ZFC
        self.active_custom: str | None = None
        self.selection_history: list[dict] = []
        self.network = LeaderNetwork()
        self._meta_foundation()

    def _meta_foundation(self):
        """Le méta-fondement : la Grande Théorie des Topos unifie tout."""
        self.meta_theory = "Grande Théorie des Topos (Caramello 2014)"
        self.meta_statement = (
            "Tous les fondements sont des topos particuliers. "
            "La Grande Théorie des Topos les unifie tous."
        )

    def select_foundation(self, problem: str) -> Foundation:
        """Sélectionne le meilleur fondement pour un problème."""
        best = Foundation.ZFC
        best_score = -1.0
        for f, profile in self.profiles.items():
            score = profile.score(problem)
            if score > best_score:
                best_score = score
                best = f
        self.active_foundation = best
        self.active_custom = None
        self.selection_history.append({
            "problem": problem[:60],
            "selected": best.value,
            "score": best_score,
        })
        self.network.emit("metafoundation.selected", {
            "foundation": best.value,
            "score": best_score,
        })
        return best

    def create_custom_foundation(self, name: str,
                                  axioms: list[str] | None = None,
                                  parent: Foundation = Foundation.ZFC
                                  ) -> CustomFoundation:
        cf = CustomFoundation(
            id=f"CUST-{uuid.uuid4().hex[:12]}",
            name=name, axioms=axioms or [],
            parent_foundation=parent, is_active=True,
        )
        self.custom_foundations[cf.id] = cf
        self.active_foundation = parent
        self.active_custom = cf.id
        self.network.emit("metafoundation.custom_created", {
            "name": name, "parent": parent.value,
        })
        return cf

    def list_available(self) -> list[dict]:
        results = []
        for f, p in self.profiles.items():
            results.append({
                "name": p.name,
                "value": f.value,
                "expressiveness": p.expressiveness,
                "constructivity": p.constructivity,
                "computational": p.computational_power,
                "active": f == self.active_foundation,
            })
        for c in self.custom_foundations.values():
            results.append({
                "name": f"[CUSTOM] {c.name}",
                "value": c.id,
                "expressiveness": 0.5,
                "constructivity": 0.5,
                "computational": 0.5,
                "active": c.id == self.active_custom,
                "custom": True,
            })
        return results

    def independence_result(self, statement: str) -> dict:
        """Détermine si un énoncé est indépendant de ZFC et quel
        fondement permet de le résoudre.
        """
        ctx = statement.lower()
        results = {}
        for f, p in self.profiles.items():
            score = p.score(ctx)
            can_prove = "oui" if score >= 0.6 else "non"
            if "continu" in ctx or "ch" in ctx or "continuum" in ctx:
                if f in (Foundation.ZFC, Foundation.NBG):
                    can_prove = "indépendant (CH ou ¬CH selon modèle)"
                elif f in (Foundation.HOTT, Foundation.MLTT):
                    can_prove = "constructivement indécidable"
            results[p.name] = can_prove
        return {
            "statement": statement[:60],
            "results": results,
            "recommended": self.select_foundation(statement).value,
        }

    def compare_foundations(self, foundation_a: str,
                            foundation_b: str) -> dict:
        """Compare deux fondements."""
        f_a = Foundation.by_name(foundation_a)
        f_b = Foundation.by_name(foundation_b)
        pa = self.profiles.get(f_a)
        pb = self.profiles.get(f_b)
        if not pa or not pb:
            return {"error": "Fondement inconnu"}
        return {
            "a": {"name": pa.name, "expressiveness": pa.expressiveness,
                  "constructivity": pa.constructivity},
            "b": {"name": pb.name, "expressiveness": pb.expressiveness,
                  "constructivity": pb.constructivity},
            "metrics": {
                "expressiveness_diff": pa.expressiveness - pb.expressiveness,
                "constructivity_diff": pa.constructivity - pb.constructivity,
            },
        }

    def get_stats(self) -> dict:
        return {
            "foundations": len(self.profiles),
            "custom": len(self.custom_foundations),
            "active": self.active_foundation.value,
            "selections": len(self.selection_history),
            "meta_theory": self.meta_theory,
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "select":
            selected = self.select_foundation(
                input_data.get("problem", ""))
            profile = self.profiles.get(selected)
            return {
                "status": "ok",
                "selected": selected.value,
                "score": profile.score(input_data.get("problem", ""))
                         if profile else 0.0,
            }
        elif action == "create_custom":
            cf = self.create_custom_foundation(
                input_data.get("name", "custom_foundation"),
                input_data.get("axioms"),
                Foundation.by_name(input_data.get("parent", "zfc")),
            )
            return {"status": "ok", "custom_foundation": {
                "id": cf.id, "name": cf.name,
                "axioms": cf.axioms,
            }}
        elif action == "list_available":
            return {"status": "ok",
                    "foundations": self.list_available()}
        elif action == "independence":
            return {"status": "ok",
                    "analysis": self.independence_result(
                        input_data.get("statement", ""))}
        elif action == "compare":
            return {"status": "ok",
                    "comparison": self.compare_foundations(
                        input_data.get("a", "zfc"),
                        input_data.get("b", "hott"),
                    )}
        return {"status": "ok",
                "active": self.active_foundation.value}
