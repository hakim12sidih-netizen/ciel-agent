"""
CIEL v∞.8 — API REST FastAPI.
Serveur HTTP exposant l'écosystème CIEL complet.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from ciel.api.middleware import AuthMiddleware, EthicsMiddleware
from ciel.api.models import ServerConfig
from ciel.api.routes import register_routes


def create_app(brain=None, config: ServerConfig | None = None) -> FastAPI:
    cfg = config or ServerConfig()
    auth = AuthMiddleware(cfg.api_keys)
    _brain_holder: list[CIELBrain] = []

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from ciel.brain.core import CIELBrain
        from ciel.providers import get_registry
        log = logging.getLogger("ciel.api")
        log.setLevel(cfg.log_level)

        # Injecter les clés API LLM de la config dans l'environnement
        _llm_cfg: dict = {}
        try:
            import json as _json
            from pathlib import Path as _Path
            _cfg_file = _Path.home() / ".ciel" / "ciel.json"
            if _cfg_file.exists():
                _cfg_data = _json.loads(_cfg_file.read_text())
                _llm_cfg = _cfg_data.get("llm", {})
                _api_keys = _llm_cfg.get("api_keys", {})
                _registry = get_registry()
                _registry.configure(api_keys=_api_keys)
                for _name, _key in _api_keys.items():
                    if _key:
                        _profile = _registry.get(_name)
                        if _profile and _profile.env_var:
                            os.environ.setdefault(_profile.env_var, _key)
                            log.info("  LLM %s: clé config injectée dans %s", _name, _profile.env_var)
        except Exception as _e:
            log.warning("  LLM config injection: %s", _e)

        b = brain or CIELBrain()
        if not brain:
            log.info("Initializing CIEL brain...")
            b.load_all_modules()
        b.start()

        # Configurer le provider LLM par défaut depuis la config
        if _llm_cfg:
            engine = b.get_module("llmbridge")
            if engine:
                _dp = _llm_cfg.get("default_provider", "ollama")
                _dm = _llm_cfg.get("default_model", "phi3")
                engine.set_active_provider(_dp, _dm)
                log.info("  LLM actif: %s / %s", _dp, _dm)

        app.state.brain = b
        app.state.auth = auth
        app.state.ethics = EthicsMiddleware(b)
        # Démarrer le moteur de workflows
        wf = b.get_module("workflow")
        if wf:
            wf._app = app
            wf.start()
        _brain_holder.append(b)
        log.info(f"CIEL API v∞.8 ready on {cfg.host}:{cfg.port}")
        yield
        wf = b.get_module("workflow")
        if wf:
            await wf.stop()
        b.stop()
        log.info("CIEL API shutdown complete")

    app = FastAPI(
        title="CIEL API",
        version="v∞.8",
        description="API REST de l\'ecosysteme cognitif CIEL",
        lifespan=lifespan,
        docs_url="/v1/docs",
        openapi_url="/v1/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class AuthCheckMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            public_paths = {
                "/v1/health", "/v1/docs", "/v1/openapi.json",
                "/v1/auth/token", "/favicon.ico",
                "/", "/webui", "/install", "/static/",
            }
            path = request.url.path
            if request.headers.get("X-CIEL-Internal") == "workflow-engine":
                return await call_next(request)
            if any(path.startswith(p) for p in ("/v1/install/", "/v1/messaging/", "/v1/persist/", "/static/")):
                return await call_next(request)
            if request.url.path in public_paths or request.url.path.startswith("/v1/auth/"):
                return await call_next(request)
            if auth._api_keys:
                token = request.headers.get("Authorization", "").replace("Bearer ", "")
                if not auth.check_token(token):
                    from fastapi.responses import JSONResponse
                    return JSONResponse(status_code=401,
                                        content={"success": False, "error": "Unauthorized"})
            resp = await call_next(request)
            resp.headers["X-CIEL-Version"] = "v8"
            return resp

    app.add_middleware(AuthCheckMiddleware)
    register_routes(app)
    return app


def run_server(brain: CIELBrain | None = None,
               host: str = "0.0.0.0",
               port: int = 8765,
               api_keys: list[str] | None = None,
               log_level: str = "INFO"):
    if not api_keys:
        try:
            import json
            from pathlib import Path
            cfg_file = Path.home() / ".ciel" / "ciel.json"
            if cfg_file.exists():
                cfg_data = json.loads(cfg_file.read_text())
                api_keys = cfg_data.get("security", {}).get("api_keys", [])
        except Exception:
            pass
    cfg = ServerConfig(host=host, port=port,
                       api_keys=api_keys or [],
                       log_level=log_level)
    app = create_app(brain, cfg)
    uvicorn.run(
        app,
        host=cfg.host,
        port=cfg.port,
        log_level=cfg.log_level.lower(),
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CIEL API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Adresse d'écoute")
    parser.add_argument("--port", "-p", type=int, default=8765, help="Port d'écoute")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Niveau de log")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port, log_level=args.log_level)
