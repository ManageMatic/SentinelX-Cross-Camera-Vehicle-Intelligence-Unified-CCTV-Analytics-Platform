"""Chronological Journey & Route Timeline Reconstructor API Endpoints (Module 17)."""

from typing import Any, Dict, List

from app.db.session import get_db
from app.schemas.common import APIResponse
from app.schemas.journey import (
    BehaviorPattern,
    JourneyReconstructRequest,
    JourneyTelemetry,
    JourneyTimeline,
)
from app.services.journey_service import journey_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/journey", tags=["Chronological Journey & Route Timeline Reconstructor"])


@router.post("/reconstruct", response_model=APIResponse[JourneyTimeline])
async def reconstruct_vehicle_journey(
    payload: JourneyReconstructRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[JourneyTimeline]:
    """Reconstruct point-to-point journey history, legs, waypoint stops, behavior patterns, and GIS GeoJSON."""
    timeline = await journey_service.reconstruct_journey(db, payload)
    if not timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No vehicle sightings found matching target query '{payload.plate or payload.event_id}'",
        )
    return APIResponse(
        data=timeline,
        message=f"Reconstructed journey with {len(timeline.waypoints)} waypoints and {len(timeline.legs)} route legs ({len(timeline.behavior_patterns)} behavior anomalies)",
    )


@router.get("/{plate}/geojson", response_model=APIResponse[Dict[str, Any]])
async def get_journey_geojson(
    plate: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, Any]]:
    """Retrieve RFC 7946 GeoJSON FeatureCollection for direct Leaflet / MapLibre visualization."""
    geojson = await journey_service.get_geojson_collection(db, plate)
    if not geojson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No journey route found for license plate '{plate}'",
        )
    return APIResponse(
        data=geojson,
        message=f"Retrieved GeoJSON route for plate '{plate}'",
    )


@router.post("/analyze-behavior", response_model=APIResponse[List[BehaviorPattern]])
async def analyze_journey_behavior(
    payload: JourneyReconstructRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[BehaviorPattern]]:
    """Analyze cruising, circular looping, and stationary loitering behavioral patterns for a vehicle."""
    timeline = await journey_service.reconstruct_journey(db, payload)
    patterns = timeline.behavior_patterns if timeline else []
    return APIResponse(
        data=patterns,
        message=f"Identified {len(patterns)} behavioral anomalies for '{payload.plate or payload.event_id}'",
    )


@router.get("/telemetry", response_model=APIResponse[JourneyTelemetry])
async def get_journey_telemetry() -> APIResponse[JourneyTelemetry]:
    """Retrieve real-time journey reconstruction throughput and behavior detection metrics."""
    telemetry = journey_service.get_telemetry()
    return APIResponse(data=telemetry, message="Journey reconstructor telemetry retrieved")
