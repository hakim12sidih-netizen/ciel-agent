"""
CIEL v1.0 — SkillCurator : évolution autonome des compétences.

Composant CIEL natif — conservateur de compétences.
Cycle de vie des skills :
  active ──(30d inactif)──→ stale ──(90d inactif)──→ archived

Phases du Curator :
  Phase 1 : transitions automatiques (pure Python)
  Phase 2 : consolidation LLM (création d'umbrellas)
"""
from __future__ import annotations

import json
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork
from ciel.skills.models import SkillManager, Skill


CURATOR_STALE_DAYS = 30
CURATOR_ARCHIVE_DAYS = 90
CURATOR_INTERVAL_HOURS = 168  # 7 jours


@dataclass(slots=True)
class CuratorState:
    last_run_at: float = 0.0
    total_reviews: int = 0
    total_archived: int = 0
    total_consolidated: int = 0
    total_umbrellas_created: int = 0

    def to_dict(self) -> dict:
        return {
            "last_run_at": self.last_run_at,
            "total_reviews": self.total_reviews,
            "total_archived": self.total_archived,
            "total_consolidated": self.total_consolidated,
            "total_umbrellas_created": self.total_umbrellas_created,
        }


@dataclass(slots=True)
class ConsolidationPlan:
    umbrella_name: str
    umbrella_description: str
    skills_to_absorb: list[str]
    new_body: str = ""

    def to_dict(self) -> dict:
        return {
            "umbrella": self.umbrella_name,
            "description": self.umbrella_description,
            "absorb": self.skills_to_absorb,
        }


class SkillCurator:
    """Curateur de compétences CIEL.

    S'exécute en arrière-plan pour maintenir la qualité
    et la pertinence du répertoire de skills.

    Phase 1 — Transitions automatiques (every 7 days):
      active → stale (30d sans activité)
      stale → archived (90d sans activité)

    Phase 2 — Consolidation LLM (optionnelle):
      Fusionne les skills étroites en umbrellas larges.
    """

    def __init__(self, skills_dir: str | Path = "skills"):
        self.skills_mgr = SkillManager(skills_dir)
        self._state_dir = Path(skills_dir) / ".curator"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self._state_dir / "state.json"
        self.state = self._load_state()
        self.network = LeaderNetwork()
        self._backup_dir = self._state_dir / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> CuratorState:
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                return CuratorState(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return CuratorState()

    def _save_state(self) -> None:
        self._state_file.write_text(
            json.dumps(self.state.to_dict(), indent=2), encoding="utf-8"
        )

    def should_run(self) -> bool:
        """Vérifie si le curator doit s'exécuter."""
        elapsed = time.time() - self.state.last_run_at
        return elapsed >= CURATOR_INTERVAL_HOURS * 3600

    def run(self, dry_run: bool = False) -> CuratorState:
        """Exécute le cycle complet du curator.

        Args:
            dry_run: Si True, ne fait que simuler (logging uniquement)

        Returns:
            CuratorState mis à jour
        """
        print(f"[Curator] Démarrage (dry_run={dry_run})")
        now = time.time()

        # Backup avant modifications
        if not dry_run:
            self._backup()

        # Phase 1: Transitions automatiques
        phase1 = self._phase1_auto_transitions(dry_run)
        print(f"[Curator] Phase 1: {phase1['stale']}→stale, {phase1['archived']}→archived")

        # Phase 2: Consolidation LLM
        phase2 = self._phase2_consolidation(dry_run)
        print(f"[Curator] Phase 2: {phase2['consolidated']} consolidated, "
              f"{phase2['umbrellas']} umbrellas")

        # Mise à jour de l'état
        self.state.last_run_at = now
        self.state.total_reviews += 1
        self.state.total_archived += phase1["archived"]
        self.state.total_consolidated += phase2["consolidated"]
        self.state.total_umbrellas_created += phase2["umbrellas"]
        self._save_state()

        self.network.emit("curator.completed", {
            "phase1": phase1,
            "phase2": phase2,
            "dry_run": dry_run,
        })
        return self.state

    def _phase1_auto_transitions(self, dry_run: bool) -> dict:
        """Phase 1: Transitions automatiques basées sur l'inactivité."""
        now = time.time()
        stale_count = 0
        archived_count = 0

        for skill in self.skills_mgr.list():
            if skill.state == "archived":
                continue

            age_days = (now - skill.updated_at) / 86400

            # active → stale (30 jours)
            if skill.state == "active" and age_days > CURATOR_STALE_DAYS:
                if dry_run:
                    print(f"[Curator]  → Stale: {skill.name} (inactif {age_days:.0f}j)")
                else:
                    self.skills_mgr._skills[skill.id].state = "stale"
                    stale_count += 1

            # stale → archived (90 jours)
            if skill.state == "stale" and age_days > CURATOR_ARCHIVE_DAYS:
                if dry_run:
                    print(f"[Curator]  → Archived: {skill.name} (inactif {age_days:.0f}j)")
                else:
                    self._archive_skill(skill)
                    archived_count += 1

        return {"stale": stale_count, "archived": archived_count}

    def _phase2_consolidation(self, dry_run: bool) -> dict:
        """Phase 2: Consolidation LLM — fusionne les skills similaires."""
        skills = self.skills_mgr.list(state="active")
        if len(skills) < 3:
            return {"consolidated": 0, "umbrellas": 0}

        # Détection de clusters par similarité de nom
        clusters = self._find_clusters(skills)
        consolidated = 0
        umbrellas_created = 0

        for cluster_name, cluster_skills in clusters.items():
            if len(cluster_skills) < 2:
                continue

            plan = self._build_consolidation_plan(cluster_name, cluster_skills)

            if dry_run:
                print(f"[Curator]  Plan: {plan.umbrella_name} ← {len(plan.skills_to_absorb)} skills")
                continue

            # Création de l'umbrella
            umbrella = self.skills_mgr.create(
                name=plan.umbrella_name,
                description=plan.umbrella_description,
                body=plan.new_body or self._generate_umbrella_body(cluster_skills),
                category="umbrella",
                tags=["curator-consolidated"],
            )

            # Archive les skills absorbées
            for sid in plan.skills_to_absorb:
                self._archive_skill_by_id(sid)

            consolidated += len(plan.skills_to_absorb)
            umbrellas_created += 1

        return {"consolidated": consolidated, "umbrellas": umbrellas_created}

    def _find_clusters(self, skills: list[Skill]) -> dict[str, list[Skill]]:
        """Trouve des clusters de skills par similarité lexicale."""
        clusters: dict[str, list[Skill]] = {}
        used: set[str] = set()

        for i, s1 in enumerate(skills):
            if s1.id in used:
                continue
            cluster = [s1]
            name_words = set(s1.name.lower().replace("-", " ").split())

            for j, s2 in enumerate(skills):
                if i == j or s2.id in used:
                    continue
                s2_words = set(s2.name.lower().replace("-", " ").split())
                overlap = name_words & s2_words
                common_tags = set(s1.tags) & set(s2.tags)
                if len(overlap) >= 1 or common_tags:
                    cluster.append(s2)
                    used.add(s2.id)

            if len(cluster) >= 2:
                base_name = max(set(s.name.split("-")[0] for s in cluster),
                                key=lambda n: sum(1 for s in cluster if n in s.name))
                clusters[base_name] = cluster
                used.update(s.id for s in cluster)

        return clusters

    def _build_consolidation_plan(self, base_name: str,
                                   cluster: list[Skill]) -> ConsolidationPlan:
        """Construit un plan de consolidation pour un cluster."""
        names = [s.name for s in cluster]
        umbrella_name = f"{base_name}-umbrella"
        umbrella_desc = f"Regroupe: {', '.join(names[:5])}"
        return ConsolidationPlan(
            umbrella_name=umbrella_name,
            umbrella_description=umbrella_desc,
            skills_to_absorb=[s.id for s in cluster],
            new_body="",
        )

    def _generate_umbrella_body(self, cluster: list[Skill]) -> str:
        """Génère le corps d'une skill umbrella."""
        lines = ["# Instructions consolidées\n"]
        for skill in cluster:
            lines.append(f"## {skill.name}")
            lines.append(f"Description: {skill.description}")
            if skill.body:
                lines.append(skill.body[:300])
            lines.append("")
        return "\n".join(lines)

    def _archive_skill(self, skill: Skill) -> None:
        """Déplace une skill vers les archives."""
        self.skills_mgr._skills[skill.id].state = "archived"
        archive_path = self._state_dir / "archive" / skill.id
        archive_path.mkdir(parents=True, exist_ok=True)
        (archive_path / "metadata.json").write_text(
            json.dumps(skill.to_dict(), indent=2), encoding="utf-8"
        )

    def _archive_skill_by_id(self, skill_id: str) -> None:
        skill = self.skills_mgr.get(skill_id)
        if skill:
            self._archive_skill(skill)

    def _backup(self) -> None:
        """Crée une sauvegarde avant modification."""
        import shutil as _shutil
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._backup_dir / f"pre_curator_{ts}"
        backup_path.mkdir(parents=True, exist_ok=True)
        state = {"state": self.state.to_dict()}
        (backup_path / "state.json").write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )

    def restore(self, skill_id: str) -> bool:
        """Restaure une skill archivée par son ID."""
        archive_dir = self._state_dir / "archive" / skill_id
        meta_file = archive_dir / "metadata.json"
        if not meta_file.exists():
            return False
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        skill = self.skills_mgr.create(
            name=data["name"],
            description=data["description"],
            body=data.get("body", ""),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
        )
        skill.state = "active"
        return True

    def list_archived(self) -> list[dict]:
        """Liste les skills archivées."""
        archive_dir = self._state_dir / "archive"
        if not archive_dir.exists():
            return []
        archived = []
        for skill_dir in archive_dir.iterdir():
            meta = skill_dir / "metadata.json"
            if meta.exists():
                data = json.loads(meta.read_text(encoding="utf-8"))
                archived.append(data)
        return archived

    def statistics(self) -> dict:
        return {
            "state": self.state.to_dict(),
            "active_skills": len(self.skills_mgr.list(state="active")),
            "stale_skills": len(self.skills_mgr.list(state="stale")),
            "archived_skills": len(self.list_archived()),
            "backups": len(list(self._backup_dir.iterdir())) if self._backup_dir.exists() else 0,
        }
