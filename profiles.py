from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CIEL_HOME = Path(os.environ.get("CIEL_HOME", Path.home() / ".ciel"))


@dataclass
class Profile:
    name: str
    display_name: str = ""
    description: str = ""
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    is_default: bool = False
    provider: str = "openai"
    model: str = "gpt-4o"
    skin: str = "ciel-dark"
    theme: str = "ciel-dark"
    env_vars: dict[str, str] = field(default_factory=dict)

    @property
    def home(self) -> Path:
        return CIEL_HOME / "profiles" / self.name

    def init_home(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "config").mkdir(exist_ok=True)
        (self.home / "data").mkdir(exist_ok=True)
        (self.home / "skills").mkdir(exist_ok=True)
        (self.home / "memory").mkdir(exist_ok=True)
        (self.home / "keys").mkdir(exist_ok=True)

    def remove_home(self) -> None:
        if self.home.exists():
            shutil.rmtree(self.home)


class ProfileManager:
    def __init__(self, profiles_dir: str | Path | None = None):
        self._dir = Path(profiles_dir or CIEL_HOME / "profiles")
        self._dir.mkdir(parents=True, exist_ok=True)
        self._profiles: dict[str, Profile] = {}
        self._current: str = "default"
        self._load()

    def _load(self) -> None:
        for f in self._dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                profile = Profile(**data)
                self._profiles[profile.name] = profile
            except Exception:
                pass

        if not self._profiles:
            default = Profile(
                name="default", display_name="Default",
                description="Profil CIEL par défaut", is_default=True,
            )
            self._profiles["default"] = default
            self._save_profile(default)

        meta_path = self._dir / ".current"
        if meta_path.exists():
            self._current = meta_path.read_text().strip()
        if self._current not in self._profiles:
            self._current = "default"

    def _save_profile(self, profile: Profile) -> None:
        path = self._dir / f"{profile.name}.json"
        path.write_text(json.dumps(vars(profile), indent=2, default=str))

    def _save_current(self) -> None:
        meta_path = self._dir / ".current"
        meta_path.write_text(self._current)

    def create(self, name: str, display_name: str = "",
               description: str = "", provider: str = "openai",
               model: str = "gpt-4o", from_profile: str = "") -> Profile:
        if name in self._profiles:
            raise ValueError(f"Profile '{name}' already exists")
        if from_profile and from_profile in self._profiles:
            src = self._profiles[from_profile]
            profile = Profile(
                name=name, display_name=display_name or name,
                description=description or f"From {from_profile}",
                provider=src.provider, model=src.model,
                skin=src.skin, theme=src.theme,
                env_vars=dict(src.env_vars),
            )
        else:
            profile = Profile(
                name=name, display_name=display_name or name,
                description=description or "Profil CIEL",
                provider=provider, model=model,
            )
        profile.init_home()
        self._profiles[name] = profile
        self._save_profile(profile)
        return profile

    def get(self, name: str | None = None) -> Profile:
        return self._profiles.get(name or self._current, self._profiles["default"])

    def switch(self, name: str) -> bool:
        if name not in self._profiles:
            return False
        self._current = name
        profile = self._profiles[name]
        profile.last_used_at = time.time()
        self._save_profile(profile)
        self._save_current()
        os.environ["CIEL_PROFILE"] = name
        for k, v in profile.env_vars.items():
            os.environ[k] = v
        return True

    def delete(self, name: str) -> bool:
        if name == "default":
            return False
        profile = self._profiles.pop(name, None)
        if profile:
            path = self._dir / f"{name}.json"
            if path.exists():
                path.unlink()
            profile.remove_home()
            if self._current == name:
                self._current = "default"
                self._save_current()
            return True
        return False

    def list(self, include_default: bool = True) -> list[Profile]:
        results = list(self._profiles.values())
        if not include_default:
            results = [p for p in results if not p.is_default]
        return results

    def get_current_name(self) -> str:
        return self._current

    def update(self, name: str, **kwargs: Any) -> bool:
        profile = self._profiles.get(name)
        if not profile:
            return False
        for k, v in kwargs.items():
            if hasattr(profile, k) and k not in ("name", "created_at"):
                setattr(profile, k, v)
        profile.last_used_at = time.time()
        self._save_profile(profile)
        return True

    def stats(self) -> dict:
        return {
            "total": len(self._profiles),
            "current": self._current,
            "dir": str(self._dir),
        }
