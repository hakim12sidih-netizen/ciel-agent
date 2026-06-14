"""Routes API pour la gestion unifiée des LLM — hot-swap sans fil."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import StreamingResponse
from typing import Any

from ciel.llmbridge.core import LLMBridgeEngine
from ciel.providers import get_registry
from ciel.providers.models import get_model_info, list_models

router = APIRouter(tags=["llm"])


def get_engine(request: Request) -> LLMBridgeEngine:
    brain = request.app.state.brain
    if not brain:
        raise HTTPException(503, "CIEL brain not initialized")
    engine = brain._modules.get("llmbridge")
    if not engine:
        raise HTTPException(503, "LLMBridge not initialized")
    return engine


# ── Modèles ──

class SetProviderRequest(BaseModel):
    provider: str
    model: str = ""


class SetModelRequest(BaseModel):
    model: str


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 4096
    session_id: str = ""
    provider: str = ""
    model: str = ""
    stream: bool = False


# ── Endpoints ──

@router.get("/llm/providers")
async def list_providers(request: Request):
    """Liste tous les providers disponibles."""
    registry = get_registry()
    return {
        "providers": [p.to_dict() for p in registry.list()],
        "available": [p.to_dict() for p in registry.list(available_only=True)],
    }


@router.get("/llm/models")
async def list_models_endpoint(provider: str = "", local_only: bool = False):
    """Liste les modèles disponibles."""
    models = list_models(provider=provider, local_only=local_only)
    return {
        "models": [
            {"name": m.name, "provider": m.provider,
             "context_window": m.context_window, "max_output": m.max_output,
             "capabilities": m.capabilities, "is_local": m.is_local}
            for m in models
        ]
    }


@router.get("/llm/active")
async def get_active(request: Request):
    """Provider et modèle actifs."""
    engine = get_engine(request)
    return engine.active_info()


@router.post("/llm/provider")
async def set_provider(req: SetProviderRequest, request: Request):
    """Change de provider/modèle (hot-swap sans fil)."""
    engine = get_engine(request)
    result = engine.set_active_provider(req.provider, req.model)
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "Erreur inconnue"))
    return result


@router.post("/llm/model")
async def switch_model(req: SetModelRequest, request: Request):
    """Change de modèle sur le provider actif."""
    engine = get_engine(request)
    result = engine.switch_model(req.model)
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "Erreur inconnue"))
    return result


@router.post("/llm/chat")
async def chat(req: ChatRequest, request: Request):
    """Envoie un message au LLM actif (streaming SSE si stream=True)."""
    engine = get_engine(request)
    try:
        if req.provider:
            engine.set_active_provider(req.provider, req.model)

        if req.stream:
            async def _stream():
                full_content = ""
                async for chunk in engine.chat_stream(req.messages, req.temperature, req.max_tokens):
                    if chunk:
                        full_content += chunk
                        yield f"data: {json.dumps({'token': chunk})}\n\n"
                yield f"data: {json.dumps({'done': True, 'full_content': full_content})}\n\n"

            return StreamingResponse(
                _stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        resp = await engine.chat(req.messages, req.temperature, req.max_tokens)
        if req.session_id:
            engine.send_message(req.session_id, req.messages[-1]["content"], "user")
            engine.send_message(req.session_id, resp.content, "assistant")
        return {
            "content": resp.content,
            "model": resp.model,
            "provider": resp.provider,
            "usage": resp.usage,
        }
    except Exception as e:
        raise HTTPException(502, f"Erreur LLM: {e}")
