"""ByteTrack Multi-Object Tracking REST API Endpoints (Module 11)."""

from typing import List

from app.core.exceptions import ResourceNotFoundException
from app.db.session import get_db
from app.models.camera import Camera
from app.schemas.common import APIResponse
from app.schemas.tracking import (
    TrackedVehicle,
    TrackerTelemetry,
    TrajectoryPoint,
)
from app.services.byte_tracker import camera_tracker_manager
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/tracking", tags=["Multi-Object Tracking (ByteTrack)"])


@router.get(
    "/telemetry",
    response_model=APIResponse[TrackerTelemetry],
    summary="Get multi-object tracking platform telemetry",
)
async def get_tracking_telemetry() -> APIResponse[TrackerTelemetry]:
    """Retrieve tracking latency, total active tracks, lost counts, and per-camera summaries."""
    telemetry = camera_tracker_manager.get_telemetry()
    return APIResponse(
        success=True,
        message="Tracker telemetry retrieved successfully",
        data=telemetry,
    )


@router.get(
    "/{camera_id}/active",
    response_model=APIResponse[List[TrackedVehicle]],
    summary="Get all currently active vehicle tracks on a camera feed",
)
async def get_active_camera_tracks(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[TrackedVehicle]]:
    """Retrieve real-time confirmed tracks, velocities, and best crop metrics for a camera."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        result = await db.execute(select(Camera).where(Camera.external_camera_id == camera_id))
        camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException(detail=f"Camera with identifier '{camera_id}' not found")

    active_tracks = camera_tracker_manager.get_active_tracks(camera.id)
    return APIResponse(
        success=True,
        message=f"Found {len(active_tracks)} active track(s) for camera '{camera.external_camera_id}'",
        data=active_tracks,
    )


@router.get(
    "/{camera_id}/trajectory/{track_id}",
    response_model=APIResponse[List[TrajectoryPoint]],
    summary="Get full spatial breadcrumb trajectory for a vehicle track",
)
async def get_track_trajectory(
    camera_id: str,
    track_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[TrajectoryPoint]]:
    """Retrieve sequential (x, y) journey coordinates for plotting vehicle paths on tactical maps."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        result = await db.execute(select(Camera).where(Camera.external_camera_id == camera_id))
        camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException(detail=f"Camera with identifier '{camera_id}' not found")

    trajectory = camera_tracker_manager.get_track_trajectory(camera.id, track_id)
    if trajectory is None:
        raise ResourceNotFoundException(
            detail=f"Track ID '{track_id}' not found on camera '{camera.external_camera_id}'"
        )

    return APIResponse(
        success=True,
        message=f"Retrieved {len(trajectory)} trajectory point(s) for track '{track_id}'",
        data=trajectory,
    )


@router.post(
    "/{camera_id}/reset",
    response_model=APIResponse[dict],
    summary="Reset tracking state and clear active tracks for a camera",
)
async def reset_camera_tracking(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Clear in-memory tracks and Kalman filter states for a camera stream."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        result = await db.execute(select(Camera).where(Camera.external_camera_id == camera_id))
        camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException(detail=f"Camera with identifier '{camera_id}' not found")

    cleared = camera_tracker_manager.reset_camera(camera.id)
    return APIResponse(
        success=True,
        message=f"Tracking state reset for camera '{camera.external_camera_id}'",
        data={"camera_id": camera.id, "cleared": cleared},
    )
