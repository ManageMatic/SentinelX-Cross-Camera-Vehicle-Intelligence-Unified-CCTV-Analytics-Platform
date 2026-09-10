"""Unit tests for Chronological Journey & Route Timeline Reconstructor (Module 17)."""

from datetime import datetime, timedelta, timezone

import pytest
from app.models.camera import Camera
from app.models.vehicle import VehicleEvent
from app.schemas.journey import JourneyReconstructRequest
from app.services.journey_service import JourneyReconstructorService


@pytest.fixture
def test_journey_service():
    return JourneyReconstructorService()


@pytest.mark.asyncio
async def test_journey_reconstruction_and_geojson(db_session, test_journey_service):
    # Setup 3 cameras along an urban arterial route
    cam1 = Camera(
        id="cam_jny_01",
        external_camera_id="EXT_JNY_01",
        name="Airport Circle Junction",
        latitude=23.0700,
        longitude=72.6200,
        location_name="Airport Circle",
        rtsp_url="rtsp://127.0.0.1:8554/cam_jny_01",
    )
    cam2 = Camera(
        id="cam_jny_02",
        external_camera_id="EXT_JNY_02",
        name="Koba Circle Checkpoint",
        latitude=23.1400,
        longitude=72.6300,
        location_name="Koba Circle",
        rtsp_url="rtsp://127.0.0.1:8554/cam_jny_02",
    )
    cam3 = Camera(
        id="cam_jny_03",
        external_camera_id="EXT_JNY_03",
        name="Infocity Junction",
        latitude=23.1900,
        longitude=72.6300,
        location_name="Infocity Gandhinagar",
        rtsp_url="rtsp://127.0.0.1:8554/cam_jny_03",
    )
    db_session.add_all([cam1, cam2, cam3])

    t0 = datetime.now(timezone.utc) - timedelta(minutes=45)
    t1 = t0 + timedelta(minutes=15)
    t2 = t1 + timedelta(minutes=15)

    ev1 = VehicleEvent(
        id="ev_jny_01",
        camera_id="cam_jny_01",
        event_time=t0,
        plate_normalized="GJ01JOURNEY",
        vehicle_class="car",
        vehicle_color="silver",
        latitude=23.0700,
        longitude=72.6200,
        location_name="Airport Circle",
    )
    ev2 = VehicleEvent(
        id="ev_jny_02",
        camera_id="cam_jny_02",
        event_time=t1,
        plate_normalized="GJ01JOURNEY",
        vehicle_class="car",
        vehicle_color="silver",
        latitude=23.1400,
        longitude=72.6300,
        location_name="Koba Circle",
    )
    ev3 = VehicleEvent(
        id="ev_jny_03",
        camera_id="cam_jny_03",
        event_time=t2,
        plate_normalized="GJ01JOURNEY",
        vehicle_class="car",
        vehicle_color="silver",
        latitude=23.1900,
        longitude=72.6300,
        location_name="Infocity Gandhinagar",
    )
    db_session.add_all([ev1, ev2, ev3])
    await db_session.commit()

    req = JourneyReconstructRequest(plate="GJ01JOURNEY")
    timeline = await test_journey_service.reconstruct_journey(db_session, req)

    assert timeline is not None
    assert timeline.plate_normalized == "GJ01JOURNEY"
    assert timeline.vehicle_class == "car"
    assert timeline.total_stops == 3
    assert len(timeline.waypoints) == 3
    assert len(timeline.legs) == 2
    assert timeline.origin_location == "Airport Circle"
    assert timeline.destination_location == "Infocity Gandhinagar"
    assert timeline.total_distance_km > 10.0

    # Verify GeoJSON RFC 7946 structure
    geojson = timeline.geojson
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 4  # 3 Points + 1 LineString
    assert geojson["features"][0]["geometry"]["type"] == "Point"
    assert geojson["features"][3]["geometry"]["type"] == "LineString"


@pytest.mark.asyncio
async def test_loitering_and_loop_detection(db_session, test_journey_service):
    cam1 = Camera(
        id="cam_loop_01",
        external_camera_id="EXT_LOOP_01",
        name="Sensitive Zone Alpha",
        latitude=23.0100,
        longitude=72.5500,
        location_name="Sensitive Zone Alpha",
        rtsp_url="rtsp://127.0.0.1:8554/cam_loop_01",
    )
    cam2 = Camera(
        id="cam_loop_02",
        external_camera_id="EXT_LOOP_02",
        name="Connecting Link",
        latitude=23.0300,
        longitude=72.5500,
        location_name="Connecting Link",
        rtsp_url="rtsp://127.0.0.1:8554/cam_loop_02",
    )
    db_session.add_all([cam1, cam2])

    t0 = datetime.now(timezone.utc) - timedelta(hours=2)
    # 1. First visit to cam1 with 30 min dwell (loitering)
    ev_a1 = VehicleEvent(
        id="ev_loop_01",
        camera_id="cam_loop_01",
        event_time=t0,
        plate_normalized="GJ01SUSPECT",
        vehicle_class="suv",
        latitude=23.0100,
        longitude=72.5500,
        location_name="Sensitive Zone Alpha",
    )
    ev_a2 = VehicleEvent(
        id="ev_loop_02",
        camera_id="cam_loop_01",
        event_time=t0 + timedelta(minutes=25),
        plate_normalized="GJ01SUSPECT",
        vehicle_class="suv",
        latitude=23.0100,
        longitude=72.5500,
        location_name="Sensitive Zone Alpha",
    )

    # 2. Travel to cam2
    ev_b = VehicleEvent(
        id="ev_loop_03",
        camera_id="cam_loop_02",
        event_time=t0 + timedelta(minutes=45),
        plate_normalized="GJ01SUSPECT",
        vehicle_class="suv",
        latitude=23.0300,
        longitude=72.5500,
        location_name="Connecting Link",
    )

    # 3. Return loop back to cam1
    ev_c = VehicleEvent(
        id="ev_loop_04",
        camera_id="cam_loop_01",
        event_time=t0 + timedelta(minutes=70),
        plate_normalized="GJ01SUSPECT",
        vehicle_class="suv",
        latitude=23.0100,
        longitude=72.5500,
        location_name="Sensitive Zone Alpha",
    )
    db_session.add_all([ev_a1, ev_a2, ev_b, ev_c])
    await db_session.commit()

    req = JourneyReconstructRequest(
        plate="GJ01SUSPECT",
        max_dwell_loiter_minutes=15.0,
        cluster_dwell_seconds=30.0 * 60.0,
    )
    timeline = await test_journey_service.reconstruct_journey(db_session, req)
    assert timeline is not None

    patterns = {p.pattern_type for p in timeline.behavior_patterns}
    assert "LOITERING_DWELL" in patterns or "CIRCULAR_LOOPING_CRUISE" in patterns


@pytest.mark.asyncio
async def test_journey_api_endpoints(async_client):
    # Ingest event to give search target
    payload = {
        "camera_id": "cam_api_jny_01",
        "plate_raw": "GJ01API1234",
        "plate_normalized": "GJ01API1234",
        "vehicle_class": "truck",
        "vehicle_color": "yellow",
        "latitude": 23.0000,
        "longitude": 72.5000,
        "location_name": "Ring Road West",
    }
    await async_client.post("/api/v1/events/ingest", json=payload)

    # 1. Reconstruct endpoint
    resp_rec = await async_client.post(
        "/api/v1/journey/reconstruct",
        json={"plate": "GJ01API1234"},
    )
    assert resp_rec.status_code == 200
    assert resp_rec.json()["data"]["plate_normalized"] == "GJ01API1234"

    # 2. GeoJSON endpoint
    resp_geo = await async_client.get("/api/v1/journey/GJ01API1234/geojson")
    assert resp_geo.status_code == 200
    assert resp_geo.json()["data"]["type"] == "FeatureCollection"

    # 3. Analyze behavior endpoint
    resp_beh = await async_client.post(
        "/api/v1/journey/analyze-behavior",
        json={"plate": "GJ01API1234"},
    )
    assert resp_beh.status_code == 200

    # 4. Telemetry endpoint
    resp_telem = await async_client.get("/api/v1/journey/telemetry")
    assert resp_telem.status_code == 200
    assert resp_telem.json()["data"]["total_journeys_reconstructed"] >= 1
