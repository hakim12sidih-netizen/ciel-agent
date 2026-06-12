"""Routes principales : santé, moteurs, traitement universel."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from ciel.api.models import (
    EthicsCheckRequest,
    EthicsCheckResponse,
    HealthResponse,
    MemoryQueryRequest,
    MemoryStoreRequest,
    ProcessRequest,
    ProcessResponse,
    TokenRequest,
    TokenResponse,
)

router = APIRouter(tags=["core"])


def get_brain(request: Request):
    brain = request.app.state.brain
    if not brain:
        raise HTTPException(503, "CIEL brain not initialized")
    return brain


def get_auth(request: Request):
    return request.app.state.auth


@router.get("/health", response_model=HealthResponse)
async def health(brain=Depends(get_brain)):
    status = brain.status_report()
    return HealthResponse(
        uptime=status.get("uptime", 0.0),
        modules_active=len(status.get("modules", [])),
        cycles=status.get("cycles", 0),
    )


@router.get("/engines")
async def list_engines(brain=Depends(get_brain)):
    status = brain.status_report()
    return {"success": True, "engines": status.get("modules", [])}


@router.post("/process", response_model=ProcessResponse)
async def process(req: ProcessRequest, brain=Depends(get_brain)):
    try:
        payload = {"action": req.action, **req.data}
        result = brain.process(payload)
        return ProcessResponse(result=result)
    except Exception as e:
        return ProcessResponse(success=False, error=str(e))


@router.get("/engine/{engine_name}/status")
async def engine_status(engine_name: str, brain=Depends(get_brain)):
    mod = brain.get_module(engine_name)
    if not mod:
        raise HTTPException(404, f"Engine '{engine_name}' not found")
    if hasattr(mod, "get_stats"):
        return {"success": True, "stats": mod.get_stats()}
    return {"success": True, "message": f"{engine_name} loaded"}


@router.post("/engine/{engine_name}/process")
async def engine_process(engine_name: str, req: ProcessRequest,
                         brain=Depends(get_brain)):
    mod = brain.get_module(engine_name)
    if not mod:
        raise HTTPException(404, f"Engine '{engine_name}' not found")
    if not hasattr(mod, "process"):
        raise HTTPException(400, f"Engine '{engine_name}' has no process()")
    try:
        payload = {"action": req.action, **req.data}
        result = mod.process(payload)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/auth/token", response_model=TokenResponse)
async def get_token(req: TokenRequest, request: Request):
    auth = request.app.state.auth
    token = auth.issue_token(req.api_key)
    if not token:
        raise HTTPException(401, "Invalid API key")
    return TokenResponse(token=token, expires_at=auth._tokens[token],
                         scope="full")


@router.post("/ethics/check", response_model=EthicsCheckResponse)
async def ethics_check(req: EthicsCheckRequest, brain=Depends(get_brain)):
    engine = brain.get_module("ethics")
    if not engine:
        return EthicsCheckResponse(allowed=True, reason="no ethics engine")
    try:
        result = engine.process({
            "action": "check",
            "action_type": req.action,
            "context": req.context,
        })
        return EthicsCheckResponse(
            allowed=result.get("allowed", True),
            reason=result.get("reason", ""),
            layer=result.get("layer", ""),
            risk_score=result.get("risk_score", 0.0),
        )
    except Exception as e:
        return EthicsCheckResponse(allowed=False, reason=str(e))


@router.post("/memory/store")
async def memory_store(req: MemoryStoreRequest, brain=Depends(get_brain)):
    engine = brain.get_module("memory")
    if not engine:
        raise HTTPException(503, "memory engine unavailable")
    result = engine.process({
        "action": "store",
        "content": req.content,
        "memory_type": req.memory_type,
        "tags": req.tags,
    })
    return {"success": True, "result": result}


@router.post("/memory/query")
async def memory_query(req: MemoryQueryRequest, brain=Depends(get_brain)):
    engine = brain.get_module("memory")
    if not engine:
        raise HTTPException(503, "memory engine unavailable")
    result = engine.process({
        "action": "query",
        "query": req.query,
        "limit": req.limit,
    })
    return {"success": True, "result": result}


@router.get("/brain/status")
async def brain_status(brain=Depends(get_brain)):
    return {"success": True, "status": brain.status_report()}
