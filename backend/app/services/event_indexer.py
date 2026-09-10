"""Real-time Vehicle Event Ingestion & Indexer Service (Module 14).

Aggregates AI detections, ByteTrack identities, ANPR license plates, Re-ID visual embeddings,
and cryptographic SHA-256 evidence snapshots into high-speed searchable database records.
"""

import base64
import hashlib
import json
import logging
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.camera import Camera
from app.models.evidence import Evidence
from app.models.vehicle import (
    VehicleEmbedding,
    VehicleEvent,
    VehiclePlate,
)
from app.schemas.events import (
    EventIndexerTelemetry,
    RecentEventsFilter,
    VehicleEventBatchCreate,
    VehicleEventCreate,
    VehicleEventResponse,
    VehiclePlateResponse,
)

logger = logging.getLogger("sentinelx.indexer")


class EventIndexerService:
    """High-Throughput Vehicle Event Ingestion and Multi-Modal Indexing Engine."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._lock = threading.Lock()

        # In-Memory Ring Buffer for sub-millisecond real-time event retrieval
        self._max_recent_events = 1000
        self._recent_events: deque[VehicleEventResponse] = deque(maxlen=self._max_recent_events)

        # Performance & Telemetry metrics
        self._total_events_ingested: int = 0
        self._latency_samples: deque[float] = deque(maxlen=200)
        self._event_timestamps: deque[float] = deque(maxlen=100)
        self._total_evidence_files: int = 0
        self._evidence_storage_bytes: int = 0
        self._last_event_time: Optional[datetime] = None

        # Ensure evidence storage directories exist
        self._vehicle_evidence_dir = Path("data/evidence/vehicles")
        self._plate_evidence_dir = Path("data/evidence/plates")
        self._vehicle_evidence_dir.mkdir(parents=True, exist_ok=True)
        self._plate_evidence_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_sha256(data_bytes: bytes) -> str:
        """Compute cryptographic SHA-256 hash for forensic chain of custody."""
        return hashlib.sha256(data_bytes).hexdigest()

    def _save_snapshot_bytes(
        self, img_bytes: bytes, folder: Path, prefix: str = "snap"
    ) -> Tuple[str, str, int]:
        """Save image bytes to storage with SHA-256 calculation. Returns (rel_path, sha256, size)."""
        file_id = f"{prefix}_{uuid.uuid4().hex[:12]}.jpg"
        target_path = folder / file_id
        target_path.write_bytes(img_bytes)

        sha256_hash = self.compute_sha256(img_bytes)
        file_size = len(img_bytes)
        rel_path = str(target_path).replace("\\", "/")

        with self._lock:
            self._total_evidence_files += 1
            self._evidence_storage_bytes += file_size

        return rel_path, sha256_hash, file_size

    def _save_image_crop(
        self, crop_bgr: np.ndarray, folder: Path, prefix: str = "crop"
    ) -> Tuple[str, str, int]:
        """Encode OpenCV BGR crop to JPEG and save. Returns (rel_path, sha256, size)."""
        if crop_bgr is None or crop_bgr.size == 0:
            return "", "", 0

        success, encoded = cv2.imencode(".jpg", crop_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not success:
            return "", "", 0

        img_bytes = encoded.tobytes()
        return self._save_snapshot_bytes(img_bytes, folder, prefix)

    async def _resolve_camera_coordinates(
        self, session: AsyncSession, camera_id: str
    ) -> Tuple[float, float, str]:
        """Lookup camera location attributes if not provided in ingestion payload."""
        stmt = select(Camera).where(Camera.id == camera_id)
        result = await session.execute(stmt)
        cam = result.scalar_one_or_none()

        if cam:
            return cam.latitude, cam.longitude, cam.location_name
        return 23.0225, 72.5714, f"Camera Node {camera_id[:8]}"

    async def ingest_event(
        self, session: AsyncSession, event_in: VehicleEventCreate
    ) -> VehicleEventResponse:
        """Process and persist a single vehicle intelligence event with child plates and embeddings."""
        start_t = time.perf_counter()
        now_utc = event_in.event_time or datetime.now(timezone.utc)
        now_ts = time.time()

        # 1. Resolve Location Coordinates
        lat = event_in.latitude
        lon = event_in.longitude
        loc_name = event_in.location_name

        if lat is None or lon is None or not loc_name:
            c_lat, c_lon, c_name = await self._resolve_camera_coordinates(
                session, event_in.camera_id
            )
            lat = lat if lat is not None else c_lat
            lon = lon if lon is not None else c_lon
            loc_name = loc_name or c_name

        # 2. Process Snapshot Evidence
        snapshot_path = event_in.snapshot_path
        sha256_hash = ""
        evidence_records: List[Evidence] = []

        if event_in.snapshot_base64:
            try:
                raw_bytes = base64.b64decode(event_in.snapshot_base64)
                snapshot_path, sha256_hash, f_size = self._save_snapshot_bytes(
                    raw_bytes, self._vehicle_evidence_dir, prefix="veh"
                )
            except Exception as e:
                logger.warning(f"Failed to decode base64 snapshot: {e}")

        # 3. Create Main VehicleEvent Record
        event_id = uuid.uuid4().hex
        db_event = VehicleEvent(
            id=event_id,
            camera_id=event_in.camera_id,
            track_id=event_in.track_id,
            event_time=now_utc,
            source_pts=event_in.source_pts,
            plate_raw=event_in.plate_raw,
            plate_normalized=event_in.plate_normalized,
            plate_confidence=event_in.plate_confidence,
            vehicle_class=event_in.vehicle_class,
            vehicle_color=event_in.vehicle_color,
            detection_confidence=event_in.detection_confidence,
            latitude=lat,
            longitude=lon,
            location_name=loc_name,
            bbox_x1=event_in.bbox_x1,
            bbox_y1=event_in.bbox_y1,
            bbox_x2=event_in.bbox_x2,
            bbox_y2=event_in.bbox_y2,
            snapshot_path=snapshot_path,
        )
        session.add(db_event)

        # 4. Attach Plate Reading if present
        plate_responses: List[VehiclePlateResponse] = []
        if event_in.plate_raw or event_in.plate_normalized:
            plate_crop_path = event_in.plate_crop_path
            if event_in.plate_crop_base64:
                try:
                    p_bytes = base64.b64decode(event_in.plate_crop_base64)
                    plate_crop_path, p_sha, p_size = self._save_snapshot_bytes(
                        p_bytes, self._plate_evidence_dir, prefix="plate"
                    )
                except Exception as e:
                    logger.warning(f"Failed to decode base64 plate crop: {e}")

            plate_id = uuid.uuid4().hex
            norm_txt = event_in.plate_normalized or event_in.plate_raw or ""
            db_plate = VehiclePlate(
                id=plate_id,
                event_id=event_id,
                plate_text=event_in.plate_raw or norm_txt,
                plate_normalized=norm_txt,
                confidence=event_in.plate_confidence or 0.85,
                crop_path=plate_crop_path,
            )
            session.add(db_plate)
            plate_responses.append(
                VehiclePlateResponse(
                    id=plate_id,
                    plate_text=db_plate.plate_text,
                    plate_normalized=db_plate.plate_normalized,
                    confidence=db_plate.confidence,
                    crop_path=db_plate.crop_path,
                )
            )

        # 5. Attach Re-ID Visual Embedding if present
        has_embedding = False
        if event_in.embedding and len(event_in.embedding) > 0:
            emb_id = uuid.uuid4().hex
            db_emb = VehicleEmbedding(
                id=emb_id,
                event_id=event_id,
                model_name=event_in.embedding_model,
                embedding_dim=len(event_in.embedding),
                vector_data=json.dumps(event_in.embedding),
            )
            session.add(db_emb)
            has_embedding = True

        # 6. Create Evidence Vault Entry
        if snapshot_path and sha256_hash:
            ev_record = Evidence(
                id=uuid.uuid4().hex,
                event_id=event_id,
                camera_id=event_in.camera_id,
                file_path=snapshot_path,
                file_type="SNAPSHOT",
                mime_type="image/jpeg",
                file_size_bytes=len(raw_bytes) if "raw_bytes" in locals() else 0,
                sha256_hash=sha256_hash,
                captured_at=now_utc,
                retention_days=90,
            )
            session.add(ev_record)

        await session.commit()

        # Construct Response
        response = VehicleEventResponse(
            id=event_id,
            camera_id=event_in.camera_id,
            track_id=event_in.track_id,
            event_time=now_utc,
            source_pts=event_in.source_pts,
            plate_raw=event_in.plate_raw,
            plate_normalized=event_in.plate_normalized,
            plate_confidence=event_in.plate_confidence,
            vehicle_class=event_in.vehicle_class,
            vehicle_color=event_in.vehicle_color,
            detection_confidence=event_in.detection_confidence,
            latitude=lat,
            longitude=lon,
            location_name=loc_name,
            bbox_x1=event_in.bbox_x1,
            bbox_y1=event_in.bbox_y1,
            bbox_x2=event_in.bbox_x2,
            bbox_y2=event_in.bbox_y2,
            snapshot_path=snapshot_path,
            sha256_hash=sha256_hash or None,
            plates=plate_responses,
            has_embedding=has_embedding,
            created_at=now_utc,
        )

        latency_ms = (time.perf_counter() - start_t) * 1000.0

        # Update In-Memory Index & Telemetry
        with self._lock:
            self._total_events_ingested += 1
            self._recent_events.appendleft(response)
            self._latency_samples.append(latency_ms)
            self._event_timestamps.append(now_ts)
            self._last_event_time = now_utc

        return response

    async def ingest_batch(
        self, session: AsyncSession, batch_in: VehicleEventBatchCreate
    ) -> List[VehicleEventResponse]:
        """Ingest a batch of vehicle events in an optimized database transaction."""
        results: List[VehicleEventResponse] = []
        for event_in in batch_in.events:
            res = await self.ingest_event(session, event_in)
            results.append(res)
        return results

    def get_recent_events(self, filters: RecentEventsFilter) -> List[VehicleEventResponse]:
        """Query recent in-memory indexed events with sub-millisecond response time."""
        with self._lock:
            events = list(self._recent_events)

        matched: List[VehicleEventResponse] = []
        for ev in events:
            if filters.camera_id and ev.camera_id != filters.camera_id:
                continue
            if filters.vehicle_class and ev.vehicle_class.lower() != filters.vehicle_class.lower():
                continue
            if filters.plate_query:
                q = filters.plate_query.upper().replace(" ", "")
                p_norm = (ev.plate_normalized or "").upper().replace(" ", "")
                p_raw = (ev.plate_raw or "").upper().replace(" ", "")
                if q not in p_norm and q not in p_raw:
                    continue
            matched.append(ev)
            if len(matched) >= filters.limit:
                break

        return matched

    def get_telemetry(self) -> EventIndexerTelemetry:
        """Retrieve real-time event indexing performance and storage telemetry."""
        with self._lock:
            now = time.time()
            cutoff = now - 3.0
            valid_ts = [t for t in self._event_timestamps if t >= cutoff]
            eps = len(valid_ts) / 3.0 if valid_ts else 0.0

            avg_lat = (
                sum(self._latency_samples) / len(self._latency_samples)
                if self._latency_samples
                else 0.0
            )

            return EventIndexerTelemetry(
                total_events_ingested=self._total_events_ingested,
                events_per_second=round(eps, 2),
                average_ingest_latency_ms=round(avg_lat, 2),
                in_memory_ring_buffer_size=len(self._recent_events),
                total_evidence_files_saved=self._total_evidence_files,
                evidence_storage_bytes=self._evidence_storage_bytes,
                last_event_time=self._last_event_time,
            )


# Global singleton instance
event_indexer = EventIndexerService()
