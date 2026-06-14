"""
CIEL v∞.8 — CONFIG ENGINE. Layered configuration management.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ciel.evolution.leader_network import LeaderNetwork


class ConfigError(Exception):
    pass


@dataclass
class ConfigLayer:
    name: str
    priority: int = 0  # higher = overrides lower
    data: dict[str, Any] = field(default_factory=dict)


class ConfigEngine:
    """Gestionnaire de configuration à couches.

    Ordre de priorité (du plus bas au plus haut):
      1. defaults   (intégrés)
      2. file       (ciel.json / ciel.yaml)
      3. env        (variables CIEL_*)
      4. cli        (arguments en ligne de commande)
    """

    DEFAULTS: dict[str, Any] = {
        "api": {"host": "0.0.0.0", "port": 8765, "log_level": "INFO",
                "max_request_size": 10_485_760},
        "brain": {"tick_interval": 1.0, "max_modules": 128},
        "database": {"path": "~/.ciel/ciel.db", "auto_migrate": True},
        "cache": {"default_ttl": 300, "backend": "memory", "max_size": 1000},
        "security": {"api_keys": [], "jwt_secret": "",
                     "rate_limit": 100},
        "vision": {"screenshot_dir": "~/.ciel/screenshots",
                   "webcam_index": 0},
        "control": {"live_mode": False, "safe_bounds": True},
        "sandbox": {"docker_image": "python:3.12-slim",
                    "default_timeout": 30, "allowed_languages":
                        ["python", "js", "go", "rust"]},
        "websearch": {"cache_ttl": 300, "max_results": 10},
        "clones": {"max_clones": 50, "default_ttl": 3600},
        "toolforge": {"max_tools": 200, "sandboxed": True},
        "llm": {"default_provider": "ollama", "default_model": "phi3",
                "temperature": 0.7, "max_tokens": 4096,
                "auto_switch": True, "fallback_provider": "ollama",
                "fallback_model": "phi3",
                "api_keys": {}},  # ex: {"openai": "sk-...", "anthropic": "sk-ant-..."}
        "channels": {"telegram_token": "", "telegram_enabled": False,
                     "discord_token": "", "discord_enabled": False,
                     "slack_token": "", "slack_enabled": False},
        "workflow": {"enabled": True, "loop_interval": 1.0,
                     "config_path": "~/.ciel/workflows.json"},
        "plugins": {"enabled": True, "dirs": ["~/.ciel/plugins"],
                     "auto_discover": True, "sandbox": True,
                     "auto_approve_permissions": False,
                     "max_plugins": 50},
    }

    def __init__(self, config_path: str | None = None):
        self._layers: list[ConfigLayer] = []
        self._config_path = config_path or os.environ.get(
            "CIEL_CONFIG", str(Path.home() / ".ciel" / "ciel.json"))
        self._env_prefix = "CIEL_"
        self.network = LeaderNetwork()

    def build(self, cli_overrides: dict[str, Any] | None = None) -> dict:
        """Construit la configuration finale en fusionnant les couches."""
        self._layers.clear()

        # 1. Defaults (deep copy to avoid mutation)
        import copy
        self._layers.append(ConfigLayer("defaults", priority=0,
                                         data=copy.deepcopy(self.DEFAULTS)))

        # 2. File (ciel.json / ciel.yaml)
        file_data = self._load_file()
        if file_data:
            self._layers.append(ConfigLayer("file", priority=10,
                                             data=file_data))

        # 3. Environment variables
        env_data = self._load_env()
        if env_data:
            self._layers.append(ConfigLayer("env", priority=20,
                                             data=env_data))

        # 4. CLI overrides
        if cli_overrides:
            self._layers.append(ConfigLayer("cli", priority=30,
                                             data=cli_overrides))

        # Fusion
        merged: dict[str, Any] = {}
        for layer in sorted(self._layers, key=lambda l: l.priority):
            merged = self._deep_merge(merged, layer.data)

        return merged

    def _load_file(self) -> dict:
        path = Path(self._config_path).expanduser()
        if not path.exists():
            return {}
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix in (".json",):
                return json.loads(text)
            elif path.suffix in (".yaml", ".yml"):
                import yaml
                return yaml.safe_load(text) or {}
        except Exception:
            return {}

    def _load_env(self) -> dict:
        """Charge les variables d'environnement CIEL_* en structure hiérarchique."""
        result: dict[str, Any] = {}
        for key, val in os.environ.items():
            if not key.startswith(self._env_prefix):
                continue
            parts = key[len(self._env_prefix):].lower().split("__")
            target = result
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = self._parse_val(val)
        return result

    @staticmethod
    def _parse_val(val: str) -> Any:
        val = val.strip()
        if val.lower() in ("true", "yes", "1"):
            return True
        if val.lower() in ("false", "no", "0"):
            return False
        if val.lower() == "null":
            return None
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        if val.startswith("[") and val.endswith("]"):
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass
        return val

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        result = dict(base)
        for key, val in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(val, dict):
                result[key] = ConfigEngine._deep_merge(result[key], val)
            else:
                result[key] = val
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur par chemin 'section.nested.key'."""
        config = self.build()
        parts = key.split(".")
        target = config
        for part in parts:
            if isinstance(target, dict):
                target = target.get(part)
            else:
                return default
        return target if target is not None else default

    def set(self, key: str, value: Any) -> dict:
        """Définit une valeur et la sauvegarde dans le fichier de config."""
        config = self.build()
        parts = key.split(".")
        target = config
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value
        self._save_file(config)
        return {"status": "ok", "key": key, "value": value}

    def _save_file(self, config: dict):
        path = Path(self._config_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    def reset(self) -> dict:
        self._layers.clear()
        return {"status": "ok"}

    def get_stats(self) -> dict:
        config = self.build()
        return {
            "layers": [l.name for l in self._layers],
            "keys": list(config.keys()),
            "config_path": self._config_path,
        }

    def process(self, input_data: dict) -> dict:
        action = input_data.get("action", "stats")
        if action == "build":
            return {"status": "ok", "config": self.build(
                input_data.get("cli_overrides"))}
        elif action == "get":
            val = self.get(input_data.get("key", ""),
                           input_data.get("default"))
            return {"status": "ok", "key": input_data.get("key"),
                    "value": val}
        elif action == "set":
            return self.set(input_data.get("key", ""),
                            input_data.get("value"))
        elif action == "reset":
            return self.reset()
        return self.get_stats()
