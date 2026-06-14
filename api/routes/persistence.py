"""
CIEL v∞.8 — Routes de persistance (auto-start, état, historique)
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ciel.persistence import (
    get_status,
    install_autostart,
    remove_autostart,
    clear_state,
    save_state,
)

router = APIRouter(prefix="/v1/persist")


class AutostartRequest(BaseModel):
    enable: bool
    port: int = 8765
    host: str = "0.0.0.0"


@router.get("/status")
async def persist_status():
    """État de la persistance."""
    return await get_status()


@router.post("/autostart")
async def set_autostart(req: AutostartRequest):
    """Active/désactive le redémarrage automatique au boot."""
    if req.enable:
        ok = install_autostart(req.port, req.host)
    else:
        ok = remove_autostart()
    return {"success": ok, "enabled": req.enable}


@router.post("/save")
async def save_state_endpoint():
    """Sauvegarde forcée de l'état."""
    st = await save_state()
    return {"success": True, "saved_at": st.get("saved_at")}


@router.post("/clear")
async def clear_state_endpoint():
    """Efface l'état sauvegardé."""
    await clear_state()
    return {"success": True}
