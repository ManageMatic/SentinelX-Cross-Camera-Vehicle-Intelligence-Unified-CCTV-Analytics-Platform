"""Unit tests for Real-time Vehicle Event Ingestion & Indexer (Module 14)."""

import base64

import pytest
from app.models.camera import Camera
from app.schemas.events import (
    RecentEventsFilter,
    VehicleEventBatchCreate,
    VehicleEventCreate,
)
from app.services.event_indexer import EventIndexerService


@pytest.fixture
def indexer_service():
    return EventIndexerService()


def test_sha256_computation(indexer_service):
    data = b"SentinelX Cryptographic Evidence Proof"
    hash_str = indexer_service.compute_sha256(data)
    assert len(hash_str) == 64
    # Deterministic hash verify
    import hashlib

    assert hash_str == hashlib.sha256(data).hexdigest()


@pytest.mark.asyncio
async def test_ingest_event_db(db_session, indexer_service):
    # Setup test camera
    cam = Camera(
        id="cam_test_indexer_01",
        external_camera_id="EXT_CAM_IDX_01",
        name="Junction Alpha Node",
        latitude=23.0225,
        longitude=72.5714,
        location_name="SG Highway Junction",
        rtsp_url="rtsp://127.0.0.1:8554/cam_test_indexer_01",
    )
    db_session.add(cam)
    await db_session.commit()

    # Small dummy 1x1 image encoded in base64
    dummy_b64 = base64.b64encode(
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb"
    ).decode("utf-8")

    event_in = VehicleEventCreate(
        camera_id="cam_test_indexer_01",
        track_id="trk_8899",
        plate_raw="GJ 01 AB 1234",
        plate_normalized="GJ01AB1234",
        plate_confidence=0.96,
        vehicle_class="car",
        vehicle_color="white",
        detection_confidence=0.92,
        bbox_x1=100.0,
        bbox_y1=150.0,
        bbox_x2=400.0,
        bbox_y2=380.0,
        snapshot_base64=dummy_b64,
        embedding=[0.05] * 512,
    )

    resp = await indexer_service.ingest_event(db_session, event_in)

    assert resp.id is not None
    assert resp.camera_id == "cam_test_indexer_01"
    assert resp.plate_normalized == "GJ01AB1234"
    assert resp.vehicle_class == "car"
    assert resp.vehicle_color == "white"
    assert resp.latitude == 23.0225
    assert resp.longitude == 72.5714
    assert resp.location_name == "SG Highway Junction"
    assert resp.has_embedding is True
    assert len(resp.plates) == 1
    assert resp.plates[0].plate_normalized == "GJ01AB1234"
    assert resp.snapshot_path is not None
    assert resp.sha256_hash is not None


@pytest.mark.asyncio
async def test_batch_ingest_and_recent_filter(db_session, indexer_service):
    cam = Camera(
        id="cam_batch_02",
        external_camera_id="EXT_CAM_BATCH_02",
        name="Ring Road Toll Node",
        latitude=23.0500,
        longitude=72.6000,
        location_name="SP Ring Road",
        rtsp_url="rtsp://127.0.0.1:8554/cam_batch_02",
    )
    db_session.add(cam)
    await db_session.commit()

    events = [
        VehicleEventCreate(
            camera_id="cam_batch_02",
            plate_normalized="GJ01XY9999",
            vehicle_class="suv",
            vehicle_color="black",
        ),
        VehicleEventCreate(
            camera_id="cam_batch_02",
            plate_normalized="GJ05ZZ1111",
            vehicle_class="truck",
            vehicle_color="red",
        ),
    ]

    batch_payload = VehicleEventBatchCreate(events=events)
    results = await indexer_service.ingest_batch(db_session, batch_payload)
    assert len(results) == 2

    # Query in-memory ring buffer with filters
    f_truck = RecentEventsFilter(vehicle_class="truck", limit=10)
    truck_events = indexer_service.get_recent_events(f_truck)
    assert len(truck_events) >= 1
    assert truck_events[0].vehicle_class == "truck"

    f_plate = RecentEventsFilter(plate_query="XY9999", limit=10)
    plate_events = indexer_service.get_recent_events(f_plate)
    assert len(plate_events) >= 1
    assert "GJ01XY9999" in plate_events[0].plate_normalized


def test_indexer_telemetry(indexer_service):
    telem = indexer_service.get_telemetry()
    assert telem.total_events_ingested >= 0
    assert telem.in_memory_ring_buffer_size >= 0
    assert telem.evidence_storage_bytes >= 0


@pytest.mark.asyncio
async def test_events_api_endpoints(async_client):
    # Ingest single event
    payload = {
        "camera_id": "cam_api_test_01",
        "plate_raw": "MH12DE1234",
        "plate_normalized": "MH12DE1234",
        "vehicle_class": "bus",
        "vehicle_color": "blue",
        "detection_confidence": 0.88,
        "latitude": 18.5204,
        "longitude": 73.8567,
        "location_name": "Pune Highway",
        "bbox_x1": 50,
        "bbox_y1": 50,
        "bbox_x2": 500,
        "bbox_y2": 400,
    }
    resp = await async_client.post("/api/v1/events/ingest", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    event_id = data["id"]
    assert data["plate_normalized"] == "MH12DE1234"

    # Get recent events
    resp_recent = await async_client.get("/api/v1/events/recent?plate_query=DE1234")
    assert resp_recent.status_code == 200
    recent_data = resp_recent.json()["data"]
    assert len(recent_data) >= 1

    # Get telemetry
    resp_telem = await async_client.get("/api/v1/events/telemetry")
    assert resp_telem.status_code == 200
    assert resp_telem.json()["data"]["total_events_ingested"] >= 1

    # Get event by ID
    resp_by_id = await async_client.get(f"/api/v1/events/{event_id}")
    assert resp_by_id.status_code == 200
    assert resp_by_id.json()["data"]["id"] == event_id
