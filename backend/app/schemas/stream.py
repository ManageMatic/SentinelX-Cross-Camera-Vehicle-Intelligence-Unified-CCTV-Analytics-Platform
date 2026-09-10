"""Pydantic schemas and dataclasses for RTSP Video Stream Ingestion and Telemetry."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class StreamWorkerState(str, Enum):
    """Operational states for RTSP stream worker."""

    INITIALIZING = "INITIALIZING"
    CONNECTING = "CONNECTING"
    STREAMING = "STREAMING"
    RECONNECTING = "RECONNECTING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


@dataclass
class VideoFrame:
    """In-memory decoded video frame container for downstream AI workers."""

    camera_id: str
    frame_index: int
    timestamp_utc: datetime
    image: np.ndarray
    width: int
    height: int
    fps: float
    is_keyframe: bool = False
    metadata: Optional[Dict[str, Any]] = None


class StreamWorkerStats(BaseModel):
    """Real-time performance and health metrics for an active camera stream worker."""

    camera_id: str
    external_camera_id: str
    rtsp_url: str
    state: StreamWorkerState
    measured_fps: float
    target_fps: float
    total_frames_read: int
    dropped_frames: int
    reconnect_attempts: int
    uptime_seconds: float
    last_frame_time: Optional[datetime] = None
    last_error: Optional[str] = None
    transport_protocol: str = "TCP"

    model_config = ConfigDict(from_attributes=True)


class StreamPoolStatus(BaseModel):
    """Aggregate telemetry for the entire worker pool across all active CCTV streams."""

    total_registered: int
    total_active_workers: int
    streaming_count: int
    reconnecting_count: int
    error_count: int
    total_aggregate_fps: float
    workers: List[StreamWorkerStats] = Field(default_factory=list)
