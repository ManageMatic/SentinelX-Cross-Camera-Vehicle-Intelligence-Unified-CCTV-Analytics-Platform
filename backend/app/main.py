"""SentinelX FastAPI Backend Application Entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import logger
from app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    settings.ensure_storage_directories()
    logger.info("Initializing SentinelX Backend v%s...", settings.VERSION)
    logger.info("Environment: %s | Debug: %s", settings.ENVIRONMENT, settings.DEBUG)
    logger.info("Configuration (Safe): %s", settings.get_safe_dict())

    # Initialize database tables
    await init_db()

    yield

    # Teardown
    await close_db()
    logger.info("SentinelX Backend shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Cross-Camera Vehicle Intelligence & Unified CCTV Analytics Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Centralized exception handling without exposing internals in production."""
    logger.error(
        "Unhandled server exception on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=settings.DEBUG,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred. Please contact the administrator."},
    )


# Root Health & Version endpoints
@app.get("/health", tags=["Health"])
async def root_health_check():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "service": "SentinelX Backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/version", tags=["System"])
async def root_version():
    """Root version endpoint."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


# Include v1 API router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
