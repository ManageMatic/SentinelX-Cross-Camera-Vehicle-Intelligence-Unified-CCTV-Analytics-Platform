"""Vehicle Search Engine API Endpoints (Module 15)."""

from typing import List

from app.db.session import get_db
from app.schemas.common import APIResponse
from app.schemas.search import (
    FuzzyPlateCandidate,
    SearchResultItem,
    SearchTelemetry,
    VehicleSearchQuery,
    VehicleSearchResponse,
)
from app.services.search_engine import search_engine
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/search", tags=["Sub-200ms Vehicle Search Engine"])


@router.post("/vehicles", response_model=APIResponse[VehicleSearchResponse])
async def search_vehicle_events(
    query: VehicleSearchQuery,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[VehicleSearchResponse]:
    """Execute multi-criteria indexed search across vehicle events with sub-200ms response time."""
    result = await search_engine.search_vehicles(db, query)
    return APIResponse(
        data=result,
        message=f"Search returned {len(result.results)} records in {result.execution_time_ms}ms",
    )


@router.get("/fuzzy-plate", response_model=APIResponse[List[FuzzyPlateCandidate]])
async def fuzzy_plate_search(
    query: str = Query(..., min_length=2, description="Target partial/distorted plate string"),
    max_distance: int = Query(2, ge=1, le=4, description="Max Levenshtein edit distance"),
    min_similarity: float = Query(
        0.60, ge=0.1, le=1.0, description="Minimum string similarity ratio"
    ),
    limit: int = Query(50, ge=1, le=200, description="Max candidates to return"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[FuzzyPlateCandidate]]:
    """Perform fuzzy search to match occluded, dirty, or misrecognized license plates."""
    candidates = await search_engine.fuzzy_plate_search(
        db, query_str=query, max_distance=max_distance, min_similarity=min_similarity, limit=limit
    )
    return APIResponse(
        data=candidates,
        message=f"Found {len(candidates)} fuzzy matches for plate query '{query}'",
    )


@router.get("/quick-lookup/{plate}", response_model=APIResponse[List[SearchResultItem]])
async def quick_plate_lookup(
    plate: str,
    limit: int = Query(20, ge=1, le=100, description="Max events to return"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[SearchResultItem]]:
    """Sub-50ms instant lookup for exact or normalized license plate string."""
    results = await search_engine.quick_lookup(db, plate_str=plate, limit=limit)
    return APIResponse(
        data=results,
        message=f"Retrieved {len(results)} events for plate '{plate}'",
    )


@router.get("/telemetry", response_model=APIResponse[SearchTelemetry])
async def get_search_telemetry() -> APIResponse[SearchTelemetry]:
    """Retrieve real-time search engine throughput, P95 latency, and sub-200ms compliance metrics."""
    telemetry = search_engine.get_telemetry()
    return APIResponse(data=telemetry, message="Search engine telemetry retrieved")
