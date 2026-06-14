"""Routes pour le marché cognitif interne."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from ciel.api.models import EconomyStatusResponse, TradeRequest

router = APIRouter(tags=["economy"])


def get_economy(request: Request):
    brain = request.app.state.brain
    eco = brain.get_module("economy") if brain else None
    if not eco:
        raise HTTPException(503, "economy engine unavailable")
    return eco


@router.get("/economy/status", response_model=EconomyStatusResponse)
async def economy_status(eco=Depends(get_economy)):
    if hasattr(eco, "get_stats"):
        stats = eco.get_stats()
        return EconomyStatusResponse(
            agents=stats.get("agents", 0),
            gdp=stats.get("gdp", 0.0),
            money_supply=stats.get("money_supply", 0.0),
            inflation=stats.get("inflation", 0.0),
            transactions=stats.get("transactions", 0),
        )
    return EconomyStatusResponse()


@router.get("/economy/wealth")
async def wealth_distribution(eco=Depends(get_economy)):
    result = eco.process({"action": "wealth"})
    return {"success": True, "wealth": result.get("wealth", result)}


@router.get("/economy/prices")
async def market_prices(eco=Depends(get_economy)):
    result = eco.process({"action": "prices"})
    return {"success": True, "prices": result.get("prices", result)}


@router.post("/economy/trade")
async def trade(req: TradeRequest, eco=Depends(get_economy)):
    result = eco.process({
        "action": "trade",
        "seller": req.seller,
        "buyer": req.buyer,
        "market": req.market,
        "item": req.item,
        "price": req.price,
    })
    return {"success": True, "trade": result}


@router.post("/economy/register")
async def register_agent(agent_id: str, balance: float = 1000.0,
                         eco=Depends(get_economy)):
    result = eco.process({
        "action": "register",
        "agent": agent_id,
        "balance": balance,
    })
    return {"success": True, "result": result}


@router.post("/economy/regulate")
async def regulate(economy=Depends(get_economy)):
    result = economy.process({"action": "regulate"})
    return {"success": True, "regulation": result}
