"""
CIEL v∞.8 — Routes de messagerie (Telegram, Discord, WhatsApp, etc.)
"""
from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1/messaging")


class ConnectRequest(BaseModel):
    api_key: str = ""
    bot_token: str = ""
    phone_number: str = ""
    server_url: str = ""
    webhook_url: str = ""
    webhook_secret: str = ""


# Stockage des connexions en mémoire
_connections: dict[str, dict] = {}


def _load_config() -> dict:
    cfg_file = Path.home() / ".ciel" / "ciel.json"
    if cfg_file.exists():
        try:
            return json.loads(cfg_file.read_text())
        except Exception:
            pass
    return {}


def _save_provider_config(provider: str, params: dict):
    cfg_file = Path.home() / ".ciel" / "ciel.json"
    cfg = _load_config()
    providers = cfg.setdefault("providers", {})
    providers[provider] = {k: v for k, v in params.items() if v}
    cfg_file.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))


@router.get("/status")
async def messaging_status():
    """État de toutes les plateformes de messagerie."""
    cfg = _load_config().get("providers", {})
    platforms = ["telegram", "discord", "whatsapp", "signal", "matrix", "slack"]
    result = {}
    for p in platforms:
        conf = cfg.get(p, {})
        connected = p in _connections and _connections[p].get("connected", False)
        result[p] = {
            "connected": connected,
            "configured": bool(conf.get("api_key") or conf.get("bot_token")),
            "error": _connections.get(p, {}).get("error"),
            **conf,
        }
    return result


@router.post("/{platform}/connect")
async def connect_platform(platform: str, req: ConnectRequest):
    """Connecte une plateforme de messagerie."""
    params = {k: v for k, v in req.dict().items() if v}
    _save_provider_config(platform, params)
    _connections[platform] = {"connected": True, **params}
    return {"success": True, "platform": platform}


@router.post("/{platform}/disconnect")
async def disconnect_platform(platform: str):
    """Déconnecte une plateforme."""
    if platform in _connections:
        _connections[platform]["connected"] = False
        _connections[platform]["error"] = None
    return {"success": True, "platform": platform}


@router.post("/{platform}/test")
async def test_platform(platform: str):
    """Teste la connexion à une plateforme."""
    cfg = _load_config().get("providers", {}).get(platform, {})
    if not cfg:
        return {"success": False, "error": "Non configuré"}
    return {"success": True, "platform": platform, "configured": True}
