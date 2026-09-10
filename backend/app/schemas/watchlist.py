"""Pydantic schemas for Real-Time Watchlist & Hotlist Matching Engine (Module 18)."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.watchlist import WatchlistCategory, WatchlistPriority


class WatchlistBase(BaseModel):
    name: str = Field(
        ..., max_length=150, description="Watchlist name (e.g. 'Stolen Vehicles - Gujarat')"
    )
    description: Optional[str] = Field(None, max_length=255)
    category: str = Field(WatchlistCategory.STOLEN.value)
    is_active: bool = True


class WatchlistCreate(WatchlistBase):
    pass


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class WatchlistResponse(WatchlistBase):
    id: str
    created_by: Optional[str] = None
    entry_count: int = 0
    created_at: datetime
    updated_at: datetime


class WatchlistEntryBase(BaseModel):
    watchlist_id: str
    registration_number: str = Field(
        ..., max_length=50, description="Raw plate string (e.g. 'GJ 01 AB 1234')"
    )
    category: str = Field(WatchlistCategory.STOLEN.value)
    priority: str = Field(WatchlistPriority.HIGH.value)
    is_active: bool = True
    notes: Optional[str] = None


class WatchlistEntryCreate(WatchlistEntryBase):
    registration_normalized: Optional[str] = None


class WatchlistEntryUpdate(BaseModel):
    registration_number: Optional[str] = None
    registration_normalized: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class WatchlistEntryResponse(WatchlistEntryBase):
    id: str
    registration_normalized: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BulkWatchlistImportItem(BaseModel):
    registration_number: str
    category: str = "STOLEN"
    priority: str = "HIGH"
    notes: Optional[str] = None


class BulkWatchlistImportRequest(BaseModel):
    watchlist_name: str = "Imported Police Hotlist"
    category: str = "STOLEN"
    items: List[BulkWatchlistImportItem] = Field(..., min_length=1, max_length=5000)


class BulkWatchlistImportResponse(BaseModel):
    watchlist_id: str
    imported_count: int
    skipped_count: int
    errors: List[str] = Field(default_factory=list)


class WatchlistMatchEvaluationRequest(BaseModel):
    """Payload to evaluate a detected vehicle plate against in-memory hotlists."""

    plate: str = Field(..., description="Observed license plate")
    camera_id: str
    event_id: Optional[str] = None
    confidence: float = Field(0.90, ge=0.0, le=1.0)
    location_name: Optional[str] = ""
    snapshot_path: Optional[str] = None


class WatchlistMatchResult(BaseModel):
    """Result of real-time hotlist evaluation."""

    is_match: bool
    match_type: Optional[str] = None  # EXACT, WILDCARD, FUZZY
    matched_plate: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    alert_generated: bool = False
    alert_id: Optional[str] = None
    evaluation_time_ms: float


class AlertResponse(BaseModel):
    """Dispatched hotlist alert details."""

    id: str
    vehicle_event_id: str
    watchlist_entry_id: Optional[str] = None
    camera_id: str
    registration_number: str
    category: str
    priority: str
    status: str
    alert_time: datetime
    confidence: float
    location_name: str
    snapshot_path: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime


class AlertAcknowledgeRequest(BaseModel):
    """Operator action payload to acknowledge or resolve an alert."""

    operator_name: str = Field(..., description="Name or badge ID of the reviewing police operator")
    status: str = Field("ACKNOWLEDGED", description="ACKNOWLEDGED, RESOLVED, DISMISSED")
    resolution_notes: Optional[str] = None


class WatchlistTelemetry(BaseModel):
    """Real-time hotlist matching throughput and performance metrics."""

    total_evaluations: int
    total_hits: int
    active_watchlist_entries_cached: int
    average_evaluation_time_ms: float
    sub_50ms_compliance_rate: float
    last_evaluation_at: Optional[datetime] = None
