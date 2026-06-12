"""API des workflows CIEL — DAG de steps, agents, situations."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

router = APIRouter(prefix="/v1/workflow", tags=["workflow"])


def get_engine(request: Request):
    brain = request.app.state.brain
    eng = brain.get_module("workflow") if brain else None
    if not eng:
        raise HTTPException(503, "workflow engine unavailable")
    return eng


@router.get("/status")
async def status(eng=Depends(get_engine)):
    return {"success": True, **eng.get_stats()}


@router.get("/list")
async def workflow_list(group: str | None = None, eng=Depends(get_engine)):
    return {"success": True, "workflows": [w.to_dict() for w in eng.list(group)]}


@router.get("/{wf_id}")
async def workflow_get(wf_id: str, eng=Depends(get_engine)):
    wf = eng.get(wf_id)
    if not wf:
        raise HTTPException(404, f"workflow '{wf_id}' not found")
    return {"success": True, "workflow": wf.to_dict()}


@router.post("/register")
async def workflow_register(data: dict, eng=Depends(get_engine)):
    from ciel.workflow.models import Workflow
    wf = Workflow.from_dict(data.get("workflow", data))
    eng.register(wf)
    eng.save()
    return {"success": True, "workflow": wf.to_dict()}


@router.delete("/{wf_id}")
async def workflow_delete(wf_id: str, eng=Depends(get_engine)):
    ok = eng.delete(wf_id)
    if not ok:
        raise HTTPException(404, f"workflow '{wf_id}' not found")
    eng.save()
    return {"success": True, "deleted": wf_id}


@router.post("/execute/{wf_id}")
async def workflow_execute(wf_id: str, data: dict | None = None,
                           eng=Depends(get_engine)):
    import asyncio
    wf = eng.get(wf_id)
    if not wf:
        raise HTTPException(404, f"workflow '{wf_id}' not found")
    loop = eng._event_loop or asyncio.get_event_loop()
    future = asyncio.run_coroutine_threadsafe(
        eng.execute(wf_id, triggered_by="api", initial_data=data or {}),
        loop,
    )
    ex = future.result(timeout=60)
    return {"success": True, "execution": ex.to_dict()}


@router.get("/executions/list")
async def execution_list(eng=Depends(get_engine)):
    return {"success": True, "executions": [e.to_dict() for e in eng._executions.values()]}
