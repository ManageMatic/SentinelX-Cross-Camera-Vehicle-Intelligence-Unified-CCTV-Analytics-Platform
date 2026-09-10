"""Camera Registry and Dynamic Ingestion API Endpoints."""

import math
from typing import Optional

from app.core.exceptions import ResourceNotFoundException
from app.db.session import get_db
from app.models.camera import Camera, CameraHealth, CameraSource
from app.schemas.camera import (
    CameraCreate,
    CameraDetailResponse,
    CameraHealthResponse,
    CameraResponse,
    CameraSourceResponse,
    CameraSyncResult,
    CameraUpdate,
)
from app.schemas.common import APIResponse, PaginatedResponse, PaginationMetadata
from app.services.camera_catalog import catalog_service
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/cameras", tags=["Camera Registry & Ingestion"])


@router.get(
    "",
    response_model=PaginatedResponse[CameraResponse],
    summary="List all registered cameras with filtering and pagination",
)
async def list_cameras(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    live_status: Optional[bool] = Query(None, description="Filter by online/offline status"),
    department: Optional[str] = Query(None, description="Filter by police department"),
    search: Optional[str] = Query(None, description="Search by camera name, ID, or location"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all ingested CCTV cameras."""
    query = select(Camera)
    count_query = select(func.count(Camera.id))

    if live_status is not None:
        query = query.where(Camera.live_status == live_status)
        count_query = count_query.where(Camera.live_status == live_status)

    if department:
        query = query.where(Camera.department.ilike(f"%{department}%"))
        count_query = count_query.where(Camera.department.ilike(f"%{department}%"))

    if search:
        search_filter = (
            Camera.name.ilike(f"%{search}%")
            | Camera.external_camera_id.ilike(f"%{search}%")
            | Camera.location_name.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    query = query.order_by(Camera.created_at.asc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    cameras = result.scalars().all()

    camera_responses = [CameraResponse.model_validate(c) for c in cameras]
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    pagination = PaginationMetadata(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

    return PaginatedResponse(
        success=True,
        message="Cameras retrieved successfully",
        data=camera_responses,
        pagination=pagination,
    )


@router.get(
    "/{camera_id}",
    response_model=APIResponse[CameraDetailResponse],
    summary="Get single camera with stream sources and health telemetry",
)
async def get_camera_detail(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve camera metadata and active stream endpoints by internal UUID or external_camera_id."""
    stmt = select(Camera).where((Camera.id == camera_id) | (Camera.external_camera_id == camera_id))
    result = await db.execute(stmt)
    camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException("Camera", camera_id)

    # Get latest health metric
    health_stmt = (
        select(CameraHealth)
        .where(CameraHealth.camera_id == camera.id)
        .order_by(CameraHealth.created_at.desc())
        .limit(1)
    )
    health_result = await db.execute(health_stmt)
    latest_health = health_result.scalar_one_or_none()

    detail = CameraDetailResponse(
        id=camera.id,
        external_camera_id=camera.external_camera_id,
        name=camera.name,
        location_name=camera.location_name,
        department=camera.department,
        latitude=camera.latitude,
        longitude=camera.longitude,
        vendor=camera.vendor,
        vms=camera.vms,
        protocol=camera.protocol,
        codec=camera.codec,
        width=camera.width,
        height=camera.height,
        fps=camera.fps,
        whep_url=camera.whep_url,
        hls_url=camera.hls_url,
        live_status=camera.live_status,
        is_active_for_ai=camera.is_active_for_ai,
        last_seen=camera.last_seen,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
        sources=[CameraSourceResponse.model_validate(s) for s in camera.sources],
        latest_health=(
            CameraHealthResponse.model_validate(latest_health) if latest_health else None
        ),
    )

    return APIResponse(
        success=True,
        message="Camera details retrieved successfully",
        data=detail,
    )


@router.post(
    "/sync",
    response_model=APIResponse[CameraSyncResult],
    summary="Trigger dynamic discovery sync from Sentinel /api/ingest",
)
async def sync_catalog(
    catalog_url: Optional[str] = Query(
        None, description="Optional override URL for camera catalog ingestion"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Synchronize camera feeds dynamically from Gujarat Police Sentinel Sandbox without hardcoding."""
    sync_result = await catalog_service.sync_catalog_to_db(db=db, catalog_url=catalog_url)
    return APIResponse(
        success=True,
        message="Dynamic camera catalog synchronization complete",
        data=sync_result,
    )


@router.post(
    "",
    response_model=APIResponse[CameraResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Manually register a new camera feed",
)
async def create_camera(
    payload: CameraCreate,
    db: AsyncSession = Depends(get_db),
):
    """Manually onboard a CCTV camera feed into the registry."""
    # Check if external_camera_id exists
    stmt = select(Camera).where(Camera.external_camera_id == payload.external_camera_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ValueError(f"Camera with ID '{payload.external_camera_id}' already registered.")

    camera = Camera(**payload.model_dump())
    db.add(camera)
    await db.flush()

    # Add main source
    source = CameraSource(
        camera_id=camera.id,
        stream_type="MAIN",
        url=payload.rtsp_url,
        codec=payload.codec,
        resolution=f"{payload.width}x{payload.height}",
    )
    db.add(source)
    await db.commit()
    await db.refresh(camera)

    return APIResponse(
        success=True,
        message="Camera registered successfully",
        data=CameraResponse.model_validate(camera),
    )


@router.patch(
    "/{camera_id}",
    response_model=APIResponse[CameraResponse],
    summary="Update camera settings or status",
)
async def update_camera(
    camera_id: str,
    payload: CameraUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update camera configuration, AI activation flag, or coordinates."""
    stmt = select(Camera).where((Camera.id == camera_id) | (Camera.external_camera_id == camera_id))
    result = await db.execute(stmt)
    camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException("Camera", camera_id)

    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(camera, key, val)

    await db.commit()
    await db.refresh(camera)

    return APIResponse(
        success=True,
        message="Camera updated successfully",
        data=CameraResponse.model_validate(camera),
    )
