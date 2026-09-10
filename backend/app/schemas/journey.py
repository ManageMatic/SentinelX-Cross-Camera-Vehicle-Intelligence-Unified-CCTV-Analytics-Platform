"""Pydantic schemas for Chronological Journey & Route Timeline Reconstructor (Module 17)."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Waypoint(BaseModel):
    """Structured camera observation waypoint in a vehicle's chronological journey."""

    sequence: int = Field(..., description="1-indexed sequence order along route")
    camera_id: str
    camera_name: str
    location_name: str
    coordinates: List[float] = Field(
        ..., description="[longitude, latitude] for GeoJSON compliance"
    )
    arrived_at: datetime
    departed_at: datetime
    dwell_seconds: float = Field(
        ..., description="Dwell / observation duration at this camera node"
    )
    snapshot_path: Optional[str] = None
    plate_reading: Optional[str] = None
    vehicle_class: str
    vehicle_color: Optional[str] = None


class RouteLeg(BaseModel):
    """Transit segment connecting two consecutive camera waypoints."""

    leg_index: int = Field(..., description="1-indexed leg sequence")
    from_camera_id: str
    to_camera_id: str
    from_location: str
    to_location: str
    start_time: datetime
    arrival_time: datetime
    duration_seconds: float
    distance_km: float
    average_speed_kmh: float
    is_speed_anomaly: bool = False


class BehaviorPattern(BaseModel):
    """Analyzed vehicle movement behavior pattern (e.g. loitering, cruising/looping, rapid transit)."""

    pattern_type: str = Field(
        ..., description="LOITERING_DWELL, CIRCULAR_LOOPING_CRUISE, RAPID_TRANSIT"
    )
    severity: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    description: str
    evidence_locations: List[str] = Field(default_factory=list)
    detected_at: datetime


class JourneyTimeline(BaseModel):
    """Complete chronological journey timeline with waypoints, legs, behavior patterns, and GeoJSON."""

    plate_normalized: str
    vehicle_class: str
    vehicle_color: Optional[str] = None
    origin_location: str
    destination_location: str
    first_detected_at: datetime
    last_detected_at: datetime
    total_journey_duration_seconds: float
    total_distance_km: float
    average_journey_speed_kmh: float
    total_stops: int
    waypoints: List[Waypoint]
    legs: List[RouteLeg]
    behavior_patterns: List[BehaviorPattern] = Field(default_factory=list)
    geojson: Dict[str, Any] = Field(..., description="RFC 7946 GeoJSON FeatureCollection")
    reconstructed_at: datetime


class JourneyReconstructRequest(BaseModel):
    """Payload to trigger chronological journey reconstruction."""

    plate: Optional[str] = Field(None, description="License plate to reconstruct journey for")
    event_id: Optional[str] = Field(None, description="Starting event ID")
    start_time: Optional[datetime] = Field(None, description="Earliest timestamp")
    end_time: Optional[datetime] = Field(None, description="Latest timestamp")
    max_dwell_loiter_minutes: float = Field(
        15.0, ge=1.0, le=300.0, description="Dwell threshold to flag loitering"
    )
    loop_detection_window_minutes: float = Field(
        60.0, ge=5.0, le=1440.0, description="Window to detect circular cruising"
    )


class JourneyTelemetry(BaseModel):
    """Telemetry metrics for the journey reconstructor service."""

    total_journeys_reconstructed: int
    total_loops_detected: int
    total_loitering_events_flagged: int
    average_reconstruction_ms: float
    last_reconstruction_at: Optional[datetime] = None
