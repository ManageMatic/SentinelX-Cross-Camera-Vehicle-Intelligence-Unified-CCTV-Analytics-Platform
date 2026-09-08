"""Health and system version endpoints."""

from app.core.config import settings
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "SentinelX Backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/version", tags=["System"])
async def get_version():
    """Returns the API version."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_version": "v1",
    }
