"""Pydantic schemas and dataclasses for Vehicle Appearance Re-ID and Visual Embeddings (Module 13)."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VehicleColor(str, Enum):
    """Dominant Vehicle Color Taxonomy."""

    WHITE = "white"
    BLACK = "black"
    SILVER = "silver"
    GREY = "grey"
    RED = "red"
    BLUE = "blue"
    YELLOW = "yellow"
    GREEN = "green"
    BROWN = "brown"
    ORANGE = "orange"
    OTHER = "other"


class BodyStyle(str, Enum):
    """Vehicle Body Style Classification."""

    SEDAN = "sedan"
    SUV = "suv"
    HATCHBACK = "hatchback"
    MOTORCYCLE = "motorcycle"
    BUS = "bus"
    TRUCK = "truck"
    AUTO_RICKSHAW = "auto_rickshaw"
    VAN = "van"
    UNKNOWN = "unknown"


class VisualEmbeddingResult(BaseModel):
    """512-dimensional visual feature vector and appearance attributes extracted from vehicle crop."""

    embedding: List[float] = Field(
        description="512-dimensional L2-normalized float feature vector (unit sphere norm = 1.0)"
    )
    embedding_dim: int = Field(default=512)
    dominant_color: VehicleColor = VehicleColor.WHITE
    color_confidence: float = Field(ge=0.0, le=1.0, default=0.85)
    secondary_color: Optional[VehicleColor] = None
    body_style: BodyStyle = BodyStyle.SEDAN
    body_style_confidence: float = Field(ge=0.0, le=1.0, default=0.80)
    quality_score: float = Field(
        ge=0.0, le=1.0, description="Visual crop quality score based on sharpness and resolution"
    )
    model_name: str = "OSNet-x0.25-FOSS"
    extraction_time_ms: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class SimilarityMatchResult(BaseModel):
    """Pairwise visual similarity score between two vehicle embeddings."""

    cosine_similarity: float = Field(
        ge=-1.0, le=1.0, description="Cosine similarity score in range [-1.0, 1.0]"
    )
    match_status: str = Field(description="Match rating: HIGH_MATCH, POSSIBLE_MATCH, NO_MATCH")
    is_match: bool = Field(
        description="True if cosine similarity exceeds confidence threshold (>= 0.70)"
    )

    model_config = ConfigDict(from_attributes=True)


class SimilarityComparisonRequest(BaseModel):
    """Request payload comparing two 512-dimensional visual embedding vectors."""

    vector_a: List[float] = Field(description="First 512-dim embedding vector")
    vector_b: List[float] = Field(description="Second 512-dim embedding vector")
    threshold: float = Field(default=0.70, ge=0.0, le=1.0)


class ReIDConfig(BaseModel):
    """Runtime configuration for Re-ID visual embedding extractor."""

    embedding_dim: int = Field(default=512, ge=128, le=1024)
    model_name: str = "OSNet-x0.25-FOSS"
    similarity_threshold: float = Field(default=0.70, ge=0.3, le=0.95)
    use_synthetic_reid: bool = Field(
        default=False, description="Use deterministic synthetic feature extractor for testing"
    )

    model_config = ConfigDict(from_attributes=True)


class ReIDTelemetry(BaseModel):
    """Real-time throughput and performance telemetry for the Re-ID pipeline."""

    model_name: str
    is_mock: bool
    total_embeddings_extracted: int
    average_extraction_ms: float
    extraction_fps: float
    color_distribution: Dict[str, int] = Field(default_factory=dict)
    body_style_distribution: Dict[str, int] = Field(default_factory=dict)
    last_extraction_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
