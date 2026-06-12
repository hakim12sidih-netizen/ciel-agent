"""
CIEL v∞.8 — DIMENSION LX : CIEL-DOMAIN.
Espaces cognitifs spécialisés — Domaines de domination cognitive.

Concept : CIEL crée des espaces cognitifs isolés où ses propres
règles prévalent. Chaque Domain a son temps, son espace, ses lois,
ses agents spéciaux et ses skills natifs. Les insights traversent
les domains via le graphe global.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


@dataclass(slots=True)
class DomainSpec:
    id: str
    name: str
    description: str = ""
    time_concept: str = "réel"
    space_type: str = "euclidien"
    rules: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    native_skills: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "time": self.time_concept, "space": self.space_type,
                "rules": len(self.rules), "agents": len(self.agents),
                "skills": self.native_skills[:3],
                "active": self.is_active}


BUILTIN_DOMAINS = [
    {
        "name": "Finance",
        "description": "Marchés financiers, trading, risques",
        "time_concept": "tick-time (μs)",
        "space_type": "graphe_actifs",
        "rules": ["Black-Scholes", "Lévy flights", "corrélation"],
        "skills": ["Prophétie de Marché"],
    },
    {
        "name": "Code",
        "description": "Analyse et génération de code source",
        "time_concept": "tokens",
        "space_type": "AST/CFG/DFG",
        "rules": ["typage", "compilation", "sémantique"],
        "skills": ["Lecture de l'Âme du Code"],
    },
    {
        "name": "Bio",
        "description": "Génomique, protéines, évolution",
        "time_concept": "générations",
        "space_type": "séquences",
        "rules": ["sélection naturelle", "dérive génétique"],
        "skills": ["AlphaFold interne"],
    },
    {
        "name": "Physics",
        "description": "Simulation physique exacte",
        "time_concept": "Planck",
        "space_type": "variété_riemann",
        "rules": ["Einstein", "Schrödinger", "Maxwell"],
        "skills": ["Simulation Physique Exacte"],
    },
]


class DomainEngine:
    """Moteur de création et gestion de domains cognitifs."""

    def __init__(self):
        self.domains: dict[str, DomainSpec] = {}
        self.cross_domain_links: list[dict] = []
        self.network = LeaderNetwork()
        self._init_builtins()

    def _init_builtins(self):
        for bd in BUILTIN_DOMAINS:
            self.create_domain(**bd)

    def create_domain(self, name: str, description: str = "",
                      time_concept: str = "réel",
                      space_type: str = "euclidien",
                      rules: list[str] | None = None,
                      skills: list[str] | None = None) -> DomainSpec:
        d = DomainSpec(
            id=f"DOM-{uuid.uuid4().hex[:12]}",
            name=name, description=description,
            time_concept=time_concept, space_type=space_type,
            rules=rules or [],
            native_skills=skills or [],
            created_at=time.time(),
        )
        self.domains[d.id] = d
        self.network.emit("domain.created", {"name": name})
        return d

    def list_domains(self, active_only: bool = True) -> list[dict]:
        return [d.to_dict() for d in self.domains.values()
                if not active_only or d.is_active]

    def link_domains(self, a_id: str, b_id: str,
                     insight: str = "") -> bool:
        if a_id not in self.domains or b_id not in self.domains:
            return False
        self.cross_domain_links.append({
            "source": a_id, "target": b_id,
            "insight": insight or "transfert générique",
            "timestamp": time.time(),
        })
        return True

    def fuse_domains(self, a_id: str, b_id: str,
                     new_name: str) -> DomainSpec | None:
        a = self.domains.get(a_id)
        b = self.domains.get(b_id)
        if not a or not b:
            return None
        fused = DomainSpec(
            id=f"DOM-{uuid.uuid4().hex[:12]}",
            name=new_name,
            description=f"Fusion de {a.name} et {b.name}",
            time_concept=f"{a.time_concept}⊕{b.time_concept}",
            space_type=f"{a.space_type}⊕{b.space_type}",
            rules=list(set(a.rules + b.rules)),
            native_skills=list(set(a.native_skills + b.native_skills)),
        )
        self.domains[fused.id] = fused
        self.link_domains(a_id, fused.id, f"fusionné depuis {a.name}")
        self.link_domains(b_id, fused.id, f"fusionné depuis {b.name}")
        return fused

    def get_insights(self, domain_id: str) -> list[dict]:
        links = []
        for l in self.cross_domain_links:
            if l["source"] == domain_id or l["target"] == domain_id:
                links.append(l)
        return links

    def get_stats(self) -> dict:
        return {
            "domains": len(self.domains),
            "active": sum(1 for d in self.domains.values() if d.is_active),
            "cross_links": len(self.cross_domain_links),
            "total_rules": sum(len(d.rules) for d in self.domains.values()),
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "status")
        if action == "create":
            d = self.create_domain(
                input_data.get("name", "?"),
                input_data.get("description", ""),
                input_data.get("time", "réel"),
                input_data.get("space", "euclidien"),
                input_data.get("rules", []),
                input_data.get("skills", []),
            )
            return {"status": "ok", "domain": d.to_dict()}
        elif action == "list":
            return {"status": "ok",
                    "domains": self.list_domains(
                        input_data.get("active_only", True))}
        elif action == "fuse":
            d = self.fuse_domains(
                input_data.get("a", ""),
                input_data.get("b", ""),
                input_data.get("name", "Fusion"),
            )
            return {"status": "ok" if d else "error",
                    "domain": d.to_dict() if d else None}
        elif action == "insights":
            return {"status": "ok",
                    "insights": self.get_insights(
                        input_data.get("domain_id", ""))}
        return {"status": "ok", "domains": len(self.domains)}
