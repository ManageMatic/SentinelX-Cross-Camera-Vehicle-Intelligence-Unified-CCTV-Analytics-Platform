"""Pydantic schemas and dataclasses for Camera Frame Buffers and Adaptive Backpressure."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BackpressureLevel(str, Enum):
    """Backpressure congestion states based on queue capacity utilization."""

    NORMAL = "NORMAL"  # < 60% capacity
    MODERATE = "MODERATE"  # 60% - 85% capacity
    CRITICAL = "CRITICAL"  # > 85% capacity


class FrameDropStrategy(str, Enum):
    """Strategies for handling frame buffer congestion during AI inference spikes."""

    DROP_OLDEST = "DROP_OLDEST"  # Drops earliest unread frame to ensure lowest latency
    DROP_NEWEST = "DROP_NEWEST"  # Drops incoming frame if buffer is full
    DROP_NON_KEYFRAME = "DROP_NON_KEYFRAME"  # Prioritizes keyframes over intermediate frames
    DECIMATE_DYNAMIC = "DECIMATE_DYNAMIC"  # Dynamically increases decimation step


class BufferConfig(BaseModel):
    """Configuration parameters for an individual camera's frame buffer queue."""

    max_capacity: int = Field(
        default=20, ge=1, le=100, description="Maximum bounded ring buffer capacity"
    )
    target_ai_fps: float = Field(
        default=10.0, ge=1.0, le=30.0, description="Target frame rate dispatched to AI workers"
    )
    drop_strategy: FrameDropStrategy = Field(
        default=FrameDropStrategy.DROP_OLDEST,
        description="Frame dropping policy when queue utilization reaches backpressure threshold",
    )
    backpressure_threshold_pct: float = Field(
        default=80.0,
        ge=50.0,
        le=95.0,
        description="Queue fullness percentage triggering backpressure mitigation",
    )

    model_config = ConfigDict(from_attributes=True)


class CameraBufferStats(BaseModel):
    """Real-time queue metrics and telemetry for an active camera frame buffer."""

    camera_id: str
    queue_size: int
    max_capacity: int
    utilization_pct: float
    backpressure_level: BackpressureLevel
    target_ai_fps: float
    ingest_fps: float
    dispatch_fps: float
    total_ingested_frames: int
    total_dispatched_frames: int
    total_dropped_frames: int
    drop_rate_pct: float
    last_ingested_at: Optional[datetime] = None
    last_dispatched_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BufferPoolStatus(BaseModel):
    """Aggregate telemetry across all active camera frame buffers in the platform."""

    total_buffers: int
    active_queues: int
    critical_queues: int
    total_buffered_frames: int
    total_dropped_frames: int
    average_utilization_pct: float
    timestamp: datetime
    buffers: List[CameraBufferStats] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
