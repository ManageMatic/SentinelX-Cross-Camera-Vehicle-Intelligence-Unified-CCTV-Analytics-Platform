"""Pydantic schemas and dataclasses for Multi-Class Vehicle Detection (Module 10)."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VehicleClass(str, Enum):
    """Standardized vehicle taxonomy for traffic surveillance and ANPR pipelines."""

    CAR = "car"
    MOTORCYCLE = "motorcycle"
    BUS = "bus"
    TRUCK = "truck"
    AUTO_RICKSHAW = "auto_rickshaw"
    VAN = "van"
    UNKNOWN = "unknown"


class BoundingBox(BaseModel):
    """Pixel and normalized bounding box coordinates for a detected vehicle."""

    x1: float = Field(description="Top-left X coordinate in pixels")
    y1: float = Field(description="Top-left Y coordinate in pixels")
    x2: float = Field(description="Bottom-right X coordinate in pixels")
    y2: float = Field(description="Bottom-right Y coordinate in pixels")
    norm_x1: float = Field(description="Normalized top-left X [0.0 - 1.0]")
    norm_y1: float = Field(description="Normalized top-left Y [0.0 - 1.0]")
    norm_x2: float = Field(description="Normalized bottom-right X [0.0 - 1.0]")
    norm_y2: float = Field(description="Normalized bottom-right Y [0.0 - 1.0]")
    width: float = Field(description="Box width in pixels")
    height: float = Field(description="Box height in pixels")

    model_config = ConfigDict(from_attributes=True)


class DetectedVehicle(BaseModel):
    """Normalized object detection record for a vehicle detected in a video frame."""

    detection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    camera_id: str
    frame_index: int
    timestamp_utc: datetime
    vehicle_class: VehicleClass
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence score")
    bbox: BoundingBox
    has_crop: bool = False
    crop_width: Optional[int] = None
    crop_height: Optional[int] = None
    color_estimate: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

    model_config = ConfigDict(from_attributes=True)


class FrameDetectionResult(BaseModel):
    """Aggregated detection inference results for a single video frame."""

    camera_id: str
    frame_index: int
    timestamp_utc: datetime
    inference_time_ms: float
    total_vehicles: int
    vehicles: List[DetectedVehicle] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DetectorConfig(BaseModel):
    """Runtime configuration for the ONNX Runtime / YOLOX vehicle detection engine."""

    model_path: Optional[str] = Field(default=None, description="Path to .onnx model weights")
    confidence_threshold: float = Field(
        default=0.35, ge=0.1, le=1.0, description="Minimum confidence score to accept detection"
    )
    nms_iou_threshold: float = Field(
        default=0.45, ge=0.1, le=0.9, description="IoU threshold for Non-Maximum Suppression"
    )
    input_width: int = Field(default=640, ge=320, le=1280)
    input_height: int = Field(default=640, ge=320, le=1280)
    use_synthetic_detector: bool = Field(
        default=False, description="Force synthetic mock detections for testing and headless CI"
    )
    enabled_classes: List[VehicleClass] = Field(
        default=[
            VehicleClass.CAR,
            VehicleClass.MOTORCYCLE,
            VehicleClass.BUS,
            VehicleClass.TRUCK,
            VehicleClass.AUTO_RICKSHAW,
            VehicleClass.VAN,
        ]
    )

    model_config = ConfigDict(from_attributes=True)


class DetectorTelemetry(BaseModel):
    """Performance telemetry and inference throughput metrics for the vehicle detector."""

    model_name: str
    execution_provider: str
    is_mock: bool
    total_frames_processed: int
    total_vehicles_detected: int
    average_inference_ms: float
    inference_fps: float
    counts_by_class: Dict[str, int] = Field(default_factory=dict)
    last_inference_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
