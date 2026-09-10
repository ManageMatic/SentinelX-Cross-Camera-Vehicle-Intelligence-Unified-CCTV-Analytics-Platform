"""Unit tests for Real-Time Watchlist & Hotlist Matching Engine (Module 18)."""

import pytest
from app.models.camera import Camera
from app.schemas.watchlist import (
    AlertAcknowledgeRequest,
    BulkWatchlistImportItem,
    BulkWatchlistImportRequest,
    WatchlistCreate,
    WatchlistEntryCreate,
    WatchlistMatchEvaluationRequest,
)
from app.services.watchlist_service import WatchlistMatchingEngine


@pytest.fixture
def test_wl_engine():
    return WatchlistMatchingEngine()


@pytest.mark.asyncio
async def test_watchlist_exact_match_and_alert_generation(db_session, test_wl_engine):
    # Setup test camera
    cam = Camera(
        id="cam_wl_01",
        external_camera_id="EXT_WL_01",
        name="SG Checkpoint 1",
        latitude=23.0225,
        longitude=72.5714,
        location_name="SG Checkpoint",
        rtsp_url="rtsp://127.0.0.1:8554/cam_wl_01",
    )
    db_session.add(cam)

    # 1. Create Watchlist and Entry
    w = await test_wl_engine.create_watchlist(
        db_session,
        WatchlistCreate(
            name="Stolen Vehicles Hotlist Ahmedabad",
            category="STOLEN",
            description="Active stolen vehicles tracked by crime branch",
        ),
    )

    await test_wl_engine.create_entry(
        db_session,
        WatchlistEntryCreate(
            watchlist_id=w.id,
            registration_number="GJ 01 STOLEN 1",
            registration_normalized="GJ01STOLEN1",
            category="STOLEN",
            priority="CRITICAL",
            notes="Armed robbery getaway vehicle",
        ),
    )

    # 2. Evaluate Exact Match
    req_hit = WatchlistMatchEvaluationRequest(
        plate="GJ01STOLEN1",
        camera_id="cam_wl_01",
        confidence=0.98,
        location_name="SG Checkpoint",
    )
    res_hit = await test_wl_engine.evaluate_plate(db_session, req_hit)

    assert res_hit.is_match is True
    assert res_hit.match_type == "EXACT"
    assert res_hit.category == "STOLEN"
    assert res_hit.priority == "CRITICAL"
    assert res_hit.alert_generated is True
    assert res_hit.alert_id is not None
    assert res_hit.evaluation_time_ms < 50.0

    # 3. Evaluate Miss
    req_miss = WatchlistMatchEvaluationRequest(
        plate="GJ01CLEAN1",
        camera_id="cam_wl_01",
    )
    res_miss = await test_wl_engine.evaluate_plate(db_session, req_miss)
    assert res_miss.is_match is False
    assert res_miss.alert_generated is False


@pytest.mark.asyncio
async def test_wildcard_and_fuzzy_watchlist_matching(db_session, test_wl_engine):
    cam = Camera(
        id="cam_wl_wild_01",
        external_camera_id="EXT_WL_WILD_01",
        name="Toll Plaza Alpha",
        latitude=23.0500,
        longitude=72.6000,
        location_name="Toll Plaza",
        rtsp_url="rtsp://127.0.0.1:8554/cam_wl_wild_01",
    )
    db_session.add(cam)

    w = await test_wl_engine.create_watchlist(
        db_session,
        WatchlistCreate(name="Pattern Watchlist", category="WANTED"),
    )

    # Wildcard entry: GJ01??9999
    await test_wl_engine.create_entry(
        db_session,
        WatchlistEntryCreate(
            watchlist_id=w.id,
            registration_number="GJ01*9999",
            registration_normalized="GJ01*9999",
            category="WANTED",
            priority="HIGH",
        ),
    )

    # Evaluate pattern match
    res_wild = await test_wl_engine.evaluate_plate(
        db_session,
        WatchlistMatchEvaluationRequest(plate="GJ01AB9999", camera_id="cam_wl_wild_01"),
    )
    assert res_wild.is_match is True
    assert res_wild.match_type == "WILDCARD"


@pytest.mark.asyncio
async def test_bulk_import_and_acknowledgment(db_session, test_wl_engine):
    # 1. Bulk import
    bulk_req = BulkWatchlistImportRequest(
        watchlist_name="Statewide Stolen DB",
        category="STOLEN",
        items=[
            BulkWatchlistImportItem(
                registration_number="GJ01AA1111", category="STOLEN", priority="HIGH"
            ),
            BulkWatchlistImportItem(
                registration_number="GJ01BB2222", category="STOLEN", priority="CRITICAL"
            ),
        ],
    )
    import_res = await test_wl_engine.bulk_import(db_session, bulk_req)
    assert import_res.imported_count == 2

    # 2. Trigger an alert
    cam = Camera(
        id="cam_ack_01",
        external_camera_id="EXT_ACK_01",
        name="Ring Road East",
        latitude=23.0000,
        longitude=72.5000,
        location_name="Ring Road",
        rtsp_url="rtsp://127.0.0.1:8554/cam_ack_01",
    )
    db_session.add(cam)
    await db_session.commit()

    eval_res = await test_wl_engine.evaluate_plate(
        db_session,
        WatchlistMatchEvaluationRequest(plate="GJ01AA1111", camera_id="cam_ack_01"),
    )
    assert eval_res.alert_id is not None

    # 3. Acknowledge alert
    ack_req = AlertAcknowledgeRequest(
        operator_name="Inspector R. Sharma (Badge #4492)",
        status="ACKNOWLEDGED",
        resolution_notes="Patrol intercept unit dispatched to Ring Road",
    )
    ack_res = await test_wl_engine.acknowledge_alert(db_session, eval_res.alert_id, ack_req)
    assert ack_res is not None
    assert ack_res.status == "ACKNOWLEDGED"
    assert ack_res.acknowledged_by == "Inspector R. Sharma (Badge #4492)"


@pytest.mark.asyncio
async def test_watchlist_api_endpoints(async_client):
    # 1. Create watchlist container via API
    w_payload = {
        "name": "API Test VIP Escort Watchlist",
        "category": "VIP_ESCORT",
        "description": "Dignitary motorcade tracker",
    }
    w_resp = await async_client.post("/api/v1/watchlist", json=w_payload)
    assert w_resp.status_code == 201
    w_id = w_resp.json()["data"]["id"]

    # 2. Add entry via API
    entry_payload = {
        "watchlist_id": w_id,
        "registration_number": "GJ01VIP9999",
        "category": "VIP_ESCORT",
        "priority": "HIGH",
    }
    e_resp = await async_client.post("/api/v1/watchlist/entries", json=entry_payload)
    assert e_resp.status_code == 201

    # 3. Evaluate plate via API
    eval_payload = {
        "plate": "GJ01VIP9999",
        "camera_id": "cam_api_test_wl",
        "confidence": 0.99,
        "location_name": "VIP Gate 1",
    }
    eval_resp = await async_client.post("/api/v1/watchlist/evaluate", json=eval_payload)
    assert eval_resp.status_code == 200
    assert eval_resp.json()["data"]["is_match"] is True

    # 4. Fetch alerts
    alerts_resp = await async_client.get("/api/v1/watchlist/alerts")
    assert alerts_resp.status_code == 200
    assert len(alerts_resp.json()["data"]) >= 1

    # 5. Fetch telemetry
    telem_resp = await async_client.get("/api/v1/watchlist/telemetry")
    assert telem_resp.status_code == 200
    assert telem_resp.json()["data"]["total_evaluations"] >= 1
