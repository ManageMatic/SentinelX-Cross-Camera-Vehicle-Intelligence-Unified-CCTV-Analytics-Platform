"""Pydantic schemas for Cross-Camera Correlation Engine & Spatial-Temporal Filter (Module 16)."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class CorrelationPlausibility(str, Enum):
    """Plausibility evaluation status for cross-camera vehicle movement."""

    PLAUSIBLE = "PLAUSIBLE"
    SUSPICIOUS_SPEED = "SUSPICIOUS_SPEED"
    IMPOSSIBLE_TELEPORT = "IMPOSSIBLE_TELEPORT"
    SIMULTANEOUS_CLONE = "SIMULTANEOUS_CLONE"
    REID_MATCH = "REID_MATCH"


class CameraSightingNode(BaseModel):
    """Clustered vehicle sighting at a specific camera node."""

    camera_id: str
    camera_name: str
    location_name: str
    latitude: float
    longitude: float
    first_seen: datetime
    last_seen: datetime
    dwell_time_seconds: float
    event_count: int
    plate_raw: Optional[str] = None
    plate_normalized: Optional[str] = None
    vehicle_class: str
    vehicle_color: Optional[str] = None
    best_snapshot_path: Optional[str] = None
    has_embedding: bool = False
    event_ids: List[str] = Field(default_factory=list)


class SightingHop(BaseModel):
    """Movement hop between two consecutive camera sightings."""

    from_camera_id: str
    to_camera_id: str
    from_location: str
    to_location: str
    distance_km: float
    transit_duration_seconds: float
    transit_speed_kmh: float
    plausibility: CorrelationPlausibility
    plausibility_reason: str


class CorrelationRequest(BaseModel):
    """Request payload to correlate multi-camera vehicle sightings."""

    plate: Optional[str] = Field(None, description="License plate to track across cameras")
    event_id: Optional[str] = Field(None, description="Target vehicle event UUID")
    embedding: Optional[List[float]] = Field(
        None, description="512-dim visual Re-ID embedding vector"
    )

    start_time: Optional[datetime] = Field(None, description="Earliest timestamp to search")
    end_time: Optional[datetime] = Field(None, description="Latest timestamp to search")

    max_speed_kmh: float = Field(
        160.0, ge=40.0, le=300.0, description="Speed threshold for impossible teleport filter"
    )
    min_reid_similarity: float = Field(
        0.70, ge=0.4, le=1.0, description="Minimum cosine similarity for visual Re-ID"
    )
    cluster_dwell_seconds: float = Field(
        30.0, ge=5.0, le=300.0, description="Max time gap to merge detections into one node"
    )


class CorrelationResult(BaseModel):
    """Unified multi-camera correlation graph with hops and spatial-temporal plausibility."""

    target_query: str
    total_sightings: int
    unique_cameras: int
    total_journey_distance_km: float
    total_journey_duration_seconds: float
    nodes: List[CameraSightingNode]
    hops: List[SightingHop]
    anomalies_detected: int
    is_cloned_plate_suspected: bool
    execution_time_ms: float


class CloneDetectionRequest(BaseModel):
    """Request parameters for network-wide cloned plate detection."""

    time_window_minutes: int = Field(
        60, ge=5, le=1440, description="Time window to evaluate for simultaneous sightings"
    )
    min_distance_km: float = Field(
        5.0, ge=1.0, le=500.0, description="Minimum distance between cameras to flag as anomaly"
    )
    max_plausible_speed_kmh: float = Field(160.0, ge=60.0, le=300.0)


class ClonedPlateAnomaly(BaseModel):
    """Detailed anomaly record for a cloned / spoofed license plate."""

    plate_normalized: str
    sighting_a: CameraSightingNode
    sighting_b: CameraSightingNode
    time_delta_seconds: float
    distance_km: float
    implied_speed_kmh: float
    anomaly_type: str = "IMPOSSIBLE_TRANSIT_SPEED"
    flagged_at: datetime


class VisualMatchRequest(BaseModel):
    """Payload for finding cross-camera visual matches via 512-dim embedding."""

    embedding: List[float] = Field(..., min_length=128, max_length=1024)
    min_similarity: float = Field(0.75, ge=0.5, le=1.0)
    limit: int = Field(20, ge=1, le=100)


class VisualMatchCandidate(BaseModel):
    """Matching vehicle event candidate identified through visual Re-ID."""

    event_id: str
    camera_id: str
    location_name: str
    event_time: datetime
    cosine_similarity: float
    vehicle_class: str
    vehicle_color: Optional[str] = None
    plate_normalized: Optional[str] = None
    snapshot_path: Optional[str] = None


class CorrelationTelemetry(BaseModel):
    """Real-time performance and anomaly tracking telemetry for correlation engine."""

    total_correlations_executed: int
    total_anomalies_flagged: int
    cloned_plates_identified: int
    average_correlation_time_ms: float
    last_correlation_at: Optional[datetime] = None
