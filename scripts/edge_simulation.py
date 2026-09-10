"""Standalone CLI Simulation Script for Gujarat Statewide 80,000-Camera Scalability.

Usage:
    python scripts/edge_simulation.py [--cameras 80000] [--bitrate 4.0]
"""

import argparse
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas.scalability import EdgeSimulationConfig
from app.services.scalability_service import scalability_engine


def main() -> None:
    parser = argparse.ArgumentParser(description="SentinelX 80,000-Camera Statewide Scalability & Edge Simulator")
    parser.add_argument("--cameras", type=int, default=80000, help="Total camera feeds to simulate (default: 80000)")
    parser.add_argument("--bitrate", type=float, default=4.0, help="Raw 1080p RTSP stream bitrate in Mbps (default: 4.0)")
    parser.add_argument("--event-rate", type=float, default=2.0, help="Vehicle events per camera per min (default: 2.0)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")

    args = parser.parse_args()

    config = EdgeSimulationConfig(
        total_cameras=args.cameras,
        raw_video_bitrate_mbps=args.bitrate,
        event_rate_per_camera_per_min=args.event_rate,
    )

    result = scalability_engine.run_edge_simulation(config)
    bm = result.bandwidth_comparison

    if args.json:
        print(json.dumps(result.model_dump(), indent=2, default=str))
        return

    print("=" * 78)
    print(" SENTINELX — STATEWIDE 80,000-CAMERA EDGE GATEWAY SCALABILITY BENCHMARK")
    print(" Gujarat Police Innovation Challenge 2026")
    print("=" * 78)
    print(f" Simulation ID       : {result.simulation_id}")
    print(f" Total Cameras       : {result.total_cameras_simulated:,}")
    print(f" Edge Gateway Nodes  : {result.total_gateways} Regional Districts")
    print(f" Effective EPS       : {result.effective_throughput_eps:,.1f} events/sec")
    print(f" Processing Time     : {result.processing_time_seconds * 1000:.2f} ms")
    print("-" * 78)
    print(" BANDWIDTH & DATA EFFICIENCY COMPARISON:")
    print(f"  [1] Centralized Raw RTSP Video Streaming : {bm.raw_video_bandwidth_gbps:,.1f} Gbps ({bm.raw_monthly_transit_tb:,.0f} TB/month)")
    print(f"  [2] SentinelX Edge Metadata-First Transit: {bm.edge_metadata_bandwidth_mbps:,.1f} Mbps ({bm.metadata_monthly_transit_tb:,.2f} TB/month)")
    print(f"  [*] Network Bandwidth Reduction          : {bm.bandwidth_saved_pct:.3f}% SAVED")
    print(f"  [*] Estimated Annual Network Cost Savings: Rs. {bm.annual_network_cost_saving_inr / 10000000.0:,.2f} Crores INR")
    print("-" * 78)
    print(" DISTRICT-WISE EDGE GATEWAY BREAKDOWN:")
    for gw in result.district_breakdown:
        print(f"  * {gw.district:<15} | Cams: {gw.camera_count:>6,} | Events/s: {gw.events_per_sec:>6.1f} | Bandwidth: {gw.bandwidth_kbps:>7.1f} Kbps | CPU: {gw.cpu_usage_pct:>4.1f}%")
    print("=" * 78)


if __name__ == "__main__":
    main()
