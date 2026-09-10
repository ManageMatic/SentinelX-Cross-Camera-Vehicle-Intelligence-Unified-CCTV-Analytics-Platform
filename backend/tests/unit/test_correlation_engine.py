"""Unit tests for Cross-Camera Correlation Engine & Spatial-Temporal Filter (Module 16)."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from app.models.camera import Camera
from app.models.vehicle import VehicleEmbedding, VehicleEvent
from app.schemas.correlation import (
    CloneDetectionRequest,
    CorrelationPlausibility,
    CorrelationRequest,
    VisualMatchRequest,
)
from app.services.correlation_engine import (
    CrossCameraCorrelationEngine,
    cosine_similarity,
)


@pytest.fixture
def corr_engine():
    return CrossCameraCorrelationEngine()


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2), 0.001) == 1.0
    assert pytest.approx(cosine_similarity(v1, v3), 0.001) == 0.0


@pytest.mark.asyncio
async def test_plausible_journey_correlation(db_session, corr_engine):
    # Setup two cameras 10km apart
    cam1 = Camera(
        id="cam_corr_01",
        external_camera_id="EXT_CORR_01",
        name="SG Highway North Node",
        latitude=23.0500,
        longitude=72.5000,
        location_name="SG Highway North",
        rtsp_url="rtsp://127.0.0.1:8554/cam_corr_01",
    )
    cam2 = Camera(
        id="cam_corr_02",
        external_camera_id="EXT_CORR_02",
        name="SG Highway South Node",
        latitude=23.1400,
        longitude=72.5000,
        location_name="SG Highway South",
        rtsp_url="rtsp://127.0.0.1:8554/cam_corr_02",
    )
    db_session.add_all([cam1, cam2])

    t0 = datetime.now(timezone.utc) - timedelta(minutes=20)
    t1 = t0 + timedelta(minutes=10)  # 10 minutes to travel ~10 km = 60 km/h (Plausible)

    ev1 = VehicleEvent(
        id="ev_corr_01",
        camera_id="cam_corr_01",
        event_time=t0,
        plate_normalized="GJ01AB9999",
        vehicle_class="car",
        latitude=23.0500,
        longitude=72.5000,
        location_name="SG Highway North",
    )
    ev2 = VehicleEvent(
        id="ev_corr_02",
        camera_id="cam_corr_02",
        event_time=t1,
        plate_normalized="GJ01AB9999",
        vehicle_class="car",
        latitude=23.1400,
        longitude=72.5000,
        location_name="SG Highway South",
    )
    db_session.add_all([ev1, ev2])
    await db_session.commit()

    req = CorrelationRequest(plate="GJ01AB9999", max_speed_kmh=120.0)
    result = await corr_engine.correlate_vehicle(db_session, req)

    assert result.total_sightings == 2
    assert result.unique_cameras == 2
    assert len(result.nodes) == 2
    assert len(result.hops) == 1
    assert result.hops[0].plausibility == CorrelationPlausibility.PLAUSIBLE
    assert result.anomalies_detected == 0
    assert result.is_cloned_plate_suspected is False


@pytest.mark.asyncio
async def test_impossible_teleport_and_cloned_plate(db_session, corr_engine):
    # Setup two cameras 30km apart
    cam1 = Camera(
        id="cam_tele_01",
        external_camera_id="EXT_TELE_01",
        name="Ahmedabad East",
        latitude=23.0000,
        longitude=72.5000,
        location_name="Ahmedabad East",
        rtsp_url="rtsp://127.0.0.1:8554/cam_tele_01",
    )
    cam2 = Camera(
        id="cam_tele_02",
        external_camera_id="EXT_TELE_02",
        name="Gandhinagar Toll",
        latitude=23.3000,
        longitude=72.5000,
        location_name="Gandhinagar Toll",
        rtsp_url="rtsp://127.0.0.1:8554/cam_tele_02",
    )
    db_session.add_all([cam1, cam2])

    t0 = datetime.now(timezone.utc) - timedelta(minutes=5)
    t1 = t0 + timedelta(seconds=30)  # 30 seconds for 33 km = 3960 km/h (Impossible / Clone)

    ev1 = VehicleEvent(
        id="ev_clone_01",
        camera_id="cam_tele_01",
        event_time=t0,
        plate_normalized="GJ01CLONE1",
        vehicle_class="car",
        latitude=23.0000,
        longitude=72.5000,
        location_name="Ahmedabad East",
    )
    ev2 = VehicleEvent(
        id="ev_clone_02",
        camera_id="cam_tele_02",
        event_time=t1,
        plate_normalized="GJ01CLONE1",
        vehicle_class="car",
        latitude=23.3000,
        longitude=72.5000,
        location_name="Gandhinagar Toll",
    )
    db_session.add_all([ev1, ev2])
    await db_session.commit()

    req = CorrelationRequest(plate="GJ01CLONE1")
    result = await corr_engine.correlate_vehicle(db_session, req)

    assert result.anomalies_detected >= 1
    assert result.is_cloned_plate_suspected is True
    assert result.hops[0].plausibility == CorrelationPlausibility.SIMULTANEOUS_CLONE

    # Test network-wide clone detector
    clone_req = CloneDetectionRequest(time_window_minutes=60, min_distance_km=5.0)
    anomalies = await corr_engine.detect_cloned_plates(db_session, clone_req)
    assert len(anomalies) >= 1
    assert anomalies[0].plate_normalized == "GJ01CLONE1"


@pytest.mark.asyncio
async def test_visual_reid_matching(db_session, corr_engine):
    cam = Camera(
        id="cam_reid_node",
        external_camera_id="EXT_REID_NODE",
        name="ReID Junction",
        latitude=23.0200,
        longitude=72.5800,
        location_name="ReID Junction",
        rtsp_url="rtsp://127.0.0.1:8554/cam_reid_node",
    )
    db_session.add(cam)

    ev = VehicleEvent(
        id="ev_reid_sample",
        camera_id="cam_reid_node",
        event_time=datetime.now(timezone.utc),
        vehicle_class="suv",
        latitude=23.0200,
        longitude=72.5800,
        location_name="ReID Junction",
    )
    db_session.add(ev)

    vec = [0.1] * 512
    # L2 normalize
    vec = [x / (len(vec) ** 0.5 * 0.1) for x in vec]

    emb = VehicleEmbedding(
        id="emb_reid_sample",
        event_id="ev_reid_sample",
        model_name="OSNet-x0.25",
        embedding_dim=512,
        vector_data=json.dumps(vec),
    )
    db_session.add(emb)
    await db_session.commit()

    match_req = VisualMatchRequest(embedding=vec, min_similarity=0.90)
    candidates = await corr_engine.visual_match(db_session, match_req)
    assert len(candidates) >= 1
    assert candidates[0].event_id == "ev_reid_sample"
    assert candidates[0].cosine_similarity >= 0.99


@pytest.mark.asyncio
async def test_correlation_api_endpoints(async_client):
    # Test correlate endpoint
    payload = {"plate": "GJ01TEST99"}
    resp = await async_client.post("/api/v1/correlation/correlate", json=payload)
    assert resp.status_code == 200
    assert resp.json()["data"]["target_query"] == "GJ01TEST99"

    # Test detect-clones endpoint
    resp_clones = await async_client.post("/api/v1/correlation/detect-clones", json={})
    assert resp_clones.status_code == 200

    # Test visual-match endpoint
    dummy_emb = [0.05] * 512
    resp_vis = await async_client.post(
        "/api/v1/correlation/visual-match",
        json={"embedding": dummy_emb, "min_similarity": 0.5},
    )
    assert resp_vis.status_code == 200

    # Test telemetry endpoint
    resp_telem = await async_client.get("/api/v1/correlation/telemetry")
    assert resp_telem.status_code == 200
    assert "total_correlations_executed" in resp_telem.json()["data"]
