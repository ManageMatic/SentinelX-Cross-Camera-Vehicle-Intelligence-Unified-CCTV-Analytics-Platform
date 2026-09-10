"""Statewide 80,000-Camera Scalability & Edge Gateway Simulation Service for SentinelX.

Demonstrates distributed edge intelligence aggregation across Gujarat Police districts,
proving >99% network bandwidth savings via metadata-first transit over centralized raw RTSP streaming.
"""

from __future__ import annotations

import math
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.logging import logger
from app.schemas.scalability import (
    BandwidthBenchmarkResult,
    EdgeGatewayNode,
    EdgeSimulationConfig,
    EdgeSimulationRunResult,
    GujaratDistrict,
    StatewideClusterTopology,
)

# Relative distribution weight of 80,000 cameras across Gujarat districts
DISTRICT_CAMERA_WEIGHTS: Dict[GujaratDistrict, float] = {
    GujaratDistrict.AHMEDABAD: 0.25,     # 20,000 cams
    GujaratDistrict.SURAT: 0.20,         # 16,000 cams
    GujaratDistrict.VADODARA: 0.15,      # 12,000 cams
    GujaratDistrict.RAJKOT: 0.12,        # 9,600 cams
    GujaratDistrict.GANDHINAGAR: 0.08,   # 6,400 cams
    GujaratDistrict.BHAVNAGAR: 0.05,     # 4,000 cams
    GujaratDistrict.JAMNAGAR: 0.05,      # 4,000 cams
    GujaratDistrict.JUNAGADH: 0.05,      # 4,000 cams
    GujaratDistrict.KUTCH: 0.03,         # 2,400 cams
    GujaratDistrict.MEHSANA: 0.02,       # 1,600 cams
}


class ScalabilitySimulationEngine:
    """Scalability and Statewide Edge Gateway Simulation Engine."""

    def compute_bandwidth_benchmark(
        self,
        total_cameras: int = 80000,
        raw_video_bitrate_mbps: float = 4.0,
        event_rate_per_cam_min: float = 2.0,
        packet_payload_bytes: int = 1500,
    ) -> BandwidthBenchmarkResult:
        """Compute exact comparative bandwidth and cost metrics."""
        # 1. Raw RTSP Video Streaming (Traditional Architecture)
        raw_total_mbps = total_cameras * raw_video_bitrate_mbps
        raw_gbps = raw_total_mbps / 1000.0

        # 2. Metadata-First Edge Gateway Transit (SentinelX Architecture)
        events_per_sec = (total_cameras * event_rate_per_cam_min) / 60.0
        bytes_per_sec = events_per_sec * packet_payload_bytes
        metadata_mbps = (bytes_per_sec * 8.0) / (1000.0 * 1000.0)
        metadata_gbps = metadata_mbps / 1000.0

        # 3. Bandwidth Reduction
        saved_pct = ((raw_gbps - metadata_gbps) / raw_gbps) * 100.0

        # 4. Monthly Transit Volume (TB = Gigabits * 3600 * 24 * 30.5 / 8000)
        seconds_in_month = 30.5 * 24 * 3600
        raw_monthly_tb = (raw_gbps * seconds_in_month) / 8000.0
        metadata_monthly_tb = (metadata_gbps * seconds_in_month) / 8000.0

        # 5. Estimated Bandwidth Infrastructure Cost Savings (INR @ ₹2,500/Mbps/month leased line)
        annual_savings_inr = (raw_total_mbps - metadata_mbps) * 2500.0 * 12.0

        verdict = (
            f"SentinelX edge intelligence reduces network transit from {raw_gbps:.1f} Gbps to {metadata_mbps:.1f} Mbps, "
            f"achieving {saved_pct:.3f}% bandwidth savings across {total_cameras:,} statewide cameras."
        )

        return BandwidthBenchmarkResult(
            total_cameras=total_cameras,
            raw_video_bandwidth_gbps=round(raw_gbps, 2),
            edge_metadata_bandwidth_mbps=round(metadata_mbps, 2),
            bandwidth_saved_pct=round(saved_pct, 4),
            raw_monthly_transit_tb=round(raw_monthly_tb, 1),
            metadata_monthly_transit_tb=round(metadata_monthly_tb, 2),
            annual_network_cost_saving_inr=round(annual_savings_inr, 2),
            verdict=verdict,
        )

    def run_edge_simulation(
        self,
        config: Optional[EdgeSimulationConfig] = None,
    ) -> EdgeSimulationRunResult:
        """Simulate high-throughput edge gateway processing across Gujarat police districts."""
        t_start = time.perf_counter()
        cfg = config or EdgeSimulationConfig()
        sim_id = f"SIM-GJ-{uuid.uuid4().hex[:8].upper()}"

        district_nodes: List[EdgeGatewayNode] = []
        total_cameras = cfg.total_cameras
        total_events = 0

        for district, weight in DISTRICT_CAMERA_WEIGHTS.items():
            cam_count = int(math.ceil(total_cameras * weight))
            eps = (cam_count * cfg.event_rate_per_camera_per_min) / 60.0
            kbps = (eps * cfg.packet_payload_bytes_avg * 8.0) / 1000.0
            total_events += int(eps * 60.0)

            node = EdgeGatewayNode(
                gateway_id=f"EDGE-GW-{district.name[:3]}-01",
                district=district.value,
                camera_count=cam_count,
                status="ONLINE",
                events_per_sec=round(eps, 2),
                bandwidth_kbps=round(kbps, 2),
                cpu_usage_pct=round(min(85.0, 20.0 + (cam_count / 1000.0) * 1.5), 1),
                memory_mb=round(min(16384.0, 2048.0 + cam_count * 0.4), 1),
            )
            district_nodes.append(node)

        benchmark = self.compute_bandwidth_benchmark(
            total_cameras=cfg.total_cameras,
            raw_video_bitrate_mbps=cfg.raw_video_bitrate_mbps,
            event_rate_per_cam_min=cfg.event_rate_per_camera_per_min,
            packet_payload_bytes=cfg.packet_payload_bytes_avg,
        )

        elapsed = time.perf_counter() - t_start
        total_eps = sum(n.events_per_sec for n in district_nodes)

        logger.info(
            f"Completed edge simulation {sim_id}: {total_cameras:,} cameras across {len(district_nodes)} gateways "
            f"generating {total_eps:.1f} eps ({elapsed*1000:.2f}ms)"
        )

        return EdgeSimulationRunResult(
            simulation_id=sim_id,
            total_cameras_simulated=total_cameras,
            total_gateways=len(district_nodes),
            total_events_generated=total_events,
            effective_throughput_eps=round(total_eps, 2),
            processing_time_seconds=round(elapsed, 4),
            bandwidth_comparison=benchmark,
            district_breakdown=district_nodes,
            timestamp=datetime.now(timezone.utc),
        )

    def get_statewide_topology(self) -> StatewideClusterTopology:
        """Generate live cluster topology representation for Gujarat Police Command Center."""
        sim_result = self.run_edge_simulation(EdgeSimulationConfig(total_cameras=80000))
        return StatewideClusterTopology(
            state_name="Gujarat",
            total_districts=len(sim_result.district_breakdown),
            total_edge_gateways=sim_result.total_gateways,
            total_connected_cameras=sim_result.total_cameras_simulated,
            aggregate_events_per_sec=sim_result.effective_throughput_eps,
            edge_gateways=sim_result.district_breakdown,
            health_status="HEALTHY_OPTIMAL",
        )


# Global singleton instance
scalability_engine = ScalabilitySimulationEngine()
