from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GeneratedSkill:
    name: str
    description: str
    code: str
    category: str = "auto-generated"
    version: str = "1.0.0"
    author: str = "ciel-curator"
    created_at: float = field(default_factory=time.time)
    source_task: str = ""
    success: bool = False


class SkillGen:
    """Génération automatique de skills après tâches complexes.

    Analyse les trajectoires de tâches complexes et crée des skills
    réutilisables via ToolForge + LLM.

    Inspiré de Hermès Skill Self-Improvement.
    """

    def __init__(self, skills_dir: str | Path | None = None):
        self._skills_dir = Path(skills_dir or Path.home() / ".ciel" / "skills" / "auto")
        self._skills_dir.mkdir(parents=True, exist_ok=True)
        self._generated: list[GeneratedSkill] = []
        self._load()

    def _load(self) -> None:
        for f in self._skills_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                self._generated.append(GeneratedSkill(**data))
            except Exception:
                pass

    def _save_skill(self, skill: GeneratedSkill) -> Path:
        path = self._skills_dir / f"{skill.name}.json"
        path.write_text(json.dumps(vars(skill), indent=2, default=str))
        return path

    def analyze_trajectory(self, task: str, steps: list[dict[str, Any]],
                           result: str) -> GeneratedSkill | None:
        if not steps:
            return None

        name = self._generate_name(task)
        description = self._generate_description(task, steps)
        code = self._generate_code(name, steps)

        skill = GeneratedSkill(
            name=name,
            description=description,
            code=code,
            source_task=task,
            success=True,
        )

        self._generated.append(skill)
        self._save_skill(skill)
        logger.info(f"Generated skill '{name}' from task analysis")
        return skill

    def _generate_name(self, task: str) -> str:
        words = re.findall(r'\w+', task.lower())
        stop_words = {"the", "a", "an", "this", "that", "to", "for", "of", "in",
                      "on", "at", "by", "with", "from", "and", "or", "is", "are"}
        filtered = [w for w in words if w not in stop_words and len(w) > 2]
        if not filtered:
            return f"auto_skill_{uuid.uuid4().hex[:6]}"
        base = "_".join(filtered[:4])
        return f"auto_{base}"

    def _generate_description(self, task: str, steps: list[dict]) -> str:
        step_summaries = []
        for s in steps[:5]:
            action = s.get("action", s.get("tool", s.get("type", "unknown")))
            step_summaries.append(action)
        desc = f"Auto-generated from: {task[:100]}"
        if step_summaries:
            desc += f" | Steps: {', '.join(step_summaries)}"
        return desc

    def _generate_code(self, name: str, steps: list[dict]) -> str:
        code_lines = [
            f"def {name}(context: dict | None = None) -> dict:",
            f'    """Skill généré automatiquement."""',
            f"    result = {{}}",
            f"    steps = {json.dumps(steps, indent=2)}",
            f"    for step in steps:",
            f"        pass  # TODO: implémenter la logique",
            f"    return result",
        ]
        return "\n".join(code_lines)

    def list_generated(self) -> list[GeneratedSkill]:
        return list(self._generated)

    def get(self, name: str) -> GeneratedSkill | None:
        for s in self._generated:
            if s.name == name:
                return s
        return None

    def stats(self) -> dict[str, Any]:
        return {
            "total_generated": len(self._generated),
            "skills_dir": str(self._skills_dir),
        }
