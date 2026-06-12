"""Middleware CIEL — authentification et filtre éthique."""
from __future__ import annotations

import hashlib
import hmac
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse


class AuthMiddleware:
    """Authentification par API key + JWT-like tokens."""

    def __init__(self, api_keys: list[str] | None = None):
        self._api_keys = set(api_keys or [])
        self._tokens: dict[str, float] = {}

    def validate_api_key(self, key: str) -> bool:
        return key in self._api_keys

    def issue_token(self, api_key: str) -> str | None:
        if api_key not in self._api_keys:
            return None
        raw = f"{api_key}:{time.time()}:ciel-api"
        token = hashlib.sha256(raw.encode()).hexdigest()
        self._tokens[token] = time.time() + 3600
        return token

    def check_token(self, token: str) -> bool:
        if token in self._tokens:
            if time.time() < self._tokens[token]:
                return True
            del self._tokens[token]
        return False


class EthicsMiddleware:
    """Filtre éthique sur chaque mutation — délègue à EthicsEngine."""

    def __init__(self, brain: Any | None = None):
        self._brain = brain

    async def check(self, action: str, context: dict) -> dict:
        if not self._brain:
            return {"allowed": True}
        engine = self._brain.get_module("ethics")
        if not engine:
            return {"allowed": True}
        try:
            result = engine.process({
                "action": "check",
                "action_type": action,
                "context": context,
            })
            if isinstance(result, dict):
                return result
        except Exception:
            pass
        return {"allowed": True}


def setup_middleware(app: FastAPI, brain: Any,
                     api_keys: list[str] | None = None) -> tuple[AuthMiddleware, EthicsMiddleware]:
    auth = AuthMiddleware(api_keys or [])
    ethics = EthicsMiddleware(brain)

    @app.middleware("http")
    async def ciel_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time.time()
        path = request.url.path

        # Routes publiques
        public_paths = {
            "/v1/health", "/v1/docs", "/v1/openapi.json",
            "/v1/auth/token", "/favicon.ico",
        }
        if path in public_paths or path.startswith("/v1/auth/"):
            return await call_next(request)

        # Auth
        if auth._api_keys:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not auth.check_token(token):
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "error": "Unauthorized"},
                )

        resp = await call_next(request)

        # Audit header
        elapsed = (time.time() - start) * 1000
        resp.headers["X-CIEL-Processing-Time"] = f"{elapsed:.1f}ms"
        resp.headers["X-CIEL-Version"] = "v∞.8"

        return resp

    return auth, ethics
