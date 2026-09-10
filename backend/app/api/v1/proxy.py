"""WebRTC (WHEP), HLS Stream Proxy, and Live Snapshot API Endpoints."""

from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import ResourceNotFoundException
from app.db.session import get_db
from app.models.camera import Camera
from app.schemas.common import APIResponse
from app.schemas.proxy import (
    CameraStreamEndpoints,
    StreamProxyInfo,
    WHEPExchangeRequest,
    WHEPExchangeResponse,
)
from app.services.stream_proxy import stream_proxy_service
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/proxy", tags=["WebRTC & HLS Stream Proxy"])


@router.get(
    "/endpoints",
    response_model=APIResponse[CameraStreamEndpoints],
    summary="List sanitized, browser-safe streaming endpoints for all cameras",
)
async def list_stream_endpoints(db: AsyncSession = Depends(get_db)):
    """Retrieve WHEP, HLS, and Snapshot URLs for all registered cameras with RTSP credentials masked."""
    stmt = select(Camera).order_by(Camera.created_at.asc())
    result = await db.execute(stmt)
    cameras = result.scalars().all()

    proxy_infos = [stream_proxy_service.get_stream_proxy_info(cam) for cam in cameras]
    online_count = sum(1 for p in proxy_infos if p.is_online)

    payload = CameraStreamEndpoints(
        total_cameras=len(proxy_infos),
        online_count=online_count,
        timestamp=datetime.now(timezone.utc),
        cameras=proxy_infos,
    )

    return APIResponse(
        success=True,
        message="Stream endpoints catalog retrieved successfully",
        data=payload,
    )


@router.get(
    "/{camera_id}/info",
    response_model=APIResponse[StreamProxyInfo],
    summary="Get sanitized streaming endpoints for a specific camera",
)
async def get_camera_proxy_info(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve browser-safe WHEP and HLS streaming endpoints for an individual camera."""
    stmt = select(Camera).where((Camera.id == camera_id) | (Camera.external_camera_id == camera_id))
    result = await db.execute(stmt)
    camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException("Camera", camera_id)

    info = stream_proxy_service.get_stream_proxy_info(camera)
    return APIResponse(
        success=True,
        message="Camera stream proxy info retrieved successfully",
        data=info,
    )


@router.post(
    "/{camera_id}/whep",
    response_model=APIResponse[WHEPExchangeResponse],
    status_code=status.HTTP_200_OK,
    summary="WHEP WebRTC SDP Offer/Answer negotiation for ultra-low latency playback",
)
async def exchange_whep_offer(
    camera_id: str,
    request: Request,
    payload: Optional[WHEPExchangeRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """Exchanges client WebRTC SDP offer with media server WHEP egress channel."""
    stmt = select(Camera).where((Camera.id == camera_id) | (Camera.external_camera_id == camera_id))
    result = await db.execute(stmt)
    camera = result.scalar_one_or_none()

    if not camera:
        raise ResourceNotFoundException("Camera", camera_id)

    # Extract client SDP from JSON payload or raw request body
    client_sdp = ""
    if payload and payload.sdp:
        client_sdp = payload.sdp
    else:
        body_bytes = await request.body()
        client_sdp = body_bytes.decode("utf-8")

    if not client_sdp:
        client_sdp = "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n"

    answer = await stream_proxy_service.exchange_whep_sdp(camera, client_sdp)
    return APIResponse(
        success=True,
        message="WHEP SDP negotiation successful",
        data=answer,
    )


@router.get(
    "/{camera_id}/snapshot",
    summary="Get real-time live JPEG image snapshot from camera feed",
    responses={200: {"content": {"image/jpeg": {}}}},
)
async def get_camera_snapshot(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve binary JPEG image snapshot from the active video stream worker."""
    stmt = select(Camera).where((Camera.id == camera_id) | (Camera.external_camera_id == camera_id))
    result = await db.execute(stmt)
    camera = result.scalar_one_or_none()

    jpeg_bytes = stream_proxy_service.get_camera_snapshot_jpeg(
        camera_id=camera.id if camera else camera_id,
        camera=camera,
    )

    return Response(content=jpeg_bytes, media_type="image/jpeg")
