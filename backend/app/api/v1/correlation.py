"""Cross-Camera Correlation Engine API Endpoints (Module 16)."""

from typing import List

from app.db.session import get_db
from app.schemas.common import APIResponse
from app.schemas.correlation import (
    CloneDetectionRequest,
    ClonedPlateAnomaly,
    CorrelationRequest,
    CorrelationResult,
    CorrelationTelemetry,
    VisualMatchCandidate,
    VisualMatchRequest,
)
from app.services.correlation_engine import correlation_engine
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/correlation", tags=["Cross-Camera Correlation Engine"])


@router.post("/correlate", response_model=APIResponse[CorrelationResult])
async def correlate_vehicle_sightings(
    payload: CorrelationRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CorrelationResult]:
    """Reconstruct multi-camera vehicle journey, evaluate transit plausibility, and flag impossible speed hops."""
    result = await correlation_engine.correlate_vehicle(db, payload)
    return APIResponse(
        data=result,
        message=f"Correlated {result.total_sightings} sightings across {result.unique_cameras} cameras ({result.anomalies_detected} anomalies)",
    )


@router.post("/detect-clones", response_model=APIResponse[List[ClonedPlateAnomaly]])
async def detect_cloned_plates(
    payload: CloneDetectionRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ClonedPlateAnomaly]]:
    """Scan active surveillance window to identify cloned or duplicated vehicle plates across the city."""
    anomalies = await correlation_engine.detect_cloned_plates(db, payload)
    return APIResponse(
        data=anomalies,
        message=f"Identified {len(anomalies)} suspected cloned plate anomalies across surveillance network",
    )


@router.post("/visual-match", response_model=APIResponse[List[VisualMatchCandidate]])
async def visual_match_embeddings(
    payload: VisualMatchRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[VisualMatchCandidate]]:
    """Cross-camera vehicle visual matching using 512-dim Re-ID embeddings."""
    candidates = await correlation_engine.visual_match(db, payload)
    return APIResponse(
        data=candidates,
        message=f"Found {len(candidates)} visual Re-ID matching vehicles",
    )


@router.get("/telemetry", response_model=APIResponse[CorrelationTelemetry])
async def get_correlation_telemetry() -> APIResponse[CorrelationTelemetry]:
    """Retrieve real-time correlation throughput, anomaly counts, and processing latency."""
    telemetry = correlation_engine.get_telemetry()
    return APIResponse(data=telemetry, message="Correlation engine telemetry retrieved")
