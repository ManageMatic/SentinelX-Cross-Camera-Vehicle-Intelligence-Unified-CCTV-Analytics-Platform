"""Vehicle Detection Engine REST API Endpoints (Module 10)."""

import uuid
from datetime import datetime, timezone

import cv2
import numpy as np
from app.core.exceptions import ValidationException
from app.schemas.common import APIResponse
from app.schemas.detection import (
    DetectorConfig,
    DetectorTelemetry,
    FrameDetectionResult,
    VehicleClass,
)
from app.schemas.stream import VideoFrame
from app.services.vehicle_detector import vehicle_detector
from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/detection", tags=["AI Vehicle Detection"])


@router.get(
    "/telemetry",
    response_model=APIResponse[DetectorTelemetry],
    summary="Get vehicle detection inference performance telemetry",
)
async def get_detection_telemetry() -> APIResponse[DetectorTelemetry]:
    """Retrieve inference engine stats, execution provider (CUDA/OpenVINO/CPU), FPS, and class breakdown."""
    telemetry = vehicle_detector.get_telemetry()
    return APIResponse(
        success=True,
        message="Vehicle detector telemetry retrieved successfully",
        data=telemetry,
    )


@router.get(
    "/classes",
    response_model=APIResponse[dict],
    summary="Get list of supported vehicle classes in the taxonomy",
)
async def get_supported_vehicle_classes() -> APIResponse[dict]:
    """Return all supported vehicle classification labels."""
    classes = [c.value for c in VehicleClass]
    return APIResponse(
        success=True,
        message="Supported vehicle classes retrieved",
        data={"classes": classes, "total_classes": len(classes)},
    )


@router.post(
    "/configure",
    response_model=APIResponse[DetectorTelemetry],
    summary="Dynamically update vehicle detector configuration",
)
async def configure_vehicle_detector(config: DetectorConfig) -> APIResponse[DetectorTelemetry]:
    """Update confidence thresholds, NMS IoU parameters, input shape, or switch mock mode."""
    vehicle_detector.configure(config)
    telemetry = vehicle_detector.get_telemetry()
    return APIResponse(
        success=True,
        message="Vehicle detector configuration updated successfully",
        data=telemetry,
    )


@router.post(
    "/detect-frame",
    response_model=APIResponse[FrameDetectionResult],
    summary="Execute vehicle detection on an uploaded image file",
)
async def detect_vehicles_in_image(
    file: UploadFile = File(..., description="CCTV snapshot image file (JPEG/PNG)"),
) -> APIResponse[FrameDetectionResult]:
    """Upload a single CCTV image frame and receive localized bounding boxes and vehicle classifications."""
    contents = await file.read()
    if not contents:
        raise ValidationException(detail="Uploaded image file is empty")

    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValidationException(
            detail="Failed to decode image file. Please provide valid JPEG/PNG image."
        )

    h, w = image.shape[:2]
    synthetic_frame = VideoFrame(
        camera_id=f"upload-{uuid.uuid4().hex[:8]}",
        frame_index=1,
        timestamp_utc=datetime.now(timezone.utc),
        image=image,
        width=w,
        height=h,
        fps=25.0,
    )

    result = vehicle_detector.detect(synthetic_frame)
    return APIResponse(
        success=True,
        message=f"Detected {result.total_vehicles} vehicle(s) in {result.inference_time_ms}ms",
        data=result,
    )
