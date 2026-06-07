from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class SkillMetadata:
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    channels: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    path: str = ""

    @classmethod
    def from_skill_md(cls, path: Path) -> SkillMetadata | None:
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
        name = path.parent.name
        description = ""
        tags: list[str] = []
        channels: list[str] = []
        deps: list[str] = []
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("# ") and i == 0:
                name = line[2:].strip()
                continue
            m = re.match(r"^>\s*(.+)$", line)
            if m and not description:
                description = m.group(1).strip()
                continue
            if "channel" in line.lower() and ":" in line:
                ch = line.split(":", 1)[1].strip()
                channels = [c.strip() for c in ch.split(",")]
            if "tag" in line.lower() and ":" in line:
                tg = line.split(":", 1)[1].strip()
                tags = [t.strip() for t in tg.split(",")]
            if re.match(r"^```", line):
                break
        return cls(
            name=name,
            description=description,
            path=str(path.parent),
            channels=tuple(channels),
            tags=tuple(tags),
            dependencies=tuple(deps),
        )


class SkillRegistry:
    """Registry for OpenClaw-style skills (SKILL.md discovery).

    Inspiré de openclaw-main/skills/ — découvre et charge les compétences
    via leur fichier SKILL.md.
    """

    def __init__(self, skills_dirs: list[str | Path] | None = None) -> None:
        self._skills: dict[str, SkillMetadata] = {}
        self._handlers: dict[str, Callable] = {}
        self._directories: list[Path] = [Path(d) for d in (skills_dirs or [])]

    def add_directory(self, path: str | Path) -> None:
        self._directories.append(Path(path))

    def discover(self) -> dict[str, SkillMetadata]:
        self._skills = {}
        for d in self._directories:
            if not d.exists():
                continue
            for skill_dir in d.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    meta = SkillMetadata.from_skill_md(skill_md)
                    if meta:
                        self._skills[meta.name] = meta
        logger.info(f"Discovered {len(self._skills)} skills from {len(self._directories)} dirs")
        return self._skills

    def get(self, name: str) -> SkillMetadata | None:
        return self._skills.get(name)

    def list(self, channel: str = "", tag: str = "") -> list[SkillMetadata]:
        results = list(self._skills.values())
        if channel:
            results = [s for s in results if channel in s.channels]
        if tag:
            results = [s for s in results if tag in s.tags]
        return results

    def register_handler(self, skill_name: str, handler: Callable) -> None:
        self._handlers[skill_name] = handler

    async def invoke(self, skill_name: str, **kwargs: Any) -> Any:
        handler = self._handlers.get(skill_name)
        if handler is None:
            raise KeyError(f"No handler registered for skill: {skill_name}")
        import asyncio
        if asyncio.iscoroutinefunction(handler):
            return await handler(**kwargs)
        return handler(**kwargs)

    def load_skills_from_openclaw(self, openclaw_skills_root: str | Path) -> int:
        """Load skills from OpenClaw's skills/ directory structure."""
        root = Path(openclaw_skills_root)
        if not root.exists():
            logger.warning(f"OpenClaw skills root not found: {root}")
            return 0
        count = 0
        for skill_dir in root.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                meta = SkillMetadata.from_skill_md(skill_md)
                if meta:
                    self._skills[meta.name] = meta
                    count += 1
        logger.info(f"Loaded {count} skills from {root}")
        return count
