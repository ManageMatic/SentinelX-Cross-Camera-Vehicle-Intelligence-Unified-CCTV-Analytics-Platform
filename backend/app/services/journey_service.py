"""Chronological Journey & Route Timeline Reconstructor Service (Module 17).

Reconstructs point-to-point vehicle movement histories, detects loitering and circular cruising
behavior patterns, and exports GIS GeoJSON for map rendering (MapLibre / Leaflet).
"""

import logging
import threading
import time
from collections import Counter, deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.correlation import CorrelationPlausibility, CorrelationRequest
from app.schemas.journey import (
    BehaviorPattern,
    JourneyReconstructRequest,
    JourneyTelemetry,
    JourneyTimeline,
    RouteLeg,
    Waypoint,
)
from app.services.correlation_engine import correlation_engine

logger = logging.getLogger("sentinelx.journey")


class JourneyReconstructorService:
    """Flagship journey reconstruction, behavior analysis, and GIS GeoJSON generator."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_journeys: int = 0
        self._total_loops: int = 0
        self._total_loitering: int = 0
        self._latency_samples: deque[float] = deque(maxlen=200)
        self._last_reconstruction_at: Optional[datetime] = None

    async def reconstruct_journey(
        self, db: AsyncSession, req: JourneyReconstructRequest
    ) -> Optional[JourneyTimeline]:
        """Reconstruct full vehicle movement timeline with legs, waypoints, behavior analysis, and GeoJSON."""
        start_t = time.perf_counter()
        now_utc = datetime.now(timezone.utc)

        # 1. Obtain correlated nodes and hops
        corr_req = CorrelationRequest(
            plate=req.plate,
            event_id=req.event_id,
            start_time=req.start_time,
            end_time=req.end_time,
        )
        corr_res = await correlation_engine.correlate_vehicle(db, corr_req)

        if not corr_res.nodes:
            return None

        # 2. Build Chronological Waypoints
        waypoints: List[Waypoint] = []
        for idx, node in enumerate(corr_res.nodes, start=1):
            waypoints.append(
                Waypoint(
                    sequence=idx,
                    camera_id=node.camera_id,
                    camera_name=node.camera_name,
                    location_name=node.location_name,
                    coordinates=[node.longitude, node.latitude],  # GeoJSON standard: [lon, lat]
                    arrived_at=node.first_seen,
                    departed_at=node.last_seen,
                    dwell_seconds=node.dwell_time_seconds,
                    snapshot_path=node.best_snapshot_path,
                    plate_reading=node.plate_normalized or node.plate_raw,
                    vehicle_class=node.vehicle_class,
                    vehicle_color=node.vehicle_color,
                )
            )

        # 3. Build Route Legs
        legs: List[RouteLeg] = []
        for idx, hop in enumerate(corr_res.hops, start=1):
            n_from = corr_res.nodes[idx - 1]
            n_to = corr_res.nodes[idx]

            is_anomaly = hop.plausibility != CorrelationPlausibility.PLAUSIBLE
            legs.append(
                RouteLeg(
                    leg_index=idx,
                    from_camera_id=hop.from_camera_id,
                    to_camera_id=hop.to_camera_id,
                    from_location=hop.from_location,
                    to_location=hop.to_location,
                    start_time=n_from.last_seen,
                    arrival_time=n_to.first_seen,
                    duration_seconds=hop.transit_duration_seconds,
                    distance_km=hop.distance_km,
                    average_speed_kmh=hop.transit_speed_kmh,
                    is_speed_anomaly=is_anomaly,
                )
            )

        # 4. Behavioral Anomaly & Pattern Recognition
        behavior_patterns: List[BehaviorPattern] = []
        loitering_count = 0
        loop_count = 0

        # Pattern A: Loitering / Extended Dwell Detection
        dwell_threshold_sec = req.max_dwell_loiter_minutes * 60.0
        for wp in waypoints:
            if wp.dwell_seconds >= dwell_threshold_sec:
                dwell_mins = wp.dwell_seconds / 60.0
                behavior_patterns.append(
                    BehaviorPattern(
                        pattern_type="LOITERING_DWELL",
                        severity="HIGH" if dwell_mins > 30.0 else "MEDIUM",
                        description=(
                            f"Vehicle remained stationary / loitering at '{wp.location_name}' "
                            f"for {dwell_mins:.1f} minutes."
                        ),
                        evidence_locations=[wp.location_name],
                        detected_at=wp.arrived_at,
                    )
                )
                loitering_count += 1

        # Pattern B: Circular Looping / Cruising Surveillance Detection
        cam_visit_counts = Counter(wp.camera_id for wp in waypoints)
        for cam_id, count in cam_visit_counts.items():
            if count >= 2 and len(waypoints) >= 3:
                # Find camera name
                matching_wp = next(w for w in waypoints if w.camera_id == cam_id)
                behavior_patterns.append(
                    BehaviorPattern(
                        pattern_type="CIRCULAR_LOOPING_CRUISE",
                        severity="HIGH",
                        description=(
                            f"Vehicle made {count} repeated passes through '{matching_wp.location_name}', "
                            "indicating potential circular cruising or route surveillance."
                        ),
                        evidence_locations=[matching_wp.location_name],
                        detected_at=matching_wp.arrived_at,
                    )
                )
                loop_count += 1

        # Pattern C: Rapid Transit Detection
        for leg in legs:
            if leg.average_speed_kmh > 120.0:
                behavior_patterns.append(
                    BehaviorPattern(
                        pattern_type="RAPID_TRANSIT",
                        severity="MEDIUM" if leg.average_speed_kmh < 160.0 else "HIGH",
                        description=(
                            f"Rapid transit speed ({leg.average_speed_kmh:.1f} km/h) recorded between "
                            f"'{leg.from_location}' and '{leg.to_location}' ({leg.distance_km:.2f} km in {leg.duration_seconds / 60:.1f} mins)."
                        ),
                        evidence_locations=[leg.from_location, leg.to_location],
                        detected_at=leg.start_time,
                    )
                )

        # 5. Build RFC 7946 GIS GeoJSON FeatureCollection
        geojson_features = []

        # Point features for waypoints
        for wp in waypoints:
            geojson_features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": wp.coordinates,  # [lon, lat]
                    },
                    "properties": {
                        "sequence": wp.sequence,
                        "camera_id": wp.camera_id,
                        "camera_name": wp.camera_name,
                        "location_name": wp.location_name,
                        "arrived_at": wp.arrived_at.isoformat(),
                        "departed_at": wp.departed_at.isoformat(),
                        "dwell_seconds": wp.dwell_seconds,
                        "snapshot_path": wp.snapshot_path,
                        "plate_reading": wp.plate_reading,
                        "vehicle_class": wp.vehicle_class,
                        "vehicle_color": wp.vehicle_color,
                    },
                }
            )

        # LineString feature for full route trajectory
        if len(waypoints) >= 2:
            route_coords = [wp.coordinates for wp in waypoints]
            geojson_features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": route_coords,
                    },
                    "properties": {
                        "route_id": f"journey_{req.plate or 'veh'}",
                        "plate_normalized": req.plate or waypoints[0].plate_reading or "UNKNOWN",
                        "total_distance_km": corr_res.total_journey_distance_km,
                        "total_duration_seconds": corr_res.total_journey_duration_seconds,
                        "total_waypoints": len(waypoints),
                        "total_legs": len(legs),
                    },
                }
            )

        geojson_collection = {
            "type": "FeatureCollection",
            "features": geojson_features,
        }

        # Calculate Overall Speed
        hours = corr_res.total_journey_duration_seconds / 3600.0
        avg_speed = round(corr_res.total_journey_distance_km / hours, 1) if hours > 0 else 0.0

        first_wp = waypoints[0]
        last_wp = waypoints[-1]

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        # Update telemetry
        with self._lock:
            self._total_journeys += 1
            self._total_loops += loop_count
            self._total_loitering += loitering_count
            self._latency_samples.append(elapsed_ms)
            self._last_reconstruction_at = now_utc

        return JourneyTimeline(
            plate_normalized=req.plate or first_wp.plate_reading or "UNKNOWN",
            vehicle_class=first_wp.vehicle_class,
            vehicle_color=first_wp.vehicle_color,
            origin_location=first_wp.location_name,
            destination_location=last_wp.location_name,
            first_detected_at=first_wp.arrived_at,
            last_detected_at=last_wp.departed_at,
            total_journey_duration_seconds=corr_res.total_journey_duration_seconds,
            total_distance_km=corr_res.total_journey_distance_km,
            average_journey_speed_kmh=avg_speed,
            total_stops=len(waypoints),
            waypoints=waypoints,
            legs=legs,
            behavior_patterns=behavior_patterns,
            geojson=geojson_collection,
            reconstructed_at=now_utc,
        )

    async def get_geojson_collection(
        self, db: AsyncSession, plate: str
    ) -> Optional[Dict[str, Any]]:
        """Direct helper to extract GeoJSON FeatureCollection for GIS map rendering."""
        req = JourneyReconstructRequest(plate=plate)
        timeline = await self.reconstruct_journey(db, req)
        return timeline.geojson if timeline else None

    def get_telemetry(self) -> JourneyTelemetry:
        """Retrieve real-time journey reconstruction throughput and behavior telemetry."""
        with self._lock:
            avg_lat = (
                sum(self._latency_samples) / len(self._latency_samples)
                if self._latency_samples
                else 0.0
            )

            return JourneyTelemetry(
                total_journeys_reconstructed=self._total_journeys,
                total_loops_detected=self._total_loops,
                total_loitering_events_flagged=self._total_loitering,
                average_reconstruction_ms=round(avg_lat, 2),
                last_reconstruction_at=self._last_reconstruction_at,
            )


# Global singleton instance
journey_service = JourneyReconstructorService()
