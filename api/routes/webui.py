"""
CIEL v∞.8 — Web IDE & Web UI routes.
Sert les interfaces web (IDE, install wizard) connectées au cerveau CIEL.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()

_HERE = Path(__file__).resolve().parent.parent.parent
_WEB_DIR = _HERE / "web"


def _read_html(name: str) -> str:
    path = _WEB_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"<html><body><h1>404</h1><p>{name} not found</p></body></html>"


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def webui_index() -> HTMLResponse:
    return HTMLResponse(_read_html("ide.html"))


@router.get("/webui", response_class=HTMLResponse, include_in_schema=False)
async def webui_page() -> HTMLResponse:
    return HTMLResponse(_read_html("ide.html"))


@router.get("/install", response_class=HTMLResponse, include_in_schema=False)
async def install_wizard() -> HTMLResponse:
    return HTMLResponse(_read_html("install_wizard.html"))


@router.get("/static/{filepath:path}", include_in_schema=False)
async def static_files(filepath: str):
    path = _WEB_DIR / filepath
    if path.exists() and path.is_file():
        return FileResponse(str(path))
    return HTMLResponse(status_code=404)
