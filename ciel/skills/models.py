"""Skill models — extracted to avoid circular imports with curator."""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


SKILL_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


@dataclass(slots=True)
class Skill:
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "general"
    body: str = ""
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    usage_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    state: str = "active"  # active | stale | archived

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "version": self.version, "category": self.category,
            "tags": self.tags, "usage_count": self.usage_count,
            "state": self.state,
        }


class SkillManager:
    """Gestionnaire de compétences CIEL.

    Découvre, charge, crée et suit l'utilisation des skills.
    """

    def __init__(self, skills_dir: str | Path = "skills"):
        self._skills_dir = Path(skills_dir)
        self._skills_dir.mkdir(parents=True, exist_ok=True)
        self._skills: dict[str, Skill] = {}
        self._usage_file = self._skills_dir / ".usage.json"
        self._discovered = False
        self.network = LeaderNetwork()
        self._load_usage()

    def discover(self) -> list[Skill]:
        if self._discovered:
            return list(self._skills.values())
        found = []
        for skill_file in self._skills_dir.rglob("SKILL.md"):
            try:
                skill = self._parse_skill_file(skill_file)
                self._skills[skill.id] = skill
                found.append(skill)
            except Exception as e:
                print(f"[CIEL Skills] Error loading {skill_file}: {e}")
        self._discovered = True
        self.network.emit("skills.discovered", {"count": len(found)})
        return found

    def create(self, name: str, description: str, body: str = "",
               category: str = "general", tags: list[str] | None = None) -> Skill:
        skill = Skill(
            id=f"SKILL-{uuid.uuid4().hex[:12]}",
            name=name, description=description[:60],
            category=category, body=body, tags=tags or [],
        )
        self._skills[skill.id] = skill
        self._save_skill_file(skill)
        self.network.emit("skill.created", {"id": skill.id, "name": name})
        return skill

    def get(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def list(self, category: str | None = None, state: str | None = None) -> list[Skill]:
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        if state:
            skills = [s for s in skills if s.state == state]
        return skills

    def use(self, skill_id: str) -> bool:
        skill = self._skills.get(skill_id)
        if not skill:
            return False
        skill.usage_count += 1
        skill.state = "active"
        skill.updated_at = time.time()
        self._save_usage()
        return True

    def archive(self, skill_id: str) -> bool:
        skill = self._skills.get(skill_id)
        if not skill:
            return False
        skill.state = "archived"
        self._save_usage()
        return True

    def delete(self, skill_id: str) -> bool:
        return self._skills.pop(skill_id, None) is not None

    def statistics(self) -> dict:
        states = {}
        categories = {}
        for s in self._skills.values():
            states[s.state] = states.get(s.state, 0) + 1
            categories[s.category] = categories.get(s.category, 0) + 1
        return {
            "total": len(self._skills),
            "states": states,
            "categories": categories,
            "total_usage": sum(s.usage_count for s in self._skills.values()),
        }

    def _parse_skill_file(self, path: Path) -> Skill:
        content = path.read_text(encoding="utf-8")
        match = SKILL_FRONTMATTER_RE.match(content)
        body = content
        frontmatter: dict = {}
        if match:
            import yaml
            frontmatter = yaml.safe_load(match.group(1)) or {}
            body = match.group(2).strip()
        return Skill(
            id=frontmatter.get("id", path.parent.name),
            name=frontmatter.get("name", path.parent.name),
            description=frontmatter.get("description", ""),
            version=frontmatter.get("version", "1.0.0"),
            category=frontmatter.get("category", "general"),
            body=body,
            tags=frontmatter.get("tags", []),
            dependencies=frontmatter.get("dependencies", []),
            usage_count=self._usage.get(path.parent.name, {}).get("use_count", 0),
        )

    def _save_skill_file(self, skill: Skill) -> None:
        category_dir = self._skills_dir / skill.category
        skill_dir = category_dir / skill.id
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        frontmatter = {
            "id": skill.id, "name": skill.name,
            "description": skill.description, "version": skill.version,
            "category": skill.category, "tags": skill.tags,
        }
        import yaml
        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{skill.body}"
        skill_file.write_text(content, encoding="utf-8")

    def _load_usage(self) -> None:
        self._usage: dict = {}
        if self._usage_file.exists():
            try:
                self._usage = json.loads(self._usage_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self._usage = {}

    def _save_usage(self) -> None:
        usage = {}
        for skill in self._skills.values():
            usage[skill.id] = {
                "use_count": skill.usage_count,
                "state": skill.state,
                "last_activity_at": skill.updated_at,
            }
        self._usage_file.write_text(json.dumps(usage, indent=2), encoding="utf-8")
