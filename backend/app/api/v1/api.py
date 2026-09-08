"""Master API Router for v1 endpoints."""

from app.api.v1 import health
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["System"])
