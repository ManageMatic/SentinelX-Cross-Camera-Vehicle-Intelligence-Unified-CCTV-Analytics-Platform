"""Pydantic schemas and dataclasses for ByteTrack Multi-Object Vehicle Tracking (Module 11)."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.detection import BoundingBox, VehicleClass


class TrackState(str, Enum):
    """Lifecycle state of a tracked vehicle."""

    NEW = "NEW"  # First detected, awaiting confirmation (min_hits)
    TRACKED = "TRACKED"  # Confirmed and actively tracked in current frame
    LOST = "LOST"  # Temporarily lost / occluded, predicting position
    REMOVED = "REMOVED"  # Expired after max_lost_frames


class TrajectoryPoint(BaseModel):
    """Spatial coordinate sample along a vehicle's observed trajectory."""

    x: float = Field(description="Center X pixel coordinate")
    y: float = Field(description="Center Y pixel coordinate")
    norm_x: float = Field(description="Normalized Center X [0.0 - 1.0]")
    norm_y: float = Field(description="Normalized Center Y [0.0 - 1.0]")
    frame_index: int
    timestamp_utc: datetime
    speed_px_per_sec: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class TrackedVehicle(BaseModel):
    """Rich vehicle track record maintaining temporal identity and trajectory history."""

    track_id: str
    camera_id: str
    vehicle_class: VehicleClass
    state: TrackState
    start_frame: int
    last_frame: int
    total_frames_tracked: int
    current_bbox: BoundingBox
    current_confidence: float
    best_crop_bbox: BoundingBox
    best_crop_confidence: float
    best_crop_frame_idx: int
    trajectory: List[TrajectoryPoint] = Field(default_factory=list)
    color_estimate: Optional[str] = None
    direction_heading_deg: Optional[float] = None
    is_confirmed: bool = True
    ocr_processed: bool = False

    model_config = ConfigDict(from_attributes=True)


class FrameTrackingResult(BaseModel):
    """Multi-object tracking output for an individual video frame."""

    camera_id: str
    frame_index: int
    timestamp_utc: datetime
    active_tracks_count: int
    tracking_latency_ms: float
    tracks: List[TrackedVehicle] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TrackerConfig(BaseModel):
    """Tuning parameters for the ByteTrack multi-object tracking engine."""

    track_thresh: float = Field(
        default=0.45,
        ge=0.1,
        le=0.9,
        description="High-confidence detection threshold for 1st stage",
    )
    high_thresh: float = Field(default=0.60, ge=0.2, le=0.95)
    match_thresh: float = Field(
        default=0.70, ge=0.1, le=0.95, description="IoU threshold for 1st stage association"
    )
    match_thresh_second: float = Field(
        default=0.50, ge=0.1, le=0.95, description="IoU threshold for 2nd stage association"
    )
    max_lost_frames: int = Field(
        default=30, ge=5, le=120, description="Maximum frames to retain track in LOST state"
    )
    min_hits: int = Field(
        default=2, ge=1, le=10, description="Minimum consecutive hits before track is confirmed"
    )

    model_config = ConfigDict(from_attributes=True)


class TrackerTelemetry(BaseModel):
    """Platform-wide multi-object tracking performance and state metrics."""

    total_tracks_created: int
    active_tracks_count: int
    lost_tracks_count: int
    removed_tracks_count: int
    average_tracking_latency_ms: float
    camera_active_counts: Dict[str, int] = Field(default_factory=dict)
    last_tracked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
