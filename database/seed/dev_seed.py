"""Database development and demonstration seeder.

Populates initial seed data for local development and testing.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to Python path for standalone script execution
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import AsyncSessionLocal, close_db, init_db  # noqa: E402
from app.models import (  # noqa: E402
    Camera,
    Role,
    RoleType,
    User,
    VehicleEvent,
    Watchlist,
    WatchlistCategory,
    WatchlistEntry,
    WatchlistPriority,
)
from sqlalchemy import select  # noqa: E402


async def seed_dev_database() -> None:
    """Seeds initial development data for SentinelX."""
    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Seed Roles & Permissions
        role_result = await session.execute(select(Role).where(Role.name == RoleType.ADMIN.value))
        admin_role = role_result.scalars().first()

        if not admin_role:
            admin_role = Role(
                name=RoleType.ADMIN.value,
                description="State Command & Control Administrator",
                is_system_default=True,
            )
            operator_role = Role(
                name=RoleType.OPERATOR.value,
                description="CCTV Grid & Live Monitoring Operator",
                is_system_default=True,
            )
            investigator_role = Role(
                name=RoleType.INVESTIGATOR.value,
                description="Cross-Camera Vehicle Intelligence Investigator",
                is_system_default=True,
            )
            session.add_all([admin_role, operator_role, investigator_role])
            await session.flush()

        # 2. Seed Default Admin User
        user_result = await session.execute(select(User).where(User.username == "inspector_patel"))
        if not user_result.scalars().first():
            user = User(
                username="inspector_patel",
                email="patel.police@gujarat.gov.in",
                full_name="Inspector R. Patel",
                badge_number="GJ-POL-8842",
                department="Gujarat Police Intelligence Division",
                hashed_password="argon2_hashed_placeholder",
                role_id=admin_role.id,
                is_superuser=True,
            )
            session.add(user)

        # 3. Seed Sample Gujarat Police Cameras (dynamic format matching Sentinel catalog)
        cameras_data = [
            {
                "external_id": "CAM_AHM_001",
                "name": "Ahmedabad Junction Entry Gate",
                "location": "Ahmedabad Junction",
                "lat": 23.0225,
                "lon": 72.5714,
                "rtsp": "rtsp://localhost:8554/stream/cam1",
                "whep": "http://localhost:8889/stream/cam1/whep",
                "hls": "http://localhost:80/live/stream/cam1/index.m3u8",
            },
            {
                "external_id": "CAM_AHM_002",
                "name": "SG Highway — Iscon Flyover North",
                "location": "SG Highway",
                "lat": 23.0298,
                "lon": 72.5074,
                "rtsp": "rtsp://localhost:8554/stream/cam2",
                "whep": "http://localhost:8889/stream/cam2/whep",
                "hls": "http://localhost:80/live/stream/cam2/index.m3u8",
            },
            {
                "external_id": "CAM_AHM_003",
                "name": "Ring Road — Vaishnodevi Circle",
                "location": "Vaishnodevi Circle",
                "lat": 23.1362,
                "lon": 72.5457,
                "rtsp": "rtsp://localhost:8554/stream/cam3",
                "whep": "http://localhost:8889/stream/cam3/whep",
                "hls": "http://localhost:80/live/stream/cam3/index.m3u8",
            },
            {
                "external_id": "CAM_GND_001",
                "name": "Gandhinagar GH Road Junction",
                "location": "GH Road Gandhinagar",
                "lat": 23.2156,
                "lon": 72.6369,
                "rtsp": "rtsp://localhost:8554/stream/cam4",
                "whep": "http://localhost:8889/stream/cam4/whep",
                "hls": "http://localhost:80/live/stream/cam4/index.m3u8",
            },
        ]

        created_cameras = []
        for cam in cameras_data:
            existing = await session.execute(
                select(Camera).where(Camera.external_camera_id == cam["external_id"])
            )
            cam_obj = existing.scalars().first()
            if not cam_obj:
                cam_obj = Camera(
                    external_camera_id=cam["external_id"],
                    name=cam["name"],
                    location_name=cam["location"],
                    latitude=cam["lat"],
                    longitude=cam["lon"],
                    rtsp_url=cam["rtsp"],
                    whep_url=cam["whep"],
                    hls_url=cam["hls"],
                    live_status=True,
                    last_seen=datetime.now(timezone.utc),
                )
                session.add(cam_obj)
            created_cameras.append(cam_obj)
        await session.flush()

        # 4. Seed Sample Watchlist
        watchlist_result = await session.execute(
            select(Watchlist).where(Watchlist.name == "High-Risk Stolen Vehicles Gujarat")
        )
        watchlist = watchlist_result.scalars().first()
        if not watchlist:
            watchlist = Watchlist(
                name="High-Risk Stolen Vehicles Gujarat",
                description="Active stolen vehicle hotlist linked to CID Crime FIRs",
                category=WatchlistCategory.STOLEN.value,
                created_by="Inspector R. Patel",
            )
            session.add(watchlist)
            await session.flush()

            entry1 = WatchlistEntry(
                watchlist_id=watchlist.id,
                registration_number="GJ 01 AB 1234",
                registration_normalized="GJ01AB1234",
                category=WatchlistCategory.STOLEN.value,
                priority=WatchlistPriority.HIGH.value,
                notes="White Hyundai Creta reported stolen in Navrangpura FIR 104/2026",
                created_by="Inspector R. Patel",
            )
            entry2 = WatchlistEntry(
                watchlist_id=watchlist.id,
                registration_number="GJ 05 CD 5678",
                registration_normalized="GJ05CD5678",
                category=WatchlistCategory.WANTED.value,
                priority=WatchlistPriority.HIGH.value,
                notes="Silver Swift Dzire involved in toll plaza evasion",
                created_by="Inspector R. Patel",
            )
            session.add_all([entry1, entry2])

        # 5. Seed Sample Vehicle Cross-Camera Events (Journey of GJ01AB1234)
        event_result = await session.execute(
            select(VehicleEvent).where(VehicleEvent.plate_normalized == "GJ01AB1234")
        )
        if not event_result.scalars().first() and len(created_cameras) >= 3:
            now = datetime.now(timezone.utc)
            event1 = VehicleEvent(
                camera_id=created_cameras[0].id,
                track_id="TRK_001_17",
                event_time=now - timedelta(minutes=25),
                plate_raw="GJ 01 AB 1234",
                plate_normalized="GJ01AB1234",
                plate_confidence=0.96,
                vehicle_class="car",
                vehicle_color="white",
                detection_confidence=0.92,
                latitude=created_cameras[0].latitude,
                longitude=created_cameras[0].longitude,
                location_name=created_cameras[0].location_name,
            )
            event2 = VehicleEvent(
                camera_id=created_cameras[1].id,
                track_id="TRK_002_09",
                event_time=now - timedelta(minutes=15),
                plate_raw="GJ01AB1234",
                plate_normalized="GJ01AB1234",
                plate_confidence=0.94,
                vehicle_class="car",
                vehicle_color="white",
                detection_confidence=0.95,
                latitude=created_cameras[1].latitude,
                longitude=created_cameras[1].longitude,
                location_name=created_cameras[1].location_name,
            )
            event3 = VehicleEvent(
                camera_id=created_cameras[2].id,
                track_id="TRK_003_24",
                event_time=now - timedelta(minutes=5),
                plate_raw="GJ 01 AB 1234",
                plate_normalized="GJ01AB1234",
                plate_confidence=0.98,
                vehicle_class="car",
                vehicle_color="white",
                detection_confidence=0.97,
                latitude=created_cameras[2].latitude,
                longitude=created_cameras[2].longitude,
                location_name=created_cameras[2].location_name,
            )
            session.add_all([event1, event2, event3])

        await session.commit()
        print("Database seed completed successfully.")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed_dev_database())
