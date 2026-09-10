"""Unit tests for SentinelX Database Models and Async CRUD Operations."""

from datetime import datetime, timezone

import pytest
from app.models import (
    Alert,
    AlertStatus,
    AuditLog,
    Camera,
    CameraHealth,
    CameraSource,
    Evidence,
    Permission,
    Role,
    RoleType,
    User,
    VehicleEmbedding,
    VehicleEvent,
    VehiclePlate,
    Watchlist,
    WatchlistCategory,
    WatchlistEntry,
    WatchlistPriority,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_user_and_role(db_session: AsyncSession):
    """Test User and Role creation with RBAC relationships."""
    admin_role = Role(
        name=RoleType.ADMIN.value,
        description="Full administrative access",
        is_system_default=True,
    )
    perm = Permission(name="cameras:write", description="Create and edit cameras")
    admin_role.permissions.append(perm)
    db_session.add(admin_role)
    await db_session.flush()

    user = User(
        username="officer_sharma",
        email="sharma@police.gov.in",
        full_name="Officer V. Sharma",
        badge_number="GJ-POL-1002",
        hashed_password="secure_hashed_password",
        role_id=admin_role.id,
    )
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.username == "officer_sharma"))
    fetched_user = result.scalars().first()
    assert fetched_user is not None
    assert fetched_user.role is not None
    assert fetched_user.role.name == "ADMIN"
    assert len(fetched_user.role.permissions) == 1
    assert fetched_user.role.permissions[0].name == "cameras:write"


@pytest.mark.asyncio
async def test_camera_and_health_models(db_session: AsyncSession):
    """Test Camera registry, auxiliary sources, and health telemetry records."""
    cam = Camera(
        external_camera_id="CAM_TEST_01",
        name="SG Highway Test Cam",
        location_name="SG Highway Junction",
        department="Traffic Police",
        latitude=23.033,
        longitude=72.512,
        rtsp_url="rtsp://localhost:8554/stream/test1",
        whep_url="http://localhost:8889/stream/test1/whep",
        hls_url="http://localhost:80/live/stream/test1/index.m3u8",
        live_status=True,
    )
    db_session.add(cam)
    await db_session.flush()

    source = CameraSource(
        camera_id=cam.id,
        stream_type="SUB",
        url="rtsp://localhost:8554/stream/test1_sub",
        resolution="720p",
    )
    health = CameraHealth(
        camera_id=cam.id,
        is_online=True,
        measured_fps=24.8,
        latency_ms=45.2,
        last_ping=datetime.now(timezone.utc),
    )
    db_session.add_all([source, health])
    await db_session.commit()

    result = await db_session.execute(
        select(Camera).where(Camera.external_camera_id == "CAM_TEST_01")
    )
    fetched_cam = result.scalars().first()
    assert fetched_cam is not None
    assert fetched_cam.name == "SG Highway Test Cam"
    assert len(fetched_cam.sources) == 1
    assert len(fetched_cam.health_records) == 1
    assert fetched_cam.health_records[0].measured_fps == 24.8


@pytest.mark.asyncio
async def test_vehicle_event_and_plate_indexing(db_session: AsyncSession):
    """Test indexing vehicle detection events, plate readings, and embeddings."""
    cam = Camera(
        external_camera_id="CAM_EVENT_TEST",
        name="Event Cam",
        location_name="Ahmedabad",
        latitude=23.02,
        longitude=72.57,
        rtsp_url="rtsp://localhost:8554/test",
    )
    db_session.add(cam)
    await db_session.flush()

    event = VehicleEvent(
        camera_id=cam.id,
        track_id="TRK_09",
        event_time=datetime.now(timezone.utc),
        plate_raw="GJ 01 AB 1234",
        plate_normalized="GJ01AB1234",
        plate_confidence=0.97,
        vehicle_class="car",
        vehicle_color="white",
        detection_confidence=0.94,
        latitude=cam.latitude,
        longitude=cam.longitude,
        location_name=cam.location_name,
    )
    db_session.add(event)
    await db_session.flush()

    plate_reading = VehiclePlate(
        event_id=event.id,
        plate_text="GJ 01 AB 1234",
        plate_normalized="GJ01AB1234",
        confidence=0.97,
    )
    embedding = VehicleEmbedding(
        event_id=event.id,
        model_name="OSNet-x0.25",
        embedding_dim=512,
        vector_data="[0.123, -0.456, 0.789]",
    )
    db_session.add_all([plate_reading, embedding])
    await db_session.commit()

    # Query event by normalized plate
    query_result = await db_session.execute(
        select(VehicleEvent).where(VehicleEvent.plate_normalized == "GJ01AB1234")
    )
    queried_event = query_result.scalars().first()
    assert queried_event is not None
    assert queried_event.vehicle_class == "car"
    assert queried_event.embedding is not None
    assert queried_event.embedding.embedding_dim == 512
    assert len(queried_event.plates) == 1


@pytest.mark.asyncio
async def test_watchlist_and_alert_generation(db_session: AsyncSession):
    """Test Watchlist creation, entry matching, and Alert recording."""
    cam = Camera(
        external_camera_id="CAM_ALERT_TEST",
        name="Alert Cam",
        latitude=23.01,
        longitude=72.56,
        rtsp_url="rtsp://localhost:8554/test",
    )
    db_session.add(cam)
    await db_session.flush()

    # Create Watchlist & Entry
    wl = Watchlist(name="Test Hotlist", category=WatchlistCategory.STOLEN.value)
    db_session.add(wl)
    await db_session.flush()

    entry = WatchlistEntry(
        watchlist_id=wl.id,
        registration_number="GJ 01 AB 9999",
        registration_normalized="GJ01AB9999",
        category=WatchlistCategory.STOLEN.value,
        priority=WatchlistPriority.HIGH.value,
    )
    db_session.add(entry)
    await db_session.flush()

    # Create matching vehicle event
    event = VehicleEvent(
        camera_id=cam.id,
        event_time=datetime.now(timezone.utc),
        plate_raw="GJ 01 AB 9999",
        plate_normalized="GJ01AB9999",
        plate_confidence=0.99,
        vehicle_class="car",
        latitude=cam.latitude,
        longitude=cam.longitude,
        location_name="Test Junction",
    )
    db_session.add(event)
    await db_session.flush()

    # Create Alert
    alert = Alert(
        vehicle_event_id=event.id,
        watchlist_entry_id=entry.id,
        camera_id=cam.id,
        registration_number="GJ01AB9999",
        category="STOLEN",
        priority="HIGH",
        status=AlertStatus.NEW.value,
        alert_time=datetime.now(timezone.utc),
        confidence=0.99,
        location_name="Test Junction",
    )
    db_session.add(alert)
    await db_session.commit()

    alert_query = await db_session.execute(select(Alert).where(Alert.status == "NEW"))
    fetched_alert = alert_query.scalars().first()
    assert fetched_alert is not None
    assert fetched_alert.registration_number == "GJ01AB9999"
    assert fetched_alert.priority == "HIGH"
    assert fetched_alert.watchlist_entry is not None
    assert fetched_alert.watchlist_entry.category == "STOLEN"


@pytest.mark.asyncio
async def test_evidence_and_audit_logging(db_session: AsyncSession):
    """Test Evidence record with SHA-256 hash and AuditLog entry."""
    cam = Camera(
        external_camera_id="CAM_EVID_TEST",
        name="Evidence Cam",
        latitude=23.0,
        longitude=72.5,
        rtsp_url="rtsp://localhost:8554/test",
    )
    db_session.add(cam)
    await db_session.flush()

    evidence = Evidence(
        camera_id=cam.id,
        file_path="./data/evidence/snapshots/2026/09/08/snap_01.jpg",
        file_type="SNAPSHOT",
        file_size_bytes=1048576,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        captured_at=datetime.now(timezone.utc),
    )
    audit = AuditLog(
        username="inspector_patel",
        action="VEHICLE_SEARCH",
        resource_type="VEHICLE",
        resource_id="GJ01AB1234",
        timestamp=datetime.now(timezone.utc),
        ip_address="192.168.1.100",
        details="Searched vehicle history across all cameras",
    )
    db_session.add_all([evidence, audit])
    await db_session.commit()

    evid_res = await db_session.execute(select(Evidence).where(Evidence.camera_id == cam.id))
    fetched_evid = evid_res.scalars().first()
    assert fetched_evid is not None
    assert len(fetched_evid.sha256_hash) == 64

    audit_res = await db_session.execute(
        select(AuditLog).where(AuditLog.username == "inspector_patel")
    )
    fetched_audit = audit_res.scalars().first()
    assert fetched_audit is not None
    assert fetched_audit.action == "VEHICLE_SEARCH"
