"""Frame Buffer & Adaptive Backpressure Queue API Endpoints (Module 9)."""

from app.core.exceptions import ResourceNotFoundException
from app.db.session import get_db
from app.models.camera import Camera
from app.schemas.buffer import BufferConfig, BufferPoolStatus, CameraBufferStats
from app.schemas.common import APIResponse
from app.services.frame_buffer import frame_buffer_manager
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/buffers", tags=["Frame Buffers & Backpressure"])


@router.get(
    "/status",
    response_model=APIResponse[BufferPoolStatus],
    summary="Get aggregate frame buffer pool telemetry and backpressure state",
)
async def get_buffer_pool_status() -> APIResponse[BufferPoolStatus]:
    """Retrieve aggregate telemetry, queue occupancy, drop rates, and backpressure congestion across all cameras."""
    status_data = frame_buffer_manager.get_pool_status()
    return APIResponse(
        success=True,
        message="Buffer pool status retrieved successfully",
        data=status_data,
    )


@router.get(
    "/{camera_id}/stats",
    response_model=APIResponse[CameraBufferStats],
    summary="Get real-time frame buffer telemetry for a specific camera",
)
async def get_camera_buffer_stats(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CameraBufferStats]:
    """Retrieve real-time queue utilization, drop rates, ingest/dispatch FPS, and backpressure level for a camera."""
    # Verify camera exists in database
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        # Check by external_camera_id fallback
        result = await db.execute(select(Camera).where(Camera.external_camera_id == camera_id))
        camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException(detail=f"Camera with identifier '{camera_id}' not found")

    stats = frame_buffer_manager.get_buffer_stats(camera.id)
    if not stats:
        # If no frames enqueued yet, initialize buffer and return baseline
        buffer = frame_buffer_manager.get_or_create_buffer(camera.id)
        stats = buffer.get_stats()

    return APIResponse(
        success=True,
        message=f"Buffer telemetry for camera '{camera.external_camera_id}' retrieved successfully",
        data=stats,
    )


@router.post(
    "/{camera_id}/configure",
    response_model=APIResponse[CameraBufferStats],
    summary="Dynamically configure frame buffer parameters for a camera",
)
async def configure_camera_buffer(
    camera_id: str,
    config: BufferConfig,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CameraBufferStats]:
    """Dynamically adjust buffer capacity (5-100), target AI FPS (1-30), drop strategy, and congestion thresholds."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        result = await db.execute(select(Camera).where(Camera.external_camera_id == camera_id))
        camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException(detail=f"Camera with identifier '{camera_id}' not found")

    updated_stats = frame_buffer_manager.configure_buffer(camera.id, config)
    return APIResponse(
        success=True,
        message=f"Buffer configuration updated for camera '{camera.external_camera_id}'",
        data=updated_stats,
    )


@router.post(
    "/{camera_id}/clear",
    response_model=APIResponse[dict],
    summary="Purge all frames currently queued in a camera buffer",
)
async def clear_camera_buffer(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Purge stale video frames from memory for a specific camera stream."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        result = await db.execute(select(Camera).where(Camera.external_camera_id == camera_id))
        camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException(detail=f"Camera with identifier '{camera_id}' not found")

    cleared = frame_buffer_manager.clear_buffer(camera.id)
    return APIResponse(
        success=True,
        message=f"Buffer cleared successfully for camera '{camera.external_camera_id}'",
        data={"camera_id": camera.id, "cleared": cleared},
    )


@router.post(
    "/clear-all",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Purge all frame queues across all cameras in the platform",
)
async def clear_all_buffers() -> APIResponse[dict]:
    """Purge all in-memory frame buffers across the entire platform."""
    total_discarded = frame_buffer_manager.clear_all()
    return APIResponse(
        success=True,
        message=f"All camera buffers cleared. Discarded {total_discarded} frames.",
        data={"total_frames_discarded": total_discarded},
    )
