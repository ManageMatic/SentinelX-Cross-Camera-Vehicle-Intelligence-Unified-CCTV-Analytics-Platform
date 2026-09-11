"""Pydantic schemas for Camera catalog discovery, ingestion, and REST responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SentinelIngestCameraItem(BaseModel):
    """Raw camera record format from Sentinel /api/ingest catalog."""

    id: Optional[str] = None
    camera_id: Optional[str] = None
    name: Optional[str] = None
    location_name: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = "Traffic Police"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    lng: Optional[float] = None
    rtsp_url: Optional[str] = None
    stream_url: Optional[str] = None
    url: Optional[str] = None
    whep_url: Optional[str] = None
    hls_url: Optional[str] = None
    vendor: Optional[str] = "Generic RTSP"
    vms: Optional[str] = "Sentinel VMS"
    protocol: Optional[str] = "RTSP/TCP"
    codec: Optional[str] = "H264"
    width: Optional[int] = 1920
    height: Optional[int] = 1080
    fps: Optional[float] = 25.0
    status: Optional[str] = "ONLINE"
    live_status: Optional[bool] = True
    extra_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")


class CameraBase(BaseModel):
    """Base fields for Camera."""

    external_camera_id: str
    name: str
    location_name: str = "Ahmedabad"
    department: str = "Traffic Police"
    latitude: float
    longitude: float
    vendor: str = "Generic RTSP"
    vms: str = "Sentinel VMS"
    protocol: str = "RTSP/TCP"
    codec: str = "H264"
    width: int = 1920
    height: int = 1080
    fps: float = 25.0
    rtsp_url: str
    whep_url: Optional[str] = None
    hls_url: Optional[str] = None
    live_status: bool = True
    is_active_for_ai: bool = False


class CameraCreate(CameraBase):
    """Schema for manual camera registration."""

    pass


class CameraUpdate(BaseModel):
    """Schema for updating camera settings."""

    name: Optional[str] = None
    location_name: Optional[str] = None
    department: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rtsp_url: Optional[str] = None
    whep_url: Optional[str] = None
    hls_url: Optional[str] = None
    live_status: Optional[bool] = None
    is_active_for_ai: Optional[bool] = None
    fps: Optional[float] = None


class CameraHealthResponse(BaseModel):
    """Health record for camera telemetry."""

    id: str
    camera_id: str
    is_online: bool
    measured_fps: float
    latency_ms: float
    reconnect_count: int
    last_error: Optional[str] = None
    last_ping: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraSourceResponse(BaseModel):
    """Auxiliary stream profiles."""

    id: str
    camera_id: str
    stream_type: str
    url: str
    codec: str
    resolution: str

    model_config = ConfigDict(from_attributes=True)


class CameraResponse(BaseModel):
    """Standard Camera response."""

    id: str
    external_camera_id: str
    name: str
    location_name: str
    department: str
    latitude: float
    longitude: float
    vendor: str
    vms: str
    protocol: str
    codec: str
    width: int
    height: int
    fps: float
    whep_url: Optional[str] = None
    hls_url: Optional[str] = None
    live_status: bool
    is_active_for_ai: bool
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraDetailResponse(CameraResponse):
    """Detailed Camera response including auxiliary sources and latest health metrics."""

    sources: List[CameraSourceResponse] = Field(default_factory=list)
    latest_health: Optional[CameraHealthResponse] = None


class CameraTestResult(BaseModel):
    """Result of an on-demand RTSP connectivity test."""

    camera_id: str
    reachable: bool
    first_frame_received: bool
    codec: str = "h264"
    width: int = 0
    height: int = 0
    fps: float = 0.0
    latency_ms: float = 0.0
    message: str


class CameraHealthLiveResponse(BaseModel):
    """Live streaming health and telemetry for an active camera stream."""

    camera_id: str
    is_online: bool
    state: str
    measured_fps: float
    latency_ms: float
    resolution_width: int
    resolution_height: int
    codec: str
    reconnect_count: int
    decoder_errors: int
    total_frames_received: int
    dropped_frames: int
    last_frame_time: Optional[datetime] = None
    last_error: Optional[str] = None


class CameraSyncResult(BaseModel):
    """Summary of dynamic catalog ingestion sync operation."""

    catalog_url: str
    total_discovered: int
    added_count: int
    updated_count: int
    unchanged_count: int
    errors_count: int
    synced_at: datetime
    duration_ms: float

