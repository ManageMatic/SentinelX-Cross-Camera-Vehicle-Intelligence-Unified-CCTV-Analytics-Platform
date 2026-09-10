"""Statewide 80,000-Camera Scalability & Edge Gateway Simulation REST API Endpoints for SentinelX."""

from app.schemas.common import APIResponse
from app.schemas.scalability import (
    BandwidthBenchmarkResult,
    EdgeSimulationConfig,
    EdgeSimulationRunResult,
    StatewideClusterTopology,
)
from app.services.scalability_service import scalability_engine
from fastapi import APIRouter, Query

router = APIRouter(prefix="/scalability", tags=["Statewide Scalability & Edge Gateways"])


@router.post(
    "/simulate",
    response_model=APIResponse[EdgeSimulationRunResult],
    summary="Execute statewide edge gateway simulation across Gujarat districts",
)
async def run_simulation(
    payload: EdgeSimulationConfig = EdgeSimulationConfig(),
) -> APIResponse[EdgeSimulationRunResult]:
    """Simulate distributed edge metadata aggregation and measure bandwidth reduction."""
    result = scalability_engine.run_edge_simulation(payload)
    return APIResponse(
        data=result,
        message=f"Simulation completed for {result.total_cameras_simulated:,} cameras ({result.effective_throughput_eps:.1f} events/sec).",
    )


@router.get(
    "/benchmark",
    response_model=APIResponse[BandwidthBenchmarkResult],
    summary="Compute comparative network bandwidth and cost savings analysis",
)
async def get_benchmark(
    cameras: int = Query(80000, ge=1, le=1000000, description="Total cameras to analyze"),
    bitrate_mbps: float = Query(4.0, ge=0.5, le=50.0, description="Raw video bitrate per stream"),
    events_per_min: float = Query(2.0, ge=0.1, le=60.0, description="Vehicle detection events/camera/min"),
) -> APIResponse[BandwidthBenchmarkResult]:
    """Retrieve bandwidth comparative metrics (Raw Video Streaming vs SentinelX Edge Metadata)."""
    benchmark = scalability_engine.compute_bandwidth_benchmark(
        total_cameras=cameras,
        raw_video_bitrate_mbps=bitrate_mbps,
        event_rate_per_cam_min=events_per_min,
    )
    return APIResponse(data=benchmark, message=benchmark.verdict)


@router.get(
    "/topology",
    response_model=APIResponse[StatewideClusterTopology],
    summary="Retrieve Gujarat statewide distributed edge cluster topology",
)
async def get_topology() -> APIResponse[StatewideClusterTopology]:
    """Get active regional gateway nodes and simulated capacity across Gujarat districts."""
    topology = scalability_engine.get_statewide_topology()
    return APIResponse(data=topology, message="Statewide Gujarat edge cluster topology retrieved.")
