"""Cross-Camera Correlation Engine & Spatial-Temporal Filter Service (Module 16).

Reconstructs multi-camera vehicle journeys, filters out physically impossible teleports,
and detects cloned/spoofed license plates across CCTV networks.
"""

import json
import logging
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import VehicleEmbedding, VehicleEvent
from app.schemas.correlation import (
    CameraSightingNode,
    CloneDetectionRequest,
    ClonedPlateAnomaly,
    CorrelationPlausibility,
    CorrelationRequest,
    CorrelationResult,
    CorrelationTelemetry,
    SightingHop,
    VisualMatchCandidate,
    VisualMatchRequest,
)
from app.services.search_engine import haversine_distance_km

logger = logging.getLogger("sentinelx.correlation")


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class CrossCameraCorrelationEngine:
    """Flagship engine for cross-camera vehicle tracking, plausibility validation, and clone detection."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_correlations: int = 0
        self._total_anomalies: int = 0
        self._cloned_plates_caught: int = 0
        self._latency_samples: deque[float] = deque(maxlen=200)
        self._last_correlation_at: Optional[datetime] = None

    def _cluster_events_into_nodes(
        self, events: List[VehicleEvent], cluster_dwell_seconds: float
    ) -> List[CameraSightingNode]:
        """Cluster raw event detections on the same camera within dwell window into single sighting nodes."""
        if not events:
            return []

        nodes: List[CameraSightingNode] = []
        current_node_events: List[VehicleEvent] = [events[0]]

        for ev in events[1:]:
            prev_ev = current_node_events[-1]
            same_camera = ev.camera_id == prev_ev.camera_id
            gap_seconds = (ev.event_time - prev_ev.event_time).total_seconds()

            if same_camera and abs(gap_seconds) <= cluster_dwell_seconds:
                current_node_events.append(ev)
            else:
                # Seal current node
                nodes.append(self._build_sighting_node(current_node_events))
                current_node_events = [ev]

        if current_node_events:
            nodes.append(self._build_sighting_node(current_node_events))

        return nodes

    @staticmethod
    def _build_sighting_node(events: List[VehicleEvent]) -> CameraSightingNode:
        """Convert a clustered list of events into a CameraSightingNode."""
        first_ev = events[0]
        last_ev = events[-1]

        cam_name = first_ev.camera.name if first_ev.camera else f"Camera {first_ev.camera_id[:8]}"
        dwell = max(0.0, (last_ev.event_time - first_ev.event_time).total_seconds())

        # Select best snapshot (prefer non-empty snapshot)
        best_snap = None
        for ev in events:
            if ev.snapshot_path:
                best_snap = ev.snapshot_path
                break

        return CameraSightingNode(
            camera_id=first_ev.camera_id,
            camera_name=cam_name,
            location_name=first_ev.location_name,
            latitude=first_ev.latitude,
            longitude=first_ev.longitude,
            first_seen=first_ev.event_time,
            last_seen=last_ev.event_time,
            dwell_time_seconds=round(dwell, 1),
            event_count=len(events),
            plate_raw=first_ev.plate_raw,
            plate_normalized=first_ev.plate_normalized,
            vehicle_class=first_ev.vehicle_class,
            vehicle_color=first_ev.vehicle_color,
            best_snapshot_path=best_snap,
            has_embedding=any(e.embedding is not None for e in events),
            event_ids=[e.id for e in events],
        )

    async def correlate_vehicle(
        self, db: AsyncSession, req: CorrelationRequest
    ) -> CorrelationResult:
        """Reconstruct multi-camera journey for a target plate, event, or Re-ID vector."""
        start_t = time.perf_counter()
        now_utc = datetime.now(timezone.utc)

        target_str = req.plate or req.event_id or "Visual-Embedding-Query"

        # 1. Fetch raw sightings matching plate or event_id
        stmt = select(VehicleEvent)
        filters = []

        if req.plate:
            p_clean = req.plate.strip().upper().replace(" ", "")
            filters.append(
                or_(
                    VehicleEvent.plate_normalized == p_clean,
                    VehicleEvent.plate_raw == p_clean,
                )
            )
        elif req.event_id:
            # First fetch target event to extract plate or embedding
            t_res = await db.execute(select(VehicleEvent).where(VehicleEvent.id == req.event_id))
            target_ev = t_res.scalar_one_or_none()
            if target_ev and target_ev.plate_normalized:
                filters.append(VehicleEvent.plate_normalized == target_ev.plate_normalized)
            elif target_ev:
                filters.append(VehicleEvent.id == target_ev.id)

        if req.start_time:
            filters.append(VehicleEvent.event_time >= req.start_time)
        if req.end_time:
            filters.append(VehicleEvent.event_time <= req.end_time)

        if filters:
            stmt = stmt.where(*filters)

        stmt = stmt.order_by(VehicleEvent.event_time.asc())
        res = await db.execute(stmt)
        raw_events = list(res.scalars().all())

        # 2. Cluster raw events into CameraSightingNodes
        nodes = self._cluster_events_into_nodes(raw_events, req.cluster_dwell_seconds)

        # 3. Compute Consecutive Sighting Hops and Spatial-Temporal Plausibility
        hops: List[SightingHop] = []
        anomalies_count = 0
        cloned_suspected = False
        total_dist_km = 0.0

        for i in range(len(nodes) - 1):
            n1 = nodes[i]
            n2 = nodes[i + 1]

            dist_km = haversine_distance_km(n1.latitude, n1.longitude, n2.latitude, n2.longitude)
            total_dist_km += dist_km

            # Time delta between leaving node 1 and entering node 2
            duration_sec = (n2.first_seen - n1.last_seen).total_seconds()
            if duration_sec <= 0:
                duration_sec = max(1.0, (n2.first_seen - n1.first_seen).total_seconds())

            # Implied speed in km/h
            speed_kmh = (dist_km / max(1.0, duration_sec)) * 3600.0

            # Spatial-Temporal Plausibility Rules
            if n1.camera_id != n2.camera_id and duration_sec < 60.0 and dist_km > 3.0:
                plausibility = CorrelationPlausibility.SIMULTANEOUS_CLONE
                reason = (
                    f"Simultaneous sighting on distant cameras ({dist_km:.2f} km in {duration_sec:.0f}s). "
                    "Cloned / duplicate license plate suspected."
                )
                anomalies_count += 1
                cloned_suspected = True
            elif speed_kmh > req.max_speed_kmh * 1.5 and dist_km > 1.0:
                plausibility = CorrelationPlausibility.IMPOSSIBLE_TELEPORT
                reason = (
                    f"Implied transit speed of {speed_kmh:.1f} km/h is physically impossible "
                    f"over {dist_km:.2f} km in {duration_sec:.0f}s."
                )
                anomalies_count += 1
            elif speed_kmh > req.max_speed_kmh:
                plausibility = CorrelationPlausibility.SUSPICIOUS_SPEED
                reason = (
                    f"High speed transit detected ({speed_kmh:.1f} km/h over {dist_km:.2f} km)."
                )
                anomalies_count += 1
            else:
                plausibility = CorrelationPlausibility.PLAUSIBLE
                reason = (
                    f"Normal plausible transit at {speed_kmh:.1f} km/h across {dist_km:.2f} km."
                )

            hops.append(
                SightingHop(
                    from_camera_id=n1.camera_id,
                    to_camera_id=n2.camera_id,
                    from_location=n1.location_name,
                    to_location=n2.location_name,
                    distance_km=dist_km,
                    transit_duration_seconds=round(duration_sec, 1),
                    transit_speed_kmh=round(speed_kmh, 1),
                    plausibility=plausibility,
                    plausibility_reason=reason,
                )
            )

        # Total journey duration
        if len(nodes) >= 2:
            total_duration = max(0.0, (nodes[-1].last_seen - nodes[0].first_seen).total_seconds())
        elif len(nodes) == 1:
            total_duration = nodes[0].dwell_time_seconds
        else:
            total_duration = 0.0

        unique_cams = len({n.camera_id for n in nodes})
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        # Update telemetry
        with self._lock:
            self._total_correlations += 1
            self._total_anomalies += anomalies_count
            if cloned_suspected:
                self._cloned_plates_caught += 1
            self._latency_samples.append(elapsed_ms)
            self._last_correlation_at = now_utc

        return CorrelationResult(
            target_query=target_str,
            total_sightings=len(raw_events),
            unique_cameras=unique_cams,
            total_journey_distance_km=round(total_dist_km, 2),
            total_journey_duration_seconds=round(total_duration, 1),
            nodes=nodes,
            hops=hops,
            anomalies_detected=anomalies_count,
            is_cloned_plate_suspected=cloned_suspected,
            execution_time_ms=round(elapsed_ms, 2),
        )

    async def detect_cloned_plates(
        self, db: AsyncSession, req: CloneDetectionRequest
    ) -> List[ClonedPlateAnomaly]:
        """Scan active surveillance window to identify cloned or duplicated vehicle plates across the city."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=req.time_window_minutes)

        stmt = (
            select(VehicleEvent)
            .where(
                VehicleEvent.plate_normalized.isnot(None),
                VehicleEvent.event_time >= cutoff,
            )
            .order_by(VehicleEvent.plate_normalized, VehicleEvent.event_time.asc())
        )
        res = await db.execute(stmt)
        events = list(res.scalars().all())

        # Group by plate
        plate_groups: Dict[str, List[VehicleEvent]] = {}
        for ev in events:
            p = ev.plate_normalized or ""
            if p:
                plate_groups.setdefault(p, []).append(ev)

        anomalies: List[ClonedPlateAnomaly] = []

        for plate, p_events in plate_groups.items():
            if len(p_events) < 2:
                continue

            nodes = self._cluster_events_into_nodes(p_events, cluster_dwell_seconds=30.0)
            if len(nodes) < 2:
                continue

            for i in range(len(nodes) - 1):
                n1 = nodes[i]
                n2 = nodes[i + 1]

                if n1.camera_id == n2.camera_id:
                    continue

                dist_km = haversine_distance_km(
                    n1.latitude, n1.longitude, n2.latitude, n2.longitude
                )
                duration_sec = (n2.first_seen - n1.last_seen).total_seconds()
                if duration_sec <= 0:
                    duration_sec = max(1.0, (n2.first_seen - n1.first_seen).total_seconds())

                speed_kmh = (dist_km / max(1.0, duration_sec)) * 3600.0

                # Cloned criteria: distant cameras observed within near-simultaneous window or exceeding maximum physical speed
                is_clone = (duration_sec < 120.0 and dist_km >= req.min_distance_km) or (
                    speed_kmh > req.max_plausible_speed_kmh and dist_km >= req.min_distance_km
                )

                if is_clone:
                    anomalies.append(
                        ClonedPlateAnomaly(
                            plate_normalized=plate,
                            sighting_a=n1,
                            sighting_b=n2,
                            time_delta_seconds=round(duration_sec, 1),
                            distance_km=round(dist_km, 2),
                            implied_speed_kmh=round(speed_kmh, 1),
                            anomaly_type="SIMULTANEOUS_MULTI_LOCATION_SIGHTING"
                            if duration_sec < 120.0
                            else "IMPOSSIBLE_TRANSIT_SPEED",
                            flagged_at=now,
                        )
                    )

        with self._lock:
            self._cloned_plates_caught += len(anomalies)

        return anomalies

    async def visual_match(
        self, db: AsyncSession, req: VisualMatchRequest
    ) -> List[VisualMatchCandidate]:
        """Find cross-camera vehicle matches via 512-dim visual Re-ID cosine similarity."""
        stmt = (
            select(VehicleEmbedding, VehicleEvent)
            .join(VehicleEvent, VehicleEmbedding.event_id == VehicleEvent.id)
            .order_by(VehicleEvent.event_time.desc())
            .limit(500)
        )
        res = await db.execute(stmt)
        records = res.all()

        candidates: List[VisualMatchCandidate] = []

        for emb_rec, ev_rec in records:
            try:
                vec = json.loads(emb_rec.vector_data)
                sim = cosine_similarity(req.embedding, vec)
                if sim >= req.min_similarity:
                    candidates.append(
                        VisualMatchCandidate(
                            event_id=ev_rec.id,
                            camera_id=ev_rec.camera_id,
                            location_name=ev_rec.location_name,
                            event_time=ev_rec.event_time,
                            cosine_similarity=round(sim, 4),
                            vehicle_class=ev_rec.vehicle_class,
                            vehicle_color=ev_rec.vehicle_color,
                            plate_normalized=ev_rec.plate_normalized,
                            snapshot_path=ev_rec.snapshot_path,
                        )
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to calculate embedding similarity for event {ev_rec.id}: {e}"
                )

        candidates.sort(key=lambda x: x.cosine_similarity, reverse=True)
        return candidates[: req.limit]

    def get_telemetry(self) -> CorrelationTelemetry:
        """Retrieve real-time correlation and anomaly detection telemetry."""
        with self._lock:
            avg_lat = (
                sum(self._latency_samples) / len(self._latency_samples)
                if self._latency_samples
                else 0.0
            )

            return CorrelationTelemetry(
                total_correlations_executed=self._total_correlations,
                total_anomalies_flagged=self._total_anomalies,
                cloned_plates_identified=self._cloned_plates_caught,
                average_correlation_time_ms=round(avg_lat, 2),
                last_correlation_at=self._last_correlation_at,
            )


# Global singleton instance
correlation_engine = CrossCameraCorrelationEngine()
