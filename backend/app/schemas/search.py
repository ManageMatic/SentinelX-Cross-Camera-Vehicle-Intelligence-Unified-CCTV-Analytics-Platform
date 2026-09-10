"""Pydantic schemas for Sub-200ms Vehicle Search Engine (Module 15)."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VehicleSearchQuery(BaseModel):
    """Multi-criteria search query for vehicle intelligence events."""

    plate: Optional[str] = Field(
        None, description="Exact or wildcard plate query (e.g. 'GJ01AB1234', 'GJ01*', '*1234')"
    )
    fuzzy_plate: bool = Field(
        False, description="Enable Levenshtein / optical similarity fuzzy matching"
    )
    fuzzy_max_distance: int = Field(
        2, ge=1, le=4, description="Max edit distance for fuzzy matching"
    )

    camera_ids: Optional[List[str]] = Field(
        None, description="List of camera UUIDs to restrict search to"
    )
    start_time: Optional[datetime] = Field(None, description="Earliest event timestamp (UTC)")
    end_time: Optional[datetime] = Field(None, description="Latest event timestamp (UTC)")

    vehicle_classes: Optional[List[str]] = Field(
        None, description="List of vehicle classes (e.g. ['car', 'suv', 'truck'])"
    )
    vehicle_colors: Optional[List[str]] = Field(
        None, description="List of dominant colors (e.g. ['white', 'black', 'red'])"
    )

    min_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum detection/plate confidence"
    )
    has_plate_only: bool = Field(
        False, description="If True, only return events with readable license plates"
    )

    # Geospatial Radius Filter
    latitude: Optional[float] = Field(None, description="Center coordinate latitude")
    longitude: Optional[float] = Field(None, description="Center coordinate longitude")
    radius_km: Optional[float] = Field(
        None, ge=0.1, le=100.0, description="Radial search distance in kilometers"
    )

    # Pagination & Ordering
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(50, ge=1, le=500, description="Records per page")
    sort_by: str = Field(
        "event_time",
        description="Sort field ('event_time', 'detection_confidence', 'plate_confidence')",
    )
    sort_order: str = Field("desc", description="Sort direction ('asc', 'desc')")


class FuzzyPlateCandidate(BaseModel):
    """Candidate match returned by fuzzy license plate search."""

    plate_raw: str
    plate_normalized: str
    event_id: str
    camera_id: str
    event_time: datetime
    edit_distance: int
    similarity_score: float
    vehicle_class: str
    vehicle_color: Optional[str] = None
    snapshot_path: Optional[str] = None


class SearchResultItem(BaseModel):
    """Individual vehicle event search result item."""

    id: str
    camera_id: str
    camera_name: Optional[str] = None
    track_id: Optional[str] = None
    event_time: datetime
    source_pts: Optional[int] = None

    plate_raw: Optional[str] = None
    plate_normalized: Optional[str] = None
    plate_confidence: Optional[float] = None

    vehicle_class: str
    vehicle_color: Optional[str] = None
    detection_confidence: float

    latitude: float
    longitude: float
    location_name: str
    distance_km: Optional[float] = None

    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float

    snapshot_path: Optional[str] = None
    has_embedding: bool = False
    match_score: Optional[float] = None


class VehicleSearchResponse(BaseModel):
    """Paginated search response with execution latency tracking."""

    results: List[SearchResultItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    execution_time_ms: float


class SearchTelemetry(BaseModel):
    """Real-time latency and throughput performance metrics for search engine."""

    total_searches_executed: int
    average_search_latency_ms: float
    p95_latency_ms: float
    sub_200ms_compliance_rate: float
    searches_last_minute: int
    top_queried_plates: List[Dict[str, Any]]
