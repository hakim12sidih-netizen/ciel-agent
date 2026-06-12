"""Route registration for CIEL API."""
from __future__ import annotations

from fastapi import FastAPI

from ciel.api.routes.core import router as core_router
from ciel.api.routes.evolution import router as evolution_router
from ciel.api.routes.cognition import router as cognition_router
from ciel.api.routes.economy import router as economy_router
from ciel.api.routes.capabilities import router as capabilities_router
from ciel.api.routes.install import router as install_router
from ciel.api.routes.messaging import router as messaging_router
from ciel.api.routes.persistence import router as persistence_router
from ciel.api.routes.webui import router as webui_router
from ciel.api.routes.llm import router as llm_router
from ciel.api.routes.workflow import router as workflow_router


def register_routes(app: FastAPI):
    app.include_router(core_router, prefix="/v1")
    app.include_router(evolution_router, prefix="/v1")
    app.include_router(cognition_router, prefix="/v1")
    app.include_router(economy_router, prefix="/v1")
    app.include_router(capabilities_router, prefix="/v1")
    app.include_router(messaging_router)
    app.include_router(persistence_router)
    app.include_router(install_router)
    app.include_router(webui_router)
    app.include_router(llm_router, prefix="/v1")
    app.include_router(workflow_router)
