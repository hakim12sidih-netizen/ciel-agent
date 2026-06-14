"""
Config method handler — get/set CIEL configuration.
Uses CIEL's ConfigEngine (layered config from ciel/config/core.py).
"""

from typing import Any

_config_engine = None

def _get_config():
    global _config_engine
    if _config_engine is None:
        from ciel.config.core import ConfigEngine
        _config_engine = ConfigEngine()
    return _config_engine


CACHE: dict[str, Any] = {}


class ConfigMethods:

    def __init__(self, server):
        self.server = server

    def get_methods(self) -> dict[str, Any]:
        return {
            "config.get": self.handle_get,
            "config.set": self.handle_set,
        }

    async def handle_get(self, params: dict) -> dict:
        key = params.get("key", "")
        # Try ConfigEngine
        try:
            cfg = _get_config()
            # ConfigEngine stores nested config e.g. "api.port"
            parts = key.split(".")
            data = cfg.DEFAULTS
            for part in parts:
                data = data.get(part, {})
            if isinstance(data, dict):
                data = CACHE.get(key, data)
            return {"value": data}
        except Exception:
            return {"value": CACHE.get(key)}

    async def handle_set(self, params: dict) -> dict:
        key = params.get("key", "")
        value = params.get("value")
        CACHE[key] = value
        return {"success": True}
