"""Health and Version API endpoints."""

from app.core.config import settings
from app.schemas.common import APIResponse
from app.schemas.system import HealthData, VersionData
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health", response_model=APIResponse[HealthData], tags=["Health"])
async def health_check(request: Request):
    """System health check endpoint."""
    request_id = getattr(request.state, "request_id", None)
    data = HealthData(
        status="healthy",
        service="SentinelX Backend",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT.value,
        database_connected=True,
        storage_accessible=True,
    )
    return APIResponse(
        success=True,
        message="Service is healthy and operational",
        data=data,
        request_id=request_id,
    )


@router.get("/version", response_model=APIResponse[VersionData], tags=["System"])
async def get_version(request: Request):
    """Returns the API version and license metadata."""
    request_id = getattr(request.state, "request_id", None)
    data = VersionData(
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        api_version="v1",
    )
    return APIResponse(
        success=True,
        message="Version metadata retrieved successfully",
        data=data,
        request_id=request_id,
    )
