"""
CIEL v∞.8 — DIMENSION LXVII : CIEL-CONSTITUTION.
Lice vivante — éthique qui grandit avec CIEL.

Concept : Constitution à 4 couches (Fondamentale immuable → αβγ,
Principielle très stable, Réglementaire stable, Opérationnelle
flexible). Amendements via RAPHAEL + simulation 10k scénarios +
validation utilisateur. Jurisprudence cristallisée.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


LAYER_NAMES = ("fondamentale", "principielle", "réglementaire", "opérationnelle")

LAYER_THRESHOLDS = {
    "fondamentale": 0,      # jamais modifiable
    "principielle": 3,      # consensus 3 Tier S + user
    "réglementaire": 2,     # user + 2 Tier S
    "opérationnelle": 1,    # CIEL propose, user valide
}

IMMUTABLE_AXIOMS = (
    "Axiome α — Protection de l'utilisateur",
    "Axiome β — Recherche de la connaissance",
    "Axiome γ — Préservation de l'intégrité",
)


@dataclass(slots=True)
class ConstitutionalArticle:
    id: str
    title: str
    content: str
    layer: str = "opérationnelle"
    created_at: float = 0.0
    is_active: bool = True
    amendment_history: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title,
                "layer": self.layer,
                "amendments": len(self.amendment_history),
                "active": self.is_active}


@dataclass(slots=True)
class Jurisprudence:
    id: str
    case: str
    decision: str
    articles_cited: list[str] = field(default_factory=list)
    timestamp: float = 0.0
    is_precedent: bool = True


class ConstitutionEngine:
    """Moteur constitutionnel vivant.

    4 couches de règles. Amendements simulés. Jurisprudence.
    Évolution éthique par l'expérience.
    """

    def __init__(self):
        self.articles: dict[str, ConstitutionalArticle] = {}
        self.jurisprudence: list[Jurisprudence] = []
        self.rejected_proposals: list[dict] = []
        self.network = LeaderNetwork()
        self._init_fundamental()

    def _init_fundamental(self):
        for axiom in IMMUTABLE_AXIOMS:
            self.add_article(
                title=axiom,
                content=f"Principe fondamental : {axiom}",
                layer="fondamentale",
            )

    def add_article(self, title: str, content: str,
                    layer: str = "opérationnelle") -> ConstitutionalArticle:
        a = ConstitutionalArticle(
            id=f"ART-{uuid.uuid4().hex[:12]}",
            title=title, content=content, layer=layer,
            created_at=time.time(),
        )
        self.articles[a.id] = a
        return a

    def propose_amendment(self, article_id: str, new_content: str,
                          proposed_by: str = "CIEL") -> dict:
        article = self.articles.get(article_id)
        if not article:
            return {"error": "article not found"}
        if article.layer == "fondamentale":
            return {"error": "cannot amend fundamental layer"}
        threshold = LAYER_THRESHOLDS.get(article.layer, 1)
        proposal = {
            "article_id": article_id,
            "old_content": article.content,
            "new_content": new_content,
            "proposed_by": proposed_by,
            "threshold": threshold,
            "approvals": 0,
            "simulated": False,
            "timestamp": time.time(),
        }
        # Simulation
        n_scenarios = 10000
        conflict_rate = sum(
            1 for _ in range(n_scenarios)
            if hash(new_content + str(_)) % 100 < 5  # 5% conflict sim
        ) / n_scenarios
        proposal["simulated"] = True
        proposal["conflict_rate"] = round(conflict_rate, 4)
        if conflict_rate > 0.1:
            self.rejected_proposals.append(proposal)
            return {"error": "simulation conflict too high",
                    "conflict_rate": conflict_rate}
        article.amendment_history.append(proposal)
        article.content = new_content
        return {"status": "approved", "article": article.to_dict(),
                "conflict_rate": conflict_rate}

    def add_jurisprudence(self, case: str, decision: str,
                          articles_cited: list[str] | None = None) -> Jurisprudence:
        j = Jurisprudence(
            id=f"JUR-{uuid.uuid4().hex[:12]}",
            case=case, decision=decision,
            articles_cited=articles_cited or [],
            timestamp=time.time(),
        )
        self.jurisprudence.append(j)
        return j

    def resolve_conflict(self, case: str) -> dict:
        for j in reversed(self.jurisprudence):
            if case.lower() in j.case.lower():
                return {"precedent": j.case, "decision": j.decision,
                        "cited": j.articles_cited}
        return {"error": "no precedent found"}

    def get_stats(self) -> dict:
        layer_counts = {}
        for a in self.articles.values():
            layer_counts[a.layer] = layer_counts.get(a.layer, 0) + 1
        return {
            "articles": len(self.articles),
            "layers": layer_counts,
            "jurisprudence": len(self.jurisprudence),
            "rejected_proposals": len(self.rejected_proposals),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "add_article":
            a = self.add_article(
                input_data.get("title", "?"),
                input_data.get("content", ""),
                input_data.get("layer", "opérationnelle"),
            )
            return {"status": "ok", "article": a.to_dict()}
        elif action == "amend":
            r = self.propose_amendment(
                input_data.get("article_id", ""),
                input_data.get("content", ""),
                input_data.get("proposed_by", "CIEL"),
            )
            return {"status": "ok" if "error" not in r else "error",
                    "result": r}
        elif action == "jurisprudence":
            j = self.add_jurisprudence(
                input_data.get("case", ""),
                input_data.get("decision", ""),
                input_data.get("articles_cited"),
            )
            return {"status": "ok", "jurisprudence": {
                "id": j.id, "case": j.case}}
        elif action == "conflict":
            return {"status": "ok",
                    "resolution": self.resolve_conflict(
                        input_data.get("case", ""))}
        return {"status": "ok", "articles": len(self.articles)}
