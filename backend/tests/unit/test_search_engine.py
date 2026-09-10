"""Unit tests for Sub-200ms Vehicle Search Engine (Module 15)."""

from datetime import datetime, timedelta, timezone

import pytest
from app.models.camera import Camera
from app.models.vehicle import VehicleEvent
from app.schemas.search import VehicleSearchQuery
from app.services.search_engine import (
    VehicleSearchEngine,
    haversine_distance_km,
    levenshtein_distance,
)


@pytest.fixture
def test_search_engine():
    return VehicleSearchEngine()


def test_levenshtein_distance():
    assert levenshtein_distance("GJ01AB1234", "GJ01AB1234") == 0
    assert levenshtein_distance("GJ01AB1234", "GJO1AB1234") == 1  # 0 vs O
    assert levenshtein_distance("GJ01AB1234", "GJ01AB1235") == 1  # 4 vs 5
    assert levenshtein_distance("GJ01AB1234", "MH02CD5678") > 4


def test_haversine_distance():
    # Distance between Ahmedabad (23.0225, 72.5714) and Gandhinagar (23.2156, 72.6369) ~ 22-25 km
    dist = haversine_distance_km(23.0225, 72.5714, 23.2156, 72.6369)
    assert 20.0 <= dist <= 26.0

    # Self-distance should be 0.0
    assert haversine_distance_km(23.0225, 72.5714, 23.0225, 72.5714) == 0.0


@pytest.mark.asyncio
async def test_search_exact_and_wildcard(db_session, test_search_engine):
    # Setup camera
    cam = Camera(
        id="cam_search_01",
        external_camera_id="EXT_SEARCH_01",
        name="SG Highway Junction Node",
        latitude=23.0225,
        longitude=72.5714,
        location_name="SG Highway",
        rtsp_url="rtsp://127.0.0.1:8554/cam_search_01",
    )
    db_session.add(cam)

    now = datetime.now(timezone.utc)
    ev1 = VehicleEvent(
        id="ev_01",
        camera_id="cam_search_01",
        event_time=now,
        plate_raw="GJ 01 AB 1234",
        plate_normalized="GJ01AB1234",
        plate_confidence=0.98,
        vehicle_class="car",
        vehicle_color="white",
        detection_confidence=0.95,
        latitude=23.0225,
        longitude=72.5714,
        location_name="SG Highway",
    )
    ev2 = VehicleEvent(
        id="ev_02",
        camera_id="cam_search_01",
        event_time=now - timedelta(minutes=5),
        plate_raw="MH 12 CD 5678",
        plate_normalized="MH12CD5678",
        plate_confidence=0.90,
        vehicle_class="truck",
        vehicle_color="red",
        detection_confidence=0.88,
        latitude=23.0225,
        longitude=72.5714,
        location_name="SG Highway",
    )
    db_session.add_all([ev1, ev2])
    await db_session.commit()

    # 1. Exact plate search
    q_exact = VehicleSearchQuery(plate="GJ01AB1234")
    res_exact = await test_search_engine.search_vehicles(db_session, q_exact)
    assert res_exact.total_count == 1
    assert res_exact.results[0].plate_normalized == "GJ01AB1234"
    assert res_exact.execution_time_ms < 200.0

    # 2. Wildcard plate search (GJ01*)
    q_wildcard = VehicleSearchQuery(plate="GJ01*")
    res_wildcard = await test_search_engine.search_vehicles(db_session, q_wildcard)
    assert res_wildcard.total_count == 1
    assert res_wildcard.results[0].plate_normalized == "GJ01AB1234"

    # 3. Class and color search
    q_class = VehicleSearchQuery(vehicle_classes=["truck"], vehicle_colors=["red"])
    res_class = await test_search_engine.search_vehicles(db_session, q_class)
    assert res_class.total_count == 1
    assert res_class.results[0].plate_normalized == "MH12CD5678"


@pytest.mark.asyncio
async def test_fuzzy_plate_search(db_session, test_search_engine):
    cam = Camera(
        id="cam_fuzzy_01",
        external_camera_id="EXT_FUZZY_01",
        name="Toll Plaza Node",
        latitude=23.0500,
        longitude=72.6000,
        location_name="Ring Road Toll",
        rtsp_url="rtsp://127.0.0.1:8554/cam_fuzzy_01",
    )
    db_session.add(cam)

    ev = VehicleEvent(
        id="ev_fuzzy_target",
        camera_id="cam_fuzzy_01",
        event_time=datetime.now(timezone.utc),
        plate_raw="GJ01AB1234",
        plate_normalized="GJ01AB1234",
        plate_confidence=0.92,
        vehicle_class="suv",
        latitude=23.0500,
        longitude=72.6000,
        location_name="Ring Road Toll",
    )
    db_session.add(ev)
    await db_session.commit()

    # Search with optical character typo 'GJO1AB1234' (O instead of 0)
    fuzzy_results = await test_search_engine.fuzzy_plate_search(
        db_session, query_str="GJO1AB1234", max_distance=2
    )
    assert len(fuzzy_results) >= 1
    assert fuzzy_results[0].plate_normalized == "GJ01AB1234"
    assert fuzzy_results[0].edit_distance == 1
    assert fuzzy_results[0].similarity_score >= 0.85


@pytest.mark.asyncio
async def test_search_api_endpoints(async_client):
    # Ingest a sample event first via events API
    ingest_payload = {
        "camera_id": "cam_search_api_01",
        "plate_raw": "DL01AA0001",
        "plate_normalized": "DL01AA0001",
        "vehicle_class": "car",
        "vehicle_color": "black",
        "detection_confidence": 0.95,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "location_name": "Connaught Place",
    }
    await async_client.post("/api/v1/events/ingest", json=ingest_payload)

    # 1. Search endpoint
    search_payload = {
        "plate": "DL01AA*",
        "vehicle_classes": ["car"],
    }
    resp = await async_client.post("/api/v1/search/vehicles", json=search_payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_count"] >= 1
    assert data["execution_time_ms"] < 200.0

    # 2. Quick lookup endpoint
    resp_quick = await async_client.get("/api/v1/search/quick-lookup/DL01AA0001")
    assert resp_quick.status_code == 200
    assert len(resp_quick.json()["data"]) >= 1

    # 3. Fuzzy search endpoint
    resp_fuzzy = await async_client.get("/api/v1/search/fuzzy-plate?query=DLO1AA0001")
    assert resp_fuzzy.status_code == 200

    # 4. Search telemetry endpoint
    resp_telem = await async_client.get("/api/v1/search/telemetry")
    assert resp_telem.status_code == 200
    telem = resp_telem.json()["data"]
    assert telem["total_searches_executed"] >= 1
    assert telem["sub_200ms_compliance_rate"] >= 80.0
