"""RTSP / TCP Video Streams and Ingestion Telemetry API Endpoints."""

from typing import Optional

from app.core.exceptions import ResourceNotFoundException
from app.db.session import get_db
from app.models.camera import Camera
from app.schemas.common import APIResponse
from app.schemas.resilience import StreamHealthSummary, StreamWatchdogRecord
from app.schemas.stream import StreamPoolStatus, StreamWorkerStats
from app.services.stream_manager import stream_manager
from app.services.stream_worker import stream_pool
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/streams", tags=["Live Video Ingestion & Telemetry"])


@router.get(
    "/status",
    response_model=APIResponse[StreamPoolStatus],
    summary="Get aggregate telemetry and FPS across all active stream workers",
)
async def get_stream_pool_status():
    """Retrieve live FPS, dropped frames, and connection states for all camera feeds."""
    status_data = stream_pool.get_pool_status()
    return APIResponse(
        success=True,
        message="Stream pool status retrieved successfully",
        data=status_data,
    )


@router.get(
    "/health",
    response_model=APIResponse[StreamHealthSummary],
    summary="Get stream watchdog health metrics and circuit breaker states",
)
async def get_stream_health_summary():
    """Retrieve watchdog health telemetry, stall detections, and circuit breaker states across all cameras."""
    health_summary = stream_manager.get_health_summary()
    return APIResponse(
        success=True,
        message="Stream health summary retrieved successfully",
        data=health_summary,
    )


@router.get(
    "/{camera_id}/stats",
    response_model=APIResponse[StreamWorkerStats],
    summary="Get real-time worker metrics for a specific camera feed",
)
async def get_stream_worker_stats(camera_id: str):
    """Retrieve measured FPS, buffer state, and uptime for an individual camera stream."""
    worker = stream_pool.get_worker(camera_id)
    if not worker:
        raise ResourceNotFoundException("Active Stream Worker", camera_id)

    return APIResponse(
        success=True,
        message="Camera stream telemetry retrieved successfully",
        data=worker.get_stats(),
    )


@router.get(
    "/{camera_id}/health",
    response_model=APIResponse[StreamWatchdogRecord],
    summary="Get watchdog record and circuit breaker state for a specific camera",
)
async def get_camera_watchdog_health(camera_id: str):
    """Inspect camera stream stall status, consecutive failures, and backoff timers."""
    record = stream_manager.check_camera_health(camera_id)
    return APIResponse(
        success=True,
        message="Camera watchdog record retrieved successfully",
        data=record,
    )


@router.post(
    "/{camera_id}/start",
    response_model=APIResponse[StreamWorkerStats],
    status_code=status.HTTP_200_OK,
    summary="Start RTSP / TCP ingestion worker for a camera",
)
async def start_stream_worker(
    camera_id: str,
    use_synthetic: bool = Query(
        False, description="Enable synthetic test generator for headless testing"
    ),
    fps_override: Optional[float] = Query(None, description="Optional override for target FPS"),
    db: AsyncSession = Depends(get_db),
):
    """Spawn or activate an RTSP/TCP video frame ingestion worker."""
    stmt = select(Camera).where((Camera.id == camera_id) | (Camera.external_camera_id == camera_id))
    result = await db.execute(stmt)
    camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException("Camera", camera_id)

    target_fps = fps_override or camera.fps or 25.0
    worker = stream_pool.start_worker(
        camera_id=camera.id,
        external_camera_id=camera.external_camera_id,
        rtsp_url=camera.rtsp_url,
        target_fps=target_fps,
        use_synthetic_stream=use_synthetic,
    )

    return APIResponse(
        success=True,
        message=f"Stream ingestion worker started for camera '{camera.external_camera_id}'",
        data=worker.get_stats(),
    )


@router.post(
    "/{camera_id}/stop",
    response_model=APIResponse[dict],
    summary="Stop RTSP / TCP ingestion worker for a camera",
)
async def stop_stream_worker(camera_id: str):
    """Stop active video stream worker for a camera."""
    worker = stream_pool.get_worker(camera_id)
    if not worker:
        return APIResponse(
            success=True,
            message=f"No active worker running for camera '{camera_id}'",
            data={"camera_id": camera_id, "stopped": False},
        )

    stream_pool.stop_worker(camera_id)
    return APIResponse(
        success=True,
        message=f"Stream ingestion worker stopped for camera '{camera_id}'",
        data={"camera_id": camera_id, "stopped": True},
    )


@router.post(
    "/{camera_id}/reconnect",
    response_model=APIResponse[StreamWatchdogRecord],
    summary="Force immediate reconnect attempt for a camera stream",
)
async def force_reconnect_stream(camera_id: str):
    """Bypasses backoff timer and immediately triggers reconnection for a camera."""
    record = stream_manager.force_reconnect(camera_id)
    return APIResponse(
        success=True,
        message=f"Immediate reconnection triggered for camera '{camera_id}'",
        data=record,
    )


@router.post(
    "/{camera_id}/reset-circuit",
    response_model=APIResponse[StreamWatchdogRecord],
    summary="Reset circuit breaker state back to CLOSED",
)
async def reset_camera_circuit_breaker(camera_id: str):
    """Manually resets circuit breaker back to CLOSED state."""
    record = stream_manager.reset_circuit(camera_id)
    return APIResponse(
        success=True,
        message=f"Circuit breaker reset to CLOSED for camera '{camera_id}'",
        data=record,
    )
