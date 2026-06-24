"""FastAPI route definitions."""

from fastapi import APIRouter

from .health import router as health_router
from .projects import draft_router
from .projects import router as projects_router
from .runs import router as runs_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(projects_router)
api_router.include_router(draft_router)
api_router.include_router(runs_router)

__all__ = ["api_router"]
