"""Vehicle Appearance Re-ID & Visual Embedding REST API Endpoints (Module 13)."""

import cv2
import numpy as np
from app.core.exceptions import ValidationException
from app.schemas.common import APIResponse
from app.schemas.reid import (
    ReIDConfig,
    ReIDTelemetry,
    SimilarityComparisonRequest,
    SimilarityMatchResult,
    VisualEmbeddingResult,
)
from app.services.reid_engine import reid_engine
from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/reid", tags=["Vehicle Re-ID & Visual Embeddings"])


@router.get(
    "/telemetry",
    response_model=APIResponse[ReIDTelemetry],
    summary="Get vehicle appearance Re-ID performance telemetry",
)
async def get_reid_telemetry() -> APIResponse[ReIDTelemetry]:
    """Retrieve embedding extraction FPS, average latency, and color/body style distributions."""
    telemetry = reid_engine.get_telemetry()
    return APIResponse(
        success=True,
        message="Re-ID telemetry retrieved successfully",
        data=telemetry,
    )


@router.post(
    "/extract",
    response_model=APIResponse[VisualEmbeddingResult],
    summary="Extract 512-dim visual embedding and appearance attributes from vehicle crop",
)
async def extract_vehicle_embedding(
    file: UploadFile = File(..., description="Vehicle snapshot crop image (JPEG/PNG)"),
) -> APIResponse[VisualEmbeddingResult]:
    """Upload a localized vehicle crop image to extract L2-normalized 512-dim feature vector and color/body attributes."""
    contents = await file.read()
    if not contents:
        raise ValidationException(detail="Uploaded vehicle crop file is empty")

    nparr = np.frombuffer(contents, np.uint8)
    crop = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if crop is None:
        raise ValidationException(
            detail="Failed to decode crop image. Please provide a valid JPEG/PNG file."
        )

    result = reid_engine.extract_embedding(crop)
    return APIResponse(
        success=True,
        message=f"Extracted 512-dim embedding ({result.dominant_color.value} {result.body_style.value}) in {result.extraction_time_ms}ms",
        data=result,
    )


@router.post(
    "/similarity",
    response_model=APIResponse[SimilarityMatchResult],
    summary="Compute cosine similarity between two 512-dim visual feature vectors",
)
async def compare_visual_embeddings(
    payload: SimilarityComparisonRequest,
) -> APIResponse[SimilarityMatchResult]:
    """Calculate cosine similarity and match confidence between two vehicle feature vectors."""
    if len(payload.vector_a) != len(payload.vector_b):
        raise ValidationException(
            detail=f"Vector dimension mismatch: vector_a has {len(payload.vector_a)} dimensions, vector_b has {len(payload.vector_b)}"
        )

    match_result = reid_engine.compare_embeddings(
        payload.vector_a, payload.vector_b, threshold=payload.threshold
    )
    return APIResponse(
        success=True,
        message=f"Cosine similarity: {match_result.cosine_similarity} (Match: {match_result.match_status})",
        data=match_result,
    )


@router.post(
    "/configure",
    response_model=APIResponse[ReIDTelemetry],
    summary="Dynamically update Re-ID engine configuration",
)
async def configure_reid_engine(config: ReIDConfig) -> APIResponse[ReIDTelemetry]:
    """Update Re-ID embedding model name, similarity thresholds, or synthetic testing mode."""
    reid_engine.configure(config)
    telemetry = reid_engine.get_telemetry()
    return APIResponse(
        success=True,
        message="Re-ID configuration updated successfully",
        data=telemetry,
    )
