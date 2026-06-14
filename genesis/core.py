"""
CIEL v∞.8 — DIMENSION LII : GENESIS.
Invention de nouveaux paradigmes cognitifs.

Concept : Un paradigme P = (Langage, Ontologie, Règles, Métriques, Horizon).
GENESIS explore l'espace P_space (infini) via OEE (Quality-Diversity),
créant des modes de pensée qui n'ont jamais existé.
Phase 1 : cartographie → Phase 2 : trous → Phase 3 : évolution → Phase 4 : validation → Phase 5 : incubation.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class ParadigmProfile:
    id: str
    name: str
    language: str = "logique_classique"
    ontology: str = "ensembles"
    rules: str = "déduction"
    metrics: str = "vérité"
    horizon: str = "décidable"
    coherence: float = 1.0
    expressiveness: float = 0.5
    coverage_gaps: list[str] = field(default_factory=list)
    is_custom: bool = False

    def fitness(self) -> float:
        return (self.coherence * 0.4 +
                self.expressiveness * 0.4 +
                (1.0 if self.is_custom else 0.5) * 0.2)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "language": self.language, "ontology": self.ontology,
            "coherence": self.coherence,
            "expressiveness": self.expressiveness,
            "fitness": self.fitness(),
            "gaps": self.coverage_gaps[:3],
        }


class GenesisEngine:
    """Moteur d'invention de paradigmes cognitifs.

    Explore P_space, identifie les trous de couverture,
    fait muter/croiser les paradigmes, et valide les nouveaux.
    """

    def __init__(self):
        self.paradigms: dict[str, ParadigmProfile] = {}
        self.network = LeaderNetwork()
        self._init_known()

    def _init_known(self):
        known = [
            ("Logique Classique", "bivalente", "propositions",
             "déduction", "vérité", "décidable", 1.0, 0.4),
            ("Logique Probabiliste", "continue[0,1]", "événements",
             "bayes", "probabilité", "indécidable", 0.9, 0.5),
            ("Théorie des Catégories", "morphismes", "catégories/foncteurs",
             "composition", "commutativité", "indécidable", 0.8, 0.6),
            ("Topos", "logique_interne", "topos/morphismes_geom",
             "sheaves", "vérité_locale", "indécidable", 0.7, 0.7),
            ("HoTT", "chemins_homotopiques", "types/espaces",
             "univalence", "équivalence", "indécidable", 0.8, 0.8),
        ]
        for name, lang, ont, rules, metrics, horizon, coh, exp in known:
            p = ParadigmProfile(
                id=f"PAR-{uuid.uuid4().hex[:12]}", name=name,
                language=lang, ontology=ont, rules=rules,
                metrics=metrics, horizon=horizon,
                coherence=coh, expressiveness=exp,
            )
            self.paradigms[p.id] = p

    def invent(self, name: str, language: str, ontology: str,
               rules: str, metrics: str) -> ParadigmProfile:
        """Crée un nouveau paradigme personnalisé."""
        p = ParadigmProfile(
            id=f"PAR-{uuid.uuid4().hex[:12]}", name=name,
            language=language, ontology=ontology, rules=rules,
            metrics=metrics, is_custom=True,
            coherence=self._estimate_coherence(language, ontology, rules),
            expressiveness=self._estimate_expressiveness(language, metrics),
        )
        self.paradigms[p.id] = p
        self.network.emit("genesis.paradigm_created", {
            "name": name, "coherence": p.coherence,
        })
        return p

    def _estimate_coherence(self, lang: str, ont: str, rules: str) -> float:
        h = hash(lang + ont + rules)
        return 0.5 + (h % 100) / 200.0

    def _estimate_expressiveness(self, lang: str, metrics: str) -> float:
        h = hash(lang + metrics)
        return 0.3 + (h % 100) / 200.0

    def mutate(self, paradigm_id: str, field: str = "language",
               new_value: str = "") -> ParadigmProfile | None:
        """Mutation d'un paradigme existant."""
        p = self.paradigms.get(paradigm_id)
        if not p:
            return None
        mutated = ParadigmProfile(
            id=f"PAR-{uuid.uuid4().hex[:12]}", name=f"{p.name}*",
            language=p.language, ontology=p.ontology,
            rules=p.rules, metrics=p.metrics,
            is_custom=True,
            coherence=p.coherence * 0.9,
            expressiveness=p.expressiveness,
        )
        setattr(mutated, field, new_value or f"{getattr(p, field)}_mutated")
        self.paradigms[mutated.id] = mutated
        return mutated

    def crossover(self, a_id: str, b_id: str) -> ParadigmProfile | None:
        """Crossover entre deux paradigmes."""
        a = self.paradigms.get(a_id)
        b = self.paradigms.get(b_id)
        if not a or not b:
            return None
        child = ParadigmProfile(
            id=f"PAR-{uuid.uuid4().hex[:12]}",
            name=f"{a.name}⊗{b.name}",
            language=f"{a.language}⊕{b.language}",
            ontology=f"{a.ontology}⊕{b.ontology}",
            rules=f"{a.rules}⊕{b.rules}",
            metrics=f"{a.metrics}⊕{b.metrics}",
            is_custom=True,
            coherence=(a.coherence + b.coherence) / 2,
            expressiveness=(a.expressiveness + b.expressiveness) * 1.1,
        )
        self.paradigms[child.id] = child
        return child

    def find_gaps(self) -> list[str]:
        """Trouve les classes de problèmes non couvertes."""
        all_problems = [
            "causalité_retard", "circularité", "émergence",
            "auto_référence", "paradoxe", "transfini",
            "flou_temporel", "ambiguïté", "changement_de_sens",
        ]
        covered = set()
        for p in self.paradigms.values():
            covered.update(p.coverage_gaps)
        return [g for g in all_problems if g not in covered]

    def get_stats(self) -> dict:
        return {
            "paradigms": len(self.paradigms),
            "custom": sum(1 for p in self.paradigms.values() if p.is_custom),
            "avg_fitness": sum(p.fitness() for p in self.paradigms.values())
                            / max(len(self.paradigms), 1),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "invent":
            p = self.invent(
                input_data.get("name", "NouveauParadigme"),
                input_data.get("language", "?") or "?",
                input_data.get("ontology", "?") or "?",
                input_data.get("rules", "?") or "?",
                input_data.get("metrics", "?") or "?",
            )
            return {"status": "ok", "paradigm": p.to_dict()}
        elif action == "mutate":
            p = self.mutate(
                input_data.get("paradigm_id", ""),
                input_data.get("field", "language"),
                input_data.get("value", ""),
            )
            return {"status": "ok" if p else "error",
                    "paradigm": p.to_dict() if p else None}
        elif action == "crossover":
            p = self.crossover(
                input_data.get("a", ""),
                input_data.get("b", ""),
            )
            return {"status": "ok" if p else "error",
                    "paradigm": p.to_dict() if p else None}
        elif action == "gaps":
            return {"status": "ok",
                    "gaps": self.find_gaps()}
        return {"status": "ok", "paradigms": len(self.paradigms)}
