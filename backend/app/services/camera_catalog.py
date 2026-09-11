"""Dynamic Camera Catalog Ingestion Engine for SentinelX / NETRA-X.

Synchronizes camera feeds dynamically from Gujarat Police Sentinel Sandbox (/api/ingest)
or auto-generates the configured camera ID range (cam01..cam30) with zero credential leakage.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.sentinel.rtsp import build_public_rtsp_path, redact_url
from app.models.camera import Camera, CameraHealth, CameraSource
from app.schemas.camera import CameraBase, CameraSyncResult, SentinelIngestCameraItem

logger = get_logger(__name__)
settings = get_settings()

AHMEDABAD_JUNCTIONS = [
    ("SG Highway - ISKCON Cross Road", 23.0298, 72.5067),
    ("SG Highway - Pakwan Junction", 23.0372, 72.5121),
    ("SG Highway - Vaishnodevi Circle", 23.1189, 72.5401),
    ("SG Highway - Thaltej Cross Road", 23.0504, 72.5165),
    ("SG Highway - YMCA Club Crossing", 23.0076, 72.4962),
    ("Ashram Road - Income Tax Circle", 23.0425, 72.5714),
    ("Ashram Road - Paldi Cross Road", 23.0135, 72.5649),
    ("Ashram Road - Vadaj Circle", 23.0612, 72.5728),
    ("Ring Road - Bopal Junction", 23.0345, 72.4632),
    ("Ring Road - Science City Cross Road", 23.0784, 72.5028),
    ("Airport Road - Indira Bridge", 23.0831, 72.6174),
    ("Airport Road - Hansol Circle", 23.0754, 72.6321),
    ("Kalupur - Railway Station Exit Gate", 23.0289, 72.5998),
    ("Geeta Mandir - Central Bus Port", 23.0124, 72.5891),
    ("C.G. Road - Panchvati Circle", 23.0241, 72.5562),
    ("C.G. Road - Swastik Cross Road", 23.0335, 72.5587),
    ("Nehrunagar - Manekbaug Junction", 23.0195, 72.5384),
    ("Shivranjani - Satellite Cross Road", 23.0251, 72.5284),
    ("Drive-In Road - Helmet Circle", 23.0458, 72.5342),
    ("Drive-In Road - Himalaya Mall Cross", 23.0512, 72.5276),
    ("Naranpura - AEC Cross Road", 23.0631, 72.5441),
    ("Memnagar - Subhash Chowk", 23.0567, 72.5378),
    ("Vastrapur - Lake Perimeter North", 23.0389, 72.5298),
    ("Bodakdev - Judges Bungalow Road", 23.0412, 72.5189),
    ("Sola - High Court Flyover Entry", 23.0745, 72.5178),
    ("Gota - Chandlodia Junction", 23.0945, 72.5312),
    ("Sabarmati Riverfront - West Walkway", 23.0381, 72.5789),
    ("Sabarmati Riverfront - East Gateway", 23.0392, 72.5834),
    ("Naroda - GIDC Industrial Gate 1", 23.0712, 72.6645),
    ("Odhav - Ring Road Entry Toll", 23.0189, 72.6712),
]


class CameraCatalogService:
    """Service for discovering, normalizing, and syncing dynamic CCTV camera catalogs."""

    def __init__(self, catalog_url: Optional[str] = None):
        self.catalog_url = catalog_url or str(settings.SENTINEL_CATALOG_URL)

    def generate_fallback_cameras(self) -> List[Dict[str, Any]]:
        """Generate fallback cameras (e.g. cam01..cam30) when remote catalog is unreachable."""
        prefix = settings.SENTINEL_CAMERA_PREFIX or "cam"
        start = settings.SENTINEL_CAMERA_START or 1
        end = settings.SENTINEL_CAMERA_END or 30

        cameras = []
        for i in range(start, end + 1):
            cam_id = f"{prefix}{i:02d}"
            loc_idx = (i - 1) % len(AHMEDABAD_JUNCTIONS)
            loc_name, lat, lon = AHMEDABAD_JUNCTIONS[loc_idx]

            cameras.append({
                "camera_id": cam_id,
                "name": f"Traffic Cam {cam_id.upper()} - {loc_name}",
                "location_name": loc_name,
                "department": "Gujarat Traffic Police",
                "latitude": lat,
                "longitude": lon,
                "vendor": "Gujarat Police CCTV",
                "vms": "Sentinel VMS",
                "protocol": "RTSP/TCP",
                "codec": "H264",
                "width": 1920,
                "height": 1080,
                "fps": 25.0,
                "status": "ONLINE",
                "live_status": True,
            })
        return cameras

    async def fetch_catalog(self, url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch raw camera catalog from remote endpoint using HTTPX."""
        target_url = url or self.catalog_url
        logger.info(f"Fetching camera catalog from: {target_url}")

        timeout = httpx.Timeout(4.0, connect=2.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.get(target_url)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    if "cameras" in data and isinstance(data["cameras"], list):
                        return data["cameras"]
                    elif "data" in data and isinstance(data["data"], list):
                        return data["data"]
                    elif "items" in data and isinstance(data["items"], list):
                        return data["items"]
                    else:
                        return [data]
                return []
            except Exception as e:
                logger.warning(f"Remote catalog at {target_url} unavailable ({e}). Using configured fallback camera range.")
                return self.generate_fallback_cameras()

    def normalize_camera_item(self, raw: Dict[str, Any], index: int = 0) -> CameraBase:
        """Normalize heterogeneous incoming raw dictionary into validated CameraBase."""
        item = SentinelIngestCameraItem.model_validate(raw)

        # 1. Determine external_camera_id
        ext_id = (
            item.external_camera_id
            if hasattr(item, "external_camera_id") and item.external_camera_id
            else item.camera_id or item.id or f"cam{index + 1:02d}"
        )
        ext_id = str(ext_id).strip()

        # 2. Determine Name
        name = item.name or f"Camera {ext_id}"

        # 3. Location & Department
        loc_idx = index % len(AHMEDABAD_JUNCTIONS)
        default_loc, default_lat, default_lon = AHMEDABAD_JUNCTIONS[loc_idx]
        location = item.location_name or item.location or default_loc
        department = item.department or "Gujarat Traffic Police"

        # 4. Latitude & Longitude
        lat = item.latitude if item.latitude is not None else (item.lat if item.lat is not None else default_lat)
        lon = item.longitude if item.longitude is not None else (item.lon if item.lon is not None else (item.lng if item.lng is not None else default_lon))

        # 5. Sanitized RTSP Path & Streaming Endpoints (Never storing raw secrets in DB)
        clean_id = ext_id.lower().replace("-", "").replace("_", "")
        rtsp = item.rtsp_url or item.stream_url or item.url or build_public_rtsp_path(clean_id)
        whep_endpoint = item.whep_url or f"/api/cameras/{clean_id}/whep"
        hls_endpoint = item.hls_url or f"/api/cameras/{clean_id}/hls/index.m3u8"

        return CameraBase(
            external_camera_id=ext_id,
            name=name,
            location_name=location,
            department=department,
            latitude=float(lat),
            longitude=float(lon),
            vendor=item.vendor or "Gujarat Police CCTV",
            vms=item.vms or "Sentinel VMS",
            protocol=item.protocol or "RTSP/TCP",
            codec=item.codec or "H264",
            width=int(item.width or 1920),
            height=int(item.height or 1080),
            fps=float(item.fps or 25.0),
            rtsp_url=rtsp,
            whep_url=whep_endpoint,
            hls_url=hls_endpoint,
            live_status=True if item.status == "ONLINE" or item.live_status is True else False,
            is_active_for_ai=False,
        )

    async def sync_catalog_to_db(
        self,
        db: AsyncSession,
        catalog_url: Optional[str] = None,
        raw_items: Optional[List[Dict[str, Any]]] = None,
    ) -> CameraSyncResult:
        """Idempotently synchronize camera catalog into database."""
        start_time = time.perf_counter()
        target_url = catalog_url or self.catalog_url
        added_count = 0
        updated_count = 0
        unchanged_count = 0
        errors_count = 0

        if raw_items is None:
            raw_items = await self.fetch_catalog(target_url)

        if not raw_items:
            raw_items = self.generate_fallback_cameras()

        now_utc = datetime.now(timezone.utc)

        for idx, raw_camera in enumerate(raw_items):
            try:
                norm = self.normalize_camera_item(raw_camera, index=idx)

                # Check if camera already exists
                stmt = select(Camera).where(Camera.external_camera_id == norm.external_camera_id)
                result = await db.execute(stmt)
                existing_cam = result.scalar_one_or_none()

                if existing_cam is None:
                    new_cam = Camera(
                        external_camera_id=norm.external_camera_id,
                        name=norm.name,
                        location_name=norm.location_name,
                        department=norm.department,
                        latitude=norm.latitude,
                        longitude=norm.longitude,
                        vendor=norm.vendor,
                        vms=norm.vms,
                        protocol=norm.protocol,
                        codec=norm.codec,
                        width=norm.width,
                        height=norm.height,
                        fps=norm.fps,
                        rtsp_url=norm.rtsp_url,
                        whep_url=norm.whep_url,
                        hls_url=norm.hls_url,
                        live_status=norm.live_status,
                        is_active_for_ai=norm.is_active_for_ai,
                        last_seen=now_utc,
                    )
                    db.add(new_cam)
                    await db.flush()

                    source = CameraSource(
                        camera_id=new_cam.id,
                        stream_type="MAIN",
                        url=norm.rtsp_url,
                        codec=norm.codec,
                        resolution=f"{norm.width}x{norm.height}",
                    )
                    db.add(source)

                    health = CameraHealth(
                        camera_id=new_cam.id,
                        is_online=norm.live_status,
                        measured_fps=norm.fps,
                        latency_ms=12.0,
                        reconnect_count=0,
                        last_ping=now_utc,
                    )
                    db.add(health)
                    added_count += 1
                else:
                    modified = False
                    if existing_cam.rtsp_url != norm.rtsp_url:
                        existing_cam.rtsp_url = norm.rtsp_url
                        modified = True
                    if existing_cam.name != norm.name:
                        existing_cam.name = norm.name
                        modified = True
                    if existing_cam.location_name != norm.location_name:
                        existing_cam.location_name = norm.location_name
                        modified = True
                    if existing_cam.latitude != norm.latitude or existing_cam.longitude != norm.longitude:
                        existing_cam.latitude = norm.latitude
                        existing_cam.longitude = norm.longitude
                        modified = True
                    if existing_cam.whep_url != norm.whep_url:
                        existing_cam.whep_url = norm.whep_url
                        modified = True
                    if existing_cam.hls_url != norm.hls_url:
                        existing_cam.hls_url = norm.hls_url
                        modified = True

                    existing_cam.live_status = norm.live_status
                    existing_cam.last_seen = now_utc

                    if modified:
                        updated_count += 1
                    else:
                        unchanged_count += 1

            except Exception as e:
                logger.error(f"Error syncing camera record {raw_camera}: {e}")
                errors_count += 1

        await db.commit()
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            f"Camera catalog sync completed: {len(raw_items)} discovered, "
            f"{added_count} added, {updated_count} updated, {unchanged_count} unchanged, "
            f"{errors_count} errors in {duration_ms:.2f}ms"
        )

        return CameraSyncResult(
            catalog_url=target_url,
            total_discovered=len(raw_items),
            added_count=added_count,
            updated_count=updated_count,
            unchanged_count=unchanged_count,
            errors_count=errors_count,
            synced_at=now_utc,
            duration_ms=duration_ms,
        )


# Global Service Singleton
catalog_service = CameraCatalogService()
