"""Master API Router for v1 endpoints."""

from app.api.v1 import health, system
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["System"])
api_router.include_router(system.router, prefix="/system", tags=["System Telemetry"])
