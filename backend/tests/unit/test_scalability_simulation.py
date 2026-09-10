"""Comprehensive Unit Tests for Statewide 80,000-Camera Scalability & Edge Simulation (Module 24)."""

import pytest
from app.main import app
from app.schemas.scalability import EdgeSimulationConfig
from app.services.scalability_service import scalability_engine
from httpx import ASGITransport, AsyncClient


def test_bandwidth_benchmark_calculation():
    """Test mathematical verification of >99% bandwidth reduction for 80,000 cameras."""
    benchmark = scalability_engine.compute_bandwidth_benchmark(
        total_cameras=80000,
        raw_video_bitrate_mbps=4.0,
        event_rate_per_cam_min=2.0,
        packet_payload_bytes=1500,
    )

    # 1. 80,000 streams * 4 Mbps = 320 Gbps raw video
    assert benchmark.total_cameras == 80000
    assert benchmark.raw_video_bandwidth_gbps == 320.0

    # 2. Metadata transit should be sub-50 Mbps
    assert benchmark.edge_metadata_bandwidth_mbps < 50.0

    # 3. Bandwidth savings must exceed 99.9%
    assert benchmark.bandwidth_saved_pct >= 99.9
    assert benchmark.annual_network_cost_saving_inr > 1_000_000_000.0  # > ₹100 Crores
    assert "99." in benchmark.verdict


def test_edge_simulation_run_across_districts():
    """Test statewide simulation across all 10 major Gujarat police districts."""
    config = EdgeSimulationConfig(
        total_cameras=80000,
        event_rate_per_camera_per_min=2.0,
    )
    result = scalability_engine.run_edge_simulation(config)

    assert result.simulation_id.startswith("SIM-GJ-")
    assert result.total_cameras_simulated == 80000
    assert result.total_gateways == 10
    assert result.effective_throughput_eps >= 2500.0
    assert result.processing_time_seconds < 1.0  # Sub-second simulation execution

    # District validation
    districts = {gw.district for gw in result.district_breakdown}
    assert "Ahmedabad" in districts
    assert "Surat" in districts
    assert "Vadodara" in districts
    assert "Rajkot" in districts
    assert "Gandhinagar" in districts

    for gw in result.district_breakdown:
        assert gw.camera_count > 0
        assert gw.events_per_sec > 0
        assert gw.status == "ONLINE"
        assert 0.0 < gw.cpu_usage_pct <= 100.0


def test_statewide_cluster_topology():
    """Test statewide Gujarat Police Command Center cluster topology model."""
    topology = scalability_engine.get_statewide_topology()

    assert topology.state_name == "Gujarat"
    assert topology.total_connected_cameras == 80000
    assert topology.total_districts == 10
    assert topology.health_status == "HEALTHY_OPTIMAL"
    assert len(topology.edge_gateways) == 10


@pytest.mark.asyncio
async def test_scalability_rest_api_endpoints():
    """Test full REST API integration for Scalability and Edge Gateway endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Post Simulation Endpoint
        sim_resp = await client.post(
            "/api/v1/scalability/simulate",
            json={"total_cameras": 50000, "raw_video_bitrate_mbps": 4.0},
        )
        assert sim_resp.status_code == 200
        sim_data = sim_resp.json()["data"]
        assert sim_data["total_cameras_simulated"] == 50000
        assert sim_data["bandwidth_comparison"]["bandwidth_saved_pct"] >= 99.9

        # 2. Get Benchmark Endpoint
        bm_resp = await client.get("/api/v1/scalability/benchmark?cameras=80000&bitrate_mbps=4.0")
        assert bm_resp.status_code == 200
        assert bm_resp.json()["data"]["raw_video_bandwidth_gbps"] == 320.0

        # 3. Get Topology Endpoint
        topo_resp = await client.get("/api/v1/scalability/topology")
        assert topo_resp.status_code == 200
        assert topo_resp.json()["data"]["total_districts"] == 10
