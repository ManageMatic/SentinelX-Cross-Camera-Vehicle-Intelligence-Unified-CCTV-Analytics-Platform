"""Unit tests for Real-time WebSocket Alert Dispatcher & Notification Hub (Module 19)."""

import json
from datetime import datetime, timezone

import pytest
from app.main import app
from app.schemas.websocket import AlertBroadcastPayload, WebSocketMessageType
from app.services.alert_dispatcher import AlertDispatcherHub, alert_dispatcher
from starlette.testclient import TestClient


@pytest.fixture
def hub():
    return AlertDispatcherHub()


def test_alert_dispatcher_backlog(hub):
    payload = AlertBroadcastPayload(
        alert_id="alert_test_01",
        registration_number="GJ01STOLEN9",
        category="STOLEN",
        priority="CRITICAL",
        camera_id="cam_01",
        camera_name="SG Highway Node",
        location_name="SG Highway",
        latitude=23.0225,
        longitude=72.5714,
        alert_time=datetime.now(timezone.utc),
        audio_alert=True,
        visual_color="#ef4444",
        message="Stolen car detected",
    )

    # In single-thread sync context
    import asyncio

    asyncio.run(hub.broadcast_alert(payload))

    backlog = hub.get_backlog()
    assert len(backlog) == 1
    assert backlog[0].alert_id == "alert_test_01"

    stats = hub.get_stats()
    assert stats.total_alerts_dispatched == 1
    assert stats.backlog_size == 1


def test_websocket_connection_and_subscription():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/alerts/ws") as websocket:
        # 1. Send Ping
        ping_payload = {"action": "PING", "timestamp": "2026-09-10T14:40:00Z"}
        websocket.send_text(json.dumps(ping_payload))

        resp_text = websocket.receive_text()
        resp = json.loads(resp_text)
        assert resp["type"] == WebSocketMessageType.HEARTBEAT_PONG.value

        # 2. Send Subscription update
        sub_payload = {"action": "SUBSCRIBE", "channels": ["priority:CRITICAL", "category:WANTED"]}
        websocket.send_text(json.dumps(sub_payload))

        sub_resp_text = websocket.receive_text()
        sub_resp = json.loads(sub_resp_text)
        assert sub_resp["type"] == WebSocketMessageType.CLIENT_SUBSCRIBE.value
        assert sub_resp["status"] == "SUCCESS"


def test_websocket_broadcast_reception():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/alerts/ws?channels=all") as websocket:
        import asyncio

        p = AlertBroadcastPayload(
            alert_id="alert_live_01",
            registration_number="MH12AB1234",
            category="WANTED",
            priority="HIGH",
            camera_id="cam_live_01",
            camera_name="Toll Node Alpha",
            location_name="Mumbai Toll",
            latitude=19.0760,
            longitude=72.8777,
            alert_time=datetime.now(timezone.utc),
            audio_alert=True,
            visual_color="#f97316",
            message="Wanted suspect vehicle detected",
        )
        asyncio.run(alert_dispatcher.broadcast_alert(p))

        # Receive broadcast over active websocket
        raw_msg = websocket.receive_text()
        msg = json.loads(raw_msg)
        assert msg["type"] == WebSocketMessageType.ALERT_BROADCAST.value
        assert msg["data"]["alert_id"] == "alert_live_01"
        assert msg["data"]["registration_number"] == "MH12AB1234"


@pytest.mark.asyncio
async def test_alerts_api_endpoints(async_client):
    # 1. Manual broadcast
    payload = {
        "alert_id": "alert_api_broadcast_01",
        "registration_number": "GJ01CRIME99",
        "category": "TERROR_SUSPECT",
        "priority": "CRITICAL",
        "camera_id": "cam_city_gate",
        "camera_name": "City Gate 1",
        "location_name": "North Entry Checkpoint",
        "latitude": 23.0800,
        "longitude": 72.5900,
        "alert_time": "2026-09-10T14:40:00Z",
        "audio_alert": True,
        "visual_color": "#ef4444",
        "message": "Critical Red Alert: Vehicle intercepted",
    }
    resp = await async_client.post("/api/v1/alerts/broadcast", json=payload)
    assert resp.status_code == 200
    assert resp.json()["data"]["alert_id"] == "alert_api_broadcast_01"

    # 2. Get backlog
    resp_backlog = await async_client.get("/api/v1/alerts/backlog")
    assert resp_backlog.status_code == 200
    assert len(resp_backlog.json()["data"]) >= 1

    # 3. Get WS stats
    resp_stats = await async_client.get("/api/v1/alerts/ws-stats")
    assert resp_stats.status_code == 200
    assert resp_stats.json()["data"]["total_alerts_dispatched"] >= 1
