"""Pydantic schemas and dataclasses for ANPR and Indian License Plate Normalization (Module 12)."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.detection import BoundingBox


class PlateCategory(str, Enum):
    """Indian License Plate Category Taxonomy."""

    STANDARD = "STANDARD"  # Private white plate (e.g. GJ01AB1234)
    BHARAT_SERIES = "BHARAT_SERIES"  # BH series (e.g. 22BH1234AA)
    COMMERCIAL = "COMMERCIAL"  # Yellow plate (commercial taxi/truck/bus)
    ELECTRIC = "ELECTRIC"  # Green plate (EV)
    DIPLOMATIC = "DIPLOMATIC"  # Blue plate (UN / CD)
    MILITARY = "MILITARY"  # Upward arrow prefix
    TEMPORARY = "TEMPORARY"  # Yellow text on red plate
    UNKNOWN = "UNKNOWN"


class ANPRResult(BaseModel):
    """Recognized and normalized Indian license plate record."""

    plate_raw: str = Field(description="Raw OCR output string before normalization")
    plate_normalized: str = Field(
        description="Cleaned, normalized alphanumeric plate string formatted for DB indexing"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="ANPR recognition confidence score")
    category: PlateCategory = PlateCategory.STANDARD
    state_code: Optional[str] = Field(
        default=None, description="2-letter Indian state code (e.g. GJ, MH)"
    )
    district_code: Optional[str] = Field(
        default=None, description="RTO district numeric code (e.g. 01, 18)"
    )
    series: Optional[str] = Field(default=None, description="Vehicle series letters (e.g. AB, CG)")
    number: Optional[str] = Field(
        default=None, description="4-digit vehicle registration number (e.g. 1234)"
    )
    is_valid_syntax: bool = Field(
        default=False,
        description="True if plate conforms strictly to Indian MORTH / MoRTH syntax standards",
    )
    processing_time_ms: float = 0.0
    plate_bbox: Optional[BoundingBox] = None

    model_config = ConfigDict(from_attributes=True)


class ANPRBatchResult(BaseModel):
    """Batch ANPR recognition outputs for a frame or group of vehicle crops."""

    camera_id: str
    frame_index: int
    timestamp_utc: datetime
    total_plates_recognized: int
    processing_time_ms: float
    plates: List[ANPRResult] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ANPRConfig(BaseModel):
    """Runtime configuration for ANPR OCR and normalization engine."""

    confidence_threshold: float = Field(default=0.45, ge=0.1, le=1.0)
    enable_clahe_enhancement: bool = Field(
        default=True,
        description="Apply Contrast Limited Adaptive Histogram Equalization for nighttime feeds",
    )
    enable_character_correction: bool = Field(
        default=True,
        description="Position-aware OCR disambiguation (e.g. O->0 in numbers, 0->O in state code)",
    )
    use_synthetic_anpr: bool = Field(
        default=False,
        description="Use synthetic realistic Indian plate generator for headless CI/CD",
    )
    target_states: List[str] = Field(
        default=["GJ", "MH", "DL", "RJ", "MP", "KA", "TN", "UP", "HR", "PB", "AP", "TS", "KL", "WB"]
    )

    model_config = ConfigDict(from_attributes=True)


class ANPRTelemetry(BaseModel):
    """Real-time throughput and accuracy metrics for the ANPR pipeline."""

    engine_name: str
    is_mock: bool
    total_plates_processed: int
    valid_syntax_count: int
    syntax_validity_rate_pct: float
    average_ocr_ms: float
    ocr_fps: float
    counts_by_category: Dict[str, int] = Field(default_factory=dict)
    counts_by_state: Dict[str, int] = Field(default_factory=dict)
    last_ocr_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
