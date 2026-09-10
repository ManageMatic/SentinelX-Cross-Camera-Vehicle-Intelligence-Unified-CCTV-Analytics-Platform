"""Pydantic schemas for WebRTC (WHEP), HLS streaming proxy, and camera stream endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WHEPExchangeRequest(BaseModel):
    """Client WebRTC SDP Offer."""

    sdp: str = Field(description="Client SDP offer string")


class WHEPExchangeResponse(BaseModel):
    """Media Server WebRTC SDP Answer."""

    sdp: str = Field(description="Media server SDP answer string")
    media_url: Optional[str] = None


class StreamProxyInfo(BaseModel):
    """Browser-safe streaming endpoints for an individual CCTV camera."""

    camera_id: str
    external_camera_id: str
    name: str
    location_name: str
    whep_endpoint: str
    hls_endpoint: str
    snapshot_endpoint: str
    preferred_protocol: str = "WHEP"
    is_online: bool = True
    fps: float = 25.0
    codec: Optional[str] = "H264"
    resolution: Optional[str] = "1920x1080"

    model_config = ConfigDict(from_attributes=True)


class CameraStreamEndpoints(BaseModel):
    """Aggregated catalog of sanitized streaming endpoints across all cameras."""

    total_cameras: int
    online_count: int
    timestamp: datetime
    cameras: List[StreamProxyInfo] = Field(default_factory=list)
