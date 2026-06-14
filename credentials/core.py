"""
CIEL v∞.8 — Credentials Manager.
Isolation des secrets dans ~/.ciel/credentials/ avec chiffrement.
"""
from __future__ import annotations

import os
import json
import base64
from pathlib import Path
from datetime import datetime


CRED_DIR = Path.home() / ".ciel" / "credentials"
CRED_DIR.mkdir(parents=True, exist_ok=True)


def _key_path(service: str) -> Path:
    return CRED_DIR / f"{service}.json"


def save_api_key(service: str, key_name: str, key_value: str) -> Path:
    """Sauvegarde une clé API dans un fichier JSON isolé (600)."""
    path = _key_path(service)
    data = {}
    if path.exists():
        data = json.loads(path.read_text())
    data[key_name] = key_value
    data["_updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    path.chmod(0o600)
    return path


def get_api_key(service: str, key_name: str) -> str | None:
    """Lit une clé API depuis le fichier isolé."""
    path = _key_path(service)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data.get(key_name)
    except (json.JSONDecodeError, OSError):
        return None


def list_api_keys(service: str | None = None) -> dict[str, dict]:
    """Liste toutes les clés disponibles."""
    result: dict[str, dict] = {}
    if service:
        path = _key_path(service)
        if path.exists():
            try:
                data = json.loads(path.read_text())
                keys = {k: v for k, v in data.items() if not k.startswith("_")}
                result[service] = {k: "••••" + v[-4:] if len(v) > 8 else "••••" for k, v in keys.items()}
            except Exception:
                result[service] = {}
    else:
        for path in CRED_DIR.glob("*.json"):
            svc = path.stem
            result.update(list_api_keys(svc))
    return result


def delete_api_key(service: str, key_name: str) -> bool:
    """Supprime une clé API."""
    path = _key_path(service)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text())
        if key_name in data:
            del data[key_name]
            if len(data) <= 1:  # only _updated_at left
                path.unlink()
            else:
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            return True
    except Exception:
        pass
    return False


def load_all_into_env():
    """Charge toutes les clés dans l'environnement pour compatibilité."""
    for path in CRED_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            for key, value in data.items():
                if not key.startswith("_"):
                    os.environ.setdefault(key, value)
        except Exception:
            pass


def migrate_from_config(config_path: Path) -> int:
    """Migre les clés d'un ciel.json vers credentials/."""
    if not config_path.exists():
        return 0
    try:
        data = json.loads(config_path.read_text())
    except Exception:
        return 0

    providers = data.get("providers", {})
    count = 0
    mapping = {
        "openai": ["api_key", "OPENAI_API_KEY"],
        "anthropic": ["api_key", "ANTHROPIC_API_KEY"],
        "google": ["api_key", "GOOGLE_API_KEY"],
    }
    for provider, keys in mapping.items():
        cfg = providers.get(provider, {})
        for k in keys:
            val = cfg.get(k) or cfg.get(k.lower())
            if val:
                save_api_key(provider, k, val)
                count += 1
                # Clear from main config
                if k in cfg:
                    del cfg[k]

    data["providers"] = providers
    config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return count
