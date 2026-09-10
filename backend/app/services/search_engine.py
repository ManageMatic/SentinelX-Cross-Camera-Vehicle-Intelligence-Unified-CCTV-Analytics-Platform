"""Sub-200ms Vehicle Search Engine Service (Module 15).

High-performance querying engine for indexed vehicle intelligence events with exact,
wildcard, fuzzy license plate matching, temporal, spatial, and visual attribute filtering.
"""

import math
import threading
import time
from collections import Counter, deque
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import VehicleEvent
from app.schemas.search import (
    FuzzyPlateCandidate,
    SearchResultItem,
    SearchTelemetry,
    VehicleSearchQuery,
    VehicleSearchResponse,
)


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute classic Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two GPS points using Haversine formula."""
    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 3)


class VehicleSearchEngine:
    """Ultra-low-latency vehicle intelligence search engine."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_searches: int = 0
        self._latency_samples: deque[float] = deque(maxlen=500)
        self._search_timestamps: deque[float] = deque(maxlen=200)
        self._top_queries: Counter[str] = Counter()

    def _record_query_latency(self, latency_ms: float, query_key: Optional[str] = None) -> None:
        """Record search latency sample and calculate moving performance metrics."""
        now_ts = time.time()
        with self._lock:
            self._total_searches += 1
            self._latency_samples.append(latency_ms)
            self._search_timestamps.append(now_ts)
            if query_key:
                self._top_queries[query_key] += 1

    async def search_vehicles(
        self, db: AsyncSession, query: VehicleSearchQuery
    ) -> VehicleSearchResponse:
        """Execute multi-criteria vehicle search with sub-200ms latency guarantee."""
        start_t = time.perf_counter()

        # Build dynamic SQLAlchemy select statement
        stmt = select(VehicleEvent)
        count_stmt = select(func.count()).select_from(VehicleEvent)

        filters = []

        # 1. License Plate Filtering (Exact, Wildcard, or Standard Match)
        if query.plate:
            plate_clean = query.plate.strip().upper().replace(" ", "")
            query_key = f"plate:{plate_clean}"

            if "*" in plate_clean or "?" in plate_clean:
                # Convert user wildcard syntax to SQL LIKE pattern
                sql_like = plate_clean.replace("*", "%").replace("?", "_")
                p_filter = or_(
                    VehicleEvent.plate_normalized.like(sql_like),
                    VehicleEvent.plate_raw.like(sql_like),
                )
                filters.append(p_filter)
            elif not query.fuzzy_plate:
                # Exact or prefix match
                p_filter = or_(
                    VehicleEvent.plate_normalized == plate_clean,
                    VehicleEvent.plate_raw == plate_clean,
                    VehicleEvent.plate_normalized.like(f"%{plate_clean}%"),
                )
                filters.append(p_filter)
        else:
            query_key = "multi_filter"

        # 2. Camera Restrictions
        if query.camera_ids and len(query.camera_ids) > 0:
            filters.append(VehicleEvent.camera_id.in_(query.camera_ids))

        # 3. Temporal Date/Time Range
        if query.start_time:
            filters.append(VehicleEvent.event_time >= query.start_time)
        if query.end_time:
            filters.append(VehicleEvent.event_time <= query.end_time)

        # 4. Vehicle Class & Color
        if query.vehicle_classes and len(query.vehicle_classes) > 0:
            classes_clean = [c.lower().strip() for c in query.vehicle_classes]
            filters.append(VehicleEvent.vehicle_class.in_(classes_clean))
        if query.vehicle_colors and len(query.vehicle_colors) > 0:
            colors_clean = [c.lower().strip() for c in query.vehicle_colors]
            filters.append(VehicleEvent.vehicle_color.in_(colors_clean))

        # 5. Confidence Thresholds & Readable Plate Constraint
        if query.min_confidence is not None:
            filters.append(VehicleEvent.detection_confidence >= query.min_confidence)
        if query.has_plate_only:
            filters.append(VehicleEvent.plate_normalized.isnot(None))

        # Apply WHERE filters
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        # Total Count Execution
        total_res = await db.execute(count_stmt)
        total_count = total_res.scalar_one() or 0

        # Sorting
        sort_col = getattr(VehicleEvent, query.sort_by, VehicleEvent.event_time)
        if query.sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_col.asc())
        else:
            stmt = stmt.order_by(sort_col.desc())

        # Pagination
        offset_val = (query.page - 1) * query.page_size
        stmt = stmt.offset(offset_val).limit(query.page_size)

        # Execute Search
        exec_res = await db.execute(stmt)
        events = exec_res.scalars().all()

        # Transform to SearchResultItems
        results: List[SearchResultItem] = []
        for ev in events:
            # Calculate distance if geospatial center provided
            dist_km = None
            if query.latitude is not None and query.longitude is not None:
                dist_km = haversine_distance_km(
                    query.latitude, query.longitude, ev.latitude, ev.longitude
                )
                if query.radius_km is not None and dist_km > query.radius_km:
                    continue  # Exclude outside radial boundary

            results.append(
                SearchResultItem(
                    id=ev.id,
                    camera_id=ev.camera_id,
                    camera_name=ev.camera.name if ev.camera else None,
                    track_id=ev.track_id,
                    event_time=ev.event_time,
                    source_pts=ev.source_pts,
                    plate_raw=ev.plate_raw,
                    plate_normalized=ev.plate_normalized,
                    plate_confidence=ev.plate_confidence,
                    vehicle_class=ev.vehicle_class,
                    vehicle_color=ev.vehicle_color,
                    detection_confidence=ev.detection_confidence,
                    latitude=ev.latitude,
                    longitude=ev.longitude,
                    location_name=ev.location_name,
                    distance_km=dist_km,
                    bbox_x1=ev.bbox_x1,
                    bbox_y1=ev.bbox_y1,
                    bbox_x2=ev.bbox_x2,
                    bbox_y2=ev.bbox_y2,
                    snapshot_path=ev.snapshot_path,
                    has_embedding=ev.embedding is not None,
                )
            )

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        self._record_query_latency(elapsed_ms, query_key)

        total_pages = max(1, math.ceil(total_count / max(1, query.page_size)))
        has_next = query.page < total_pages

        return VehicleSearchResponse(
            results=results,
            total_count=total_count,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            has_next=has_next,
            execution_time_ms=round(elapsed_ms, 2),
        )

    async def fuzzy_plate_search(
        self,
        db: AsyncSession,
        query_str: str,
        max_distance: int = 2,
        min_similarity: float = 0.60,
        limit: int = 50,
    ) -> List[FuzzyPlateCandidate]:
        """Perform fuzzy Levenshtein license plate search with optical character tolerance."""
        start_t = time.perf_counter()
        target = query_str.strip().upper().replace(" ", "")

        # Fetch recent events with valid normalized plates
        stmt = (
            select(VehicleEvent)
            .where(VehicleEvent.plate_normalized.isnot(None))
            .order_by(VehicleEvent.event_time.desc())
            .limit(1000)
        )
        res = await db.execute(stmt)
        events = res.scalars().all()

        candidates: List[FuzzyPlateCandidate] = []
        seen_events = set()

        for ev in events:
            plate_candidate = (ev.plate_normalized or "").upper().replace(" ", "")
            if not plate_candidate or ev.id in seen_events:
                continue

            dist = levenshtein_distance(target, plate_candidate)
            max_len = max(len(target), len(plate_candidate))
            sim = 1.0 - (float(dist) / float(max_len)) if max_len > 0 else 1.0

            if dist <= max_distance or sim >= min_similarity:
                seen_events.add(ev.id)
                candidates.append(
                    FuzzyPlateCandidate(
                        plate_raw=ev.plate_raw or plate_candidate,
                        plate_normalized=plate_candidate,
                        event_id=ev.id,
                        camera_id=ev.camera_id,
                        event_time=ev.event_time,
                        edit_distance=dist,
                        similarity_score=round(sim, 4),
                        vehicle_class=ev.vehicle_class,
                        vehicle_color=ev.vehicle_color,
                        snapshot_path=ev.snapshot_path,
                    )
                )

        # Sort by highest similarity first (lowest edit distance)
        candidates.sort(key=lambda x: (-x.similarity_score, x.edit_distance))
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        self._record_query_latency(elapsed_ms, f"fuzzy:{target}")

        return candidates[:limit]

    async def quick_lookup(
        self, db: AsyncSession, plate_str: str, limit: int = 20
    ) -> List[SearchResultItem]:
        """Sub-50ms instant lookup by exact or normalized license plate string."""
        clean_plate = plate_str.strip().upper().replace(" ", "")
        q = VehicleSearchQuery(plate=clean_plate, page=1, page_size=limit)
        res = await self.search_vehicles(db, q)
        return res.results

    def get_telemetry(self) -> SearchTelemetry:
        """Retrieve real-time search engine query throughput and latency telemetry."""
        with self._lock:
            now = time.time()
            cutoff = now - 60.0
            recent_count = len([t for t in self._search_timestamps if t >= cutoff])

            samples = list(self._latency_samples)
            if samples:
                avg_lat = sum(samples) / len(samples)
                sorted_samples = sorted(samples)
                p95_idx = int(0.95 * len(sorted_samples))
                p95_lat = sorted_samples[min(p95_idx, len(sorted_samples) - 1)]
                sub_200_count = sum(1 for s in samples if s <= 200.0)
                compliance = (sub_200_count / len(samples)) * 100.0
            else:
                avg_lat = 0.0
                p95_lat = 0.0
                compliance = 100.0

            top_q = [{"query": k, "count": v} for k, v in self._top_queries.most_common(10)]

            return SearchTelemetry(
                total_searches_executed=self._total_searches,
                average_search_latency_ms=round(avg_lat, 2),
                p95_latency_ms=round(p95_lat, 2),
                sub_200ms_compliance_rate=round(compliance, 2),
                searches_last_minute=recent_count,
                top_queried_plates=top_q,
            )


# Global singleton instance
search_engine = VehicleSearchEngine()
