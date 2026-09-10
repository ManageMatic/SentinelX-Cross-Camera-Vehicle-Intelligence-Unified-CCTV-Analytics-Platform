"""Pydantic schemas for Real-time Vehicle Event Ingestion & Indexer (Module 14)."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class VehicleEventCreate(BaseModel):
    """Payload for creating/ingesting a single vehicle intelligence event."""

    camera_id: str = Field(..., description="UUID or identifier of the observing camera")
    event_time: Optional[datetime] = Field(None, description="Detection timestamp (UTC)")
    source_pts: Optional[int] = Field(None, description="Presentation timestamp or frame sequence")
    track_id: Optional[str] = Field(None, description="ByteTrack identity track identifier")

    # ANPR Plate Information
    plate_raw: Optional[str] = Field(None, description="Raw OCR license plate text")
    plate_normalized: Optional[str] = Field(
        None, description="Standardized normalized plate text (e.g. GJ01AB1234)"
    )
    plate_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="ANPR recognition confidence"
    )

    # Vehicle Visual Classification
    vehicle_class: str = Field(
        "car",
        description="Vehicle classification (car, suv, truck, bus, motorcycle, auto_rickshaw)",
    )
    vehicle_color: Optional[str] = Field(None, description="Dominant vehicle color")
    detection_confidence: float = Field(
        0.85, ge=0.0, le=1.0, description="Detection model confidence score"
    )

    # Geospatial Coordinates (Optional; will fallback to camera catalog if omitted)
    latitude: Optional[float] = Field(None, description="WGS84 latitude coordinate")
    longitude: Optional[float] = Field(None, description="WGS84 longitude coordinate")
    location_name: Optional[str] = Field(None, description="Location name / junction / checkpoint")

    # Bounding Box Coordinates [x1, y1, x2, y2]
    bbox_x1: float = Field(0.0, ge=0.0)
    bbox_y1: float = Field(0.0, ge=0.0)
    bbox_x2: float = Field(0.0, ge=0.0)
    bbox_y2: float = Field(0.0, ge=0.0)

    # Visual Snapshot & Evidence
    snapshot_base64: Optional[str] = Field(
        None, description="Base64 encoded JPEG vehicle crop/snapshot"
    )
    snapshot_path: Optional[str] = Field(
        None, description="Existing relative file path to vehicle crop"
    )
    plate_crop_base64: Optional[str] = Field(None, description="Base64 encoded JPEG plate crop")
    plate_crop_path: Optional[str] = Field(
        None, description="Existing relative file path to plate crop"
    )

    # 512-dim Re-ID Vector
    embedding: Optional[List[float]] = Field(
        None, description="512-dimensional L2-normalized visual feature vector"
    )
    embedding_model: str = Field(
        "OSNet-x0.25", description="Re-ID embedding model architecture name"
    )


class VehicleEventBatchCreate(BaseModel):
    """Payload for batch ingesting multiple vehicle events in a single transaction."""

    events: List[VehicleEventCreate] = Field(..., min_length=1, max_length=1000)


class VehiclePlateResponse(BaseModel):
    """License plate candidate representation."""

    id: str
    plate_text: str
    plate_normalized: str
    confidence: float
    crop_path: Optional[str] = None


class VehicleEmbeddingResponse(BaseModel):
    """Visual embedding representation."""

    id: str
    model_name: str
    embedding_dim: int
    vector_sample: Optional[List[float]] = Field(
        None, description="First 8 dimensions for quick inspection"
    )


class VehicleEventResponse(BaseModel):
    """Standard unified vehicle intelligence event response."""

    id: str
    camera_id: str
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

    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float

    snapshot_path: Optional[str] = None
    sha256_hash: Optional[str] = None

    plates: List[VehiclePlateResponse] = Field(default_factory=list)
    has_embedding: bool = False
    created_at: datetime


class EventIndexerTelemetry(BaseModel):
    """Real-time throughput and performance metrics for the event indexer."""

    total_events_ingested: int
    events_per_second: float
    average_ingest_latency_ms: float
    in_memory_ring_buffer_size: int
    total_evidence_files_saved: int
    evidence_storage_bytes: int
    last_event_time: Optional[datetime] = None


class RecentEventsFilter(BaseModel):
    """Query filter parameters for in-memory and recent event lookups."""

    camera_id: Optional[str] = None
    plate_query: Optional[str] = None
    vehicle_class: Optional[str] = None
    limit: int = Field(50, ge=1, le=500)
