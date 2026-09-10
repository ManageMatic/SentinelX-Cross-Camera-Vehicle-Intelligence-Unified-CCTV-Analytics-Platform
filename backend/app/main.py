"""SentinelX FastAPI Backend Application Entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.core.middleware import RequestLoggingMiddleware
from app.db.session import close_db, init_db
from app.schemas.common import APIResponse
from app.schemas.system import HealthData, VersionData


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    settings.ensure_storage_directories()
    logger.info("Initializing NETRA-X Backend v%s...", settings.VERSION)
    logger.info("Environment: %s | Debug: %s", settings.ENVIRONMENT, settings.DEBUG)
    logger.info("Configuration (Safe): %s", settings.get_safe_dict())

    # Initialize database tables
    await init_db()

    yield

    # Teardown
    await close_db()
    logger.info("NETRA-X Backend shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Unified Vehicle Tracking & Command Intelligence Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Custom Request Logging & Tracing Middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Centralized Error and Exception Handlers
register_exception_handlers(app)


# Root Health & Version endpoints (Used by Docker healthchecks, probes, and load balancers)
@app.get("/health", response_model=APIResponse[HealthData], tags=["Health"])
async def root_health_check(request: Request):
    """Root health check endpoint."""
    request_id = getattr(request.state, "request_id", None)
    return APIResponse(
        success=True,
        message="NETRA-X Backend is operational",
        data=HealthData(
            status="healthy",
            service="NETRA-X Backend",
            version=settings.VERSION,
            environment=settings.ENVIRONMENT.value,
            database_connected=True,
            storage_accessible=True,
        ),
        request_id=request_id,
    )


@app.get("/api/version", response_model=APIResponse[VersionData], tags=["System"])
async def root_version(request: Request):
    """Root version endpoint."""
    request_id = getattr(request.state, "request_id", None)
    return APIResponse(
        success=True,
        message="SentinelX Version",
        data=VersionData(
            project=settings.PROJECT_NAME,
            version=settings.VERSION,
        ),
        request_id=request_id,
    )


# Include v1 API router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
