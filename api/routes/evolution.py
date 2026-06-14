"""Routes pour le moteur d'évolution."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from ciel.api.models import EvolveRequest, EvolveResponse

router = APIRouter(tags=["evolution"])


def get_evolution(request: Request):
    brain = request.app.state.brain
    evo = brain.get_module("evolution") if brain else None
    if not evo:
        raise HTTPException(503, "evolution engine unavailable")
    return evo


@router.post("/evolution/evolve", response_model=EvolveResponse)
async def evolve(req: EvolveRequest, evo=Depends(get_evolution)):
    start = time.time()
    result = evo.process({
        "action": "step",
        "generations": req.generations,
        "elite_pct": req.elite_pct,
        "mut_rate": req.mut_rate,
    })
    elapsed = (time.time() - start) * 1000
    return EvolveResponse(
        generation=result.get("generation", 0),
        best_fitness=result.get("best_fitness", 0.0),
        population_size=result.get("population_size", 0),
        elapsed_ms=round(elapsed, 2),
    )


@router.get("/evolution/status")
async def evolution_status(evo=Depends(get_evolution)):
    if hasattr(evo, "get_stats"):
        return {"success": True, "stats": evo.get_stats()}
    return {"success": True, "message": "evolution engine running"}


@router.get("/evolution/population")
async def population(evo=Depends(get_evolution)):
    result = evo.process({"action": "population"})
    return {"success": True, "population": result}


@router.get("/evolution/best")
async def best_individual(evo=Depends(get_evolution)):
    result = evo.process({"action": "best"})
    return {"success": True, "best": result}


@router.post("/evolution/metamorphic/cycle")
async def metamorphic_cycle(request: Request, r: int = 1):
    brain = request.app.state.brain
    mc = brain.get_module("metamorphic_core") if brain else None
    if not mc:
        raise HTTPException(503, "metamorphic core unavailable")
    result = mc.status()
    return {"success": True, "result": result}


@router.post("/evolution/imperial/cycle")
async def imperial_cycle(request: Request, r: int = 1):
    brain = request.app.state.brain
    ic = brain.get_module("imperial_cycle") if brain else None
    if not ic:
        raise HTTPException(503, "imperial cycle unavailable")
    result = ic.run_generation(phase_mask=0xFF)
    return {"success": True, "result": result.to_dict()}
