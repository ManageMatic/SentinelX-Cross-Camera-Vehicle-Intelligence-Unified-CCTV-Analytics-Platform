"""ANPR Engine & Indian License Plate Normalizer REST API Endpoints (Module 12)."""

import cv2
import numpy as np
from app.core.exceptions import ValidationException
from app.schemas.anpr import (
    ANPRConfig,
    ANPRResult,
    ANPRTelemetry,
)
from app.schemas.common import APIResponse
from app.services.anpr_engine import INDIAN_STATE_CODES, anpr_engine
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel, Field

router = APIRouter(prefix="/anpr", tags=["ANPR & Plate Recognition"])


class NormalizePlateRequest(BaseModel):
    """Raw license plate string normalization payload."""

    raw_text: str = Field(
        description="Raw text output from OCR or operator input", examples=["GJ 01 AB 1234"]
    )
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)


@router.get(
    "/telemetry",
    response_model=APIResponse[ANPRTelemetry],
    summary="Get ANPR engine recognition throughput and accuracy telemetry",
)
async def get_anpr_telemetry() -> APIResponse[ANPRTelemetry]:
    """Retrieve ANPR performance metrics, syntax validity percentage, and state breakdown."""
    telemetry = anpr_engine.get_telemetry()
    return APIResponse(
        success=True,
        message="ANPR telemetry retrieved successfully",
        data=telemetry,
    )


@router.get(
    "/states",
    response_model=APIResponse[dict],
    summary="Get list of supported Indian State and Union Territory codes",
)
async def get_supported_indian_states() -> APIResponse[dict]:
    """Return all 36 supported Indian State / UT codes under MoRTH vehicle registration standards."""
    states_list = sorted(list(INDIAN_STATE_CODES))
    return APIResponse(
        success=True,
        message="Supported Indian state codes retrieved",
        data={"states": states_list, "total_states": len(states_list)},
    )


@router.post(
    "/normalize-text",
    response_model=APIResponse[ANPRResult],
    summary="Normalize and validate a raw Indian license plate string",
)
async def normalize_plate_string(payload: NormalizePlateRequest) -> APIResponse[ANPRResult]:
    """Clean, disambiguate characters (e.g. O->0 in numbers, 0->O in state code), and format plate for DB search."""
    if not payload.raw_text.strip():
        raise ValidationException(detail="License plate text cannot be empty")

    result = anpr_engine.normalize_plate(payload.raw_text, confidence=payload.confidence)
    return APIResponse(
        success=True,
        message=f"Normalized plate: {result.plate_normalized} (Syntax Valid: {result.is_valid_syntax})",
        data=result,
    )


@router.post(
    "/recognize-crop",
    response_model=APIResponse[ANPRResult],
    summary="Run OCR recognition on an uploaded vehicle or plate crop image",
)
async def recognize_plate_from_crop(
    file: UploadFile = File(..., description="Vehicle crop image file (JPEG/PNG)"),
) -> APIResponse[ANPRResult]:
    """Upload a vehicle snapshot crop and extract normalized Indian license plate registration."""
    contents = await file.read()
    if not contents:
        raise ValidationException(detail="Uploaded image crop is empty")

    nparr = np.frombuffer(contents, np.uint8)
    crop = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if crop is None:
        raise ValidationException(
            detail="Failed to decode crop image. Please upload a valid JPEG/PNG."
        )

    result = anpr_engine.recognize_crop(crop, camera_id="manual-upload")
    return APIResponse(
        success=True,
        message=f"Recognized plate '{result.plate_normalized}' in {result.processing_time_ms}ms",
        data=result,
    )


@router.post(
    "/configure",
    response_model=APIResponse[ANPRTelemetry],
    summary="Dynamically update ANPR configuration parameters",
)
async def configure_anpr_engine(config: ANPRConfig) -> APIResponse[ANPRTelemetry]:
    """Update CLAHE enhancement, character disambiguation policies, or target states."""
    anpr_engine.configure(config)
    telemetry = anpr_engine.get_telemetry()
    return APIResponse(
        success=True,
        message="ANPR configuration updated successfully",
        data=telemetry,
    )
