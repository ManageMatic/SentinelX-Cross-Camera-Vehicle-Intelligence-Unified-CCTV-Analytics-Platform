"""System Telemetry, Component Health, and Uptime API endpoints."""

import os
import time

from app.core.config import settings
from app.db.session import get_db
from app.schemas.common import APIResponse
from app.schemas.system import ComponentHealth, SystemStatusData
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
START_TIME = time.time()


@router.get(
    "/status",
    response_model=APIResponse[SystemStatusData],
    summary="Get comprehensive system status",
)
async def get_system_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Checks and returns the status of core platform components (Database, Storage, Config)."""
    request_id = getattr(request.state, "request_id", None)
    components = {}

    # 1. Check Database Connectivity
    db_start = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_latency = (time.perf_counter() - db_start) * 1000.0
        components["database"] = ComponentHealth(
            status="UP",
            latency_ms=round(db_latency, 2),
            details=f"Connected ({settings.DATABASE_URL.split('://')[0]})",
        )
    except Exception as exc:
        components["database"] = ComponentHealth(
            status="DOWN",
            details=f"Database unreachable: {str(exc)}",
        )

    # 2. Check Evidence Storage Path
    storage_path = settings.EVIDENCE_STORAGE_PATH
    if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
        components["evidence_storage"] = ComponentHealth(
            status="UP",
            details=f"Writable at {storage_path}",
        )
    else:
        components["evidence_storage"] = ComponentHealth(
            status="DEGRADED",
            details=f"Storage path {storage_path} is not writable",
        )

    # 3. Overall System Health aggregation
    is_all_up = all(c.status == "UP" for c in components.values())
    overall_status = "HEALTHY" if is_all_up else "DEGRADED"

    status_data = SystemStatusData(
        status=overall_status,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT.value,
        uptime_seconds=round(time.time() - START_TIME, 2),
        components=components,
    )

    return APIResponse(
        success=True,
        message="System status telemetry retrieved successfully",
        data=status_data,
        request_id=request_id,
    )
