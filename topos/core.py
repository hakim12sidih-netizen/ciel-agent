"""
CIEL v∞.8 — DIMENSION XXXII : TOPOS.
La logique n'est pas absolue — chaque domaine est un univers logique.

Concept : Un topos est une catégorie avec sa propre logique interne.
CIEL navigue entre topos, adaptant sa logique au contexte.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from ciel.evolution.leader_network import LeaderNetwork


class ToposType(Enum):
    SCIENCE = "science"               # Logique classique bivalente
    INCERTITUDE = "incertitude"       # Logique probabiliste [0,1]
    TEMPOREL = "temporel"             # Logique temporelle LTL
    SOCIAL = "social"                 # Logique déontique
    CREATIF = "creatif"               # Logique paraconsistante + fuzzy
    META = "meta"                     # Logique de second ordre


@dataclass(slots=True)
class TruthValue:
    """Valeur de vérité dans un topos.
    
    Dans Topos_Science : {⊤, ⊥} (booléen)
    Dans Topos_Incertitude : [0, 1] (probabilité)
    Dans Topos_Créatif : treillis flou
    """
    value: float       # 0.0 = faux, 1.0 = vrai
    confidence: float = 1.0
    context: str = ""
    
    def is_true(self, threshold: float = 0.5) -> bool:
        return self.value >= threshold
    
    def __and__(self, other: TruthValue) -> TruthValue:
        return TruthValue(
            min(self.value, other.value),
            min(self.confidence, other.confidence),
        )
    
    def __or__(self, other: TruthValue) -> TruthValue:
        return TruthValue(
            max(self.value, other.value),
            min(self.confidence, other.confidence),
        )
    
    def __invert__(self) -> TruthValue:
        return TruthValue(1.0 - self.value, self.confidence)
    
    def to_dict(self) -> dict:
        return {"value": self.value, "confidence": self.confidence,
                "context": self.context}


@dataclass(slots=True)
class GeometricMorphism:
    """Morphisme géométrique entre topos : translation de logique.
    
    f* : partie inverse (rapatrier du topos B vers A)
    f* : partie directe (traduire de A vers B)
    f! : partie extraordinaire (optimiser dans B)
    """
    id: str
    source_topos: ToposType
    target_topos: ToposType
    translation_rules: dict[str, str] = field(default_factory=dict)
    fidelity: float = 0.0  # 0..1, à quel point la traduction préserve le sens


@dataclass(slots=True)
class SubobjectClassifier:
    """L'objet classifiant Ω — ensemble des valeurs de vérité du topos."""
    topos: ToposType
    values: list[float] = field(default_factory=lambda: [0.0, 1.0])
    cardinality: str = "finite"  # finite | interval | lattice

    def classify(self, proposition: TruthValue) -> TruthValue:
        if self.topos == ToposType.SCIENCE:
            return TruthValue(
                1.0 if proposition.value >= 0.5 else 0.0,
                proposition.confidence,
            )
        return proposition


class ToposEngine:
    """Moteur multi-topos de CIEL.
    
    Maintient plusieurs topos avec leur logique interne.
    Permet la navigation inter-topos via des morphismes géométriques.
    Sélectionne automatiquement le topos adapté au problème.
    """

    def __init__(self):
        self.active_topos: ToposType = ToposType.SCIENCE
        self.topoi: dict[ToposType, SubobjectClassifier] = {}
        self.morphisms: list[GeometricMorphism] = []
        self.network = LeaderNetwork()
        self._init_topoi()

    def _init_topoi(self):
        for t in ToposType:
            if t == ToposType.SCIENCE:
                self.topoi[t] = SubobjectClassifier(t, [0.0, 1.0], "finite")
            elif t == ToposType.INCERTITUDE:
                self.topoi[t] = SubobjectClassifier(t, [0.0, 0.25, 0.5, 0.75, 1.0], "interval")
            elif t == ToposType.CREATIF:
                self.topoi[t] = SubobjectClassifier(t, list(range(11)), "lattice")
            else:
                self.topoi[t] = SubobjectClassifier(t, [0.0, 1.0], "finite")

    def evaluate(self, proposition_value: float,
                 topos: ToposType | None = None) -> TruthValue:
        """Évalue une proposition dans un topos donné."""
        t = topos or self.active_topos
        classifier = self.topoi.get(t, self.topoi[ToposType.SCIENCE])
        return classifier.classify(TruthValue(proposition_value))

    def create_morphism(self, source: ToposType, target: ToposType,
                        rules: dict[str, str] | None = None,
                        fidelity: float = 0.8) -> GeometricMorphism:
        m = GeometricMorphism(
            id=f"MORPH-{uuid.uuid4().hex[:12]}",
            source_topos=source, target_topos=target,
            translation_rules=rules or {},
            fidelity=fidelity,
        )
        self.morphisms.append(m)
        return m

    def translate(self, value: TruthValue,
                  from_topos: ToposType,
                  to_topos: ToposType) -> TruthValue:
        """Traduit une valeur de vérité entre topos."""
        morphisms = [m for m in self.morphisms
                     if m.source_topos == from_topos
                     and m.target_topos == topos]
        fidelity = 1.0
        if morphisms:
            best = max(morphisms, key=lambda m: m.fidelity)
            fidelity = best.fidelity
        return TruthValue(
            value.value * fidelity,
            value.confidence * fidelity,
            context=f"{from_topos.value}→{to_topos.value}",
        )

    def select_topos(self, context: str) -> ToposType:
        """Sélectionne automatiquement le topos adapté au contexte."""
        ctx = context.lower()
        if any(w in ctx for w in ["code", "logique", "proof", "theorem",
                                   "math", "logique", "preuve", "théorème"]):
            return ToposType.SCIENCE
        if any(w in ctx for w in ["probabilité", "risque", "prédiction",
                                   "probability", "risk", "prediction",
                                   "stat", "statistique"]):
            return ToposType.INCERTITUDE
        if any(w in ctx for w in ["temps", "évolution", "time", "evolution",
                                   "historique", "historical", "futur"]):
            return ToposType.TEMPOREL
        if any(w in ctx for w in ["éthique", "droit", "norme", "devoir",
                                   "ethics", "law", "moral", "duty"]):
            return ToposType.SOCIAL
        if any(w in ctx for w in ["créer", "inventer", "imaginer",
                                   "create", "invent", "imagine", "art"]):
            return ToposType.CREATIF
        if any(w in ctx for w in ["méta", "réflexion", "auto",
                                   "meta", "reflection", "self"]):
            return ToposType.META
        return self.active_topos

    def get_stats(self) -> dict:
        return {
            "active_topos": self.active_topos.value,
            "available_topoi": [t.value for t in self.topoi],
            "morphisms": len(self.morphisms),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "evaluate":
            tv = self.evaluate(
                input_data.get("value", 0.5),
                ToposType(input_data.get("topos", self.active_topos.value))
                if input_data.get("topos") else None,
            )
            return {"status": "ok", "truth": tv.to_dict()}
        elif action == "select_topos":
            self.active_topos = self.select_topos(
                input_data.get("context", ""))
            return {"status": "ok",
                    "selected": self.active_topos.value}
        elif action == "translate":
            tv = TruthValue(
                input_data.get("value", 0.5),
                input_data.get("confidence", 1.0),
            )
            result = self.translate(
                tv,
                ToposType(input_data.get("from", "science")),
                ToposType(input_data.get("to", "science")),
            )
            return {"status": "ok", "translated": result.to_dict()}
        elif action == "create_morphism":
            m = self.create_morphism(
                ToposType(input_data.get("source", "science")),
                ToposType(input_data.get("target", "science")),
                input_data.get("rules"),
                input_data.get("fidelity", 0.8),
            )
            return {"status": "ok",
                    "morphism": {"id": m.id, "source": m.source_topos.value,
                                 "target": m.target_topos.value}}
        return {"status": "ok", "topos": self.active_topos.value}
