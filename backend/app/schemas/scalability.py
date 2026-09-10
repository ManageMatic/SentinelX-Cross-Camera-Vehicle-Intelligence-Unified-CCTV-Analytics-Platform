"""Statewide 80,000-Camera Scalability and Edge Gateway Simulation Schemas for SentinelX."""

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class GujaratDistrict(str, Enum):
    """Major administrative police districts across Gujarat State."""
    AHMEDABAD = "Ahmedabad"
    SURAT = "Surat"
    VADODARA = "Vadodara"
    RAJKOT = "Rajkot"
    GANDHINAGAR = "Gandhinagar"
    BHAVNAGAR = "Bhavnagar"
    JAMNAGAR = "Jamnagar"
    JUNAGADH = "Junagadh"
    KUTCH = "Kutch"
    MEHSANA = "Mehsana"


class EdgeGatewayNode(BaseModel):
    """Simulated regional Edge Gateway node aggregating local CCTV streams."""
    gateway_id: str
    district: str
    camera_count: int
    status: str = "ONLINE"
    events_per_sec: float
    bandwidth_kbps: float
    cpu_usage_pct: float
    memory_mb: float


class EdgeSimulationConfig(BaseModel):
    """Configuration parameters for statewide scalability simulation."""
    total_cameras: int = Field(default=80000, ge=1, le=500000, description="Target total cameras (e.g. 80,000)")
    districts_count: int = Field(default=10, ge=1, le=33, description="Number of police districts simulated")
    event_rate_per_camera_per_min: float = Field(default=2.0, ge=0.1, le=60.0, description="Vehicle events detected per camera/min")
    packet_payload_bytes_avg: int = Field(default=1500, ge=100, le=50000, description="Average JSON/Protobuf metadata packet size (Bytes)")
    raw_video_bitrate_mbps: float = Field(default=4.0, ge=0.5, le=25.0, description="Raw 1080p RTSP stream bitrate per camera (Mbps)")


class BandwidthBenchmarkResult(BaseModel):
    """Comparative bandwidth and cost efficiency analysis: Raw Video vs. Metadata-First Edge."""
    total_cameras: int
    raw_video_bandwidth_gbps: float
    edge_metadata_bandwidth_mbps: float
    bandwidth_saved_pct: float
    raw_monthly_transit_tb: float
    metadata_monthly_transit_tb: float
    annual_network_cost_saving_inr: float
    verdict: str


class EdgeSimulationRunResult(BaseModel):
    """Output results of a statewide edge cluster simulation."""
    simulation_id: str
    total_cameras_simulated: int
    total_gateways: int
    total_events_generated: int
    effective_throughput_eps: float
    processing_time_seconds: float
    bandwidth_comparison: BandwidthBenchmarkResult
    district_breakdown: List[EdgeGatewayNode]
    timestamp: datetime


class StatewideClusterTopology(BaseModel):
    """Statewide distributed edge cluster topology and health."""
    state_name: str = "Gujarat"
    total_districts: int
    total_edge_gateways: int
    total_connected_cameras: int
    aggregate_events_per_sec: float
    edge_gateways: List[EdgeGatewayNode]
    health_status: str
