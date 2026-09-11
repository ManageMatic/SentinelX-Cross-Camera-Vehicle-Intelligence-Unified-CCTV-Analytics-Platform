"""Comprehensive Unit and Integration Tests for Sentinel CCTV Integration.

Tests RTSP URL builder, camera ID validator (SSRF prevention), secret redaction,
exponential backoff calculations, dynamic camera sync, and test/health endpoints.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from app.core.exceptions import ValidationException
from app.integrations.sentinel.client import SentinelClient, sentinel_client
from app.integrations.sentinel.rtsp import (
    build_public_rtsp_path,
    build_rtsp_url,
    redact_url,
    validate_camera_id,
)
from app.services.camera_catalog import catalog_service
from app.video.stream_manager import video_stream_manager
from httpx import ASGITransport, AsyncClient


# 1. Camera ID Validation & SSRF Prevention
def test_validate_camera_id_valid():
    """Verify valid camera identifiers pass validation."""
    assert validate_camera_id("cam01") == "cam01"
    assert validate_camera_id("cam30") == "cam30"
    assert validate_camera_id("CAM-05") == "CAM-05"
    assert validate_camera_id("ahmedabad_cctv_01") == "ahmedabad_cctv_01"


def test_validate_camera_id_invalid_ssrf():
    """Verify malicious or invalid camera IDs raise ValidationException."""
    invalid_ids = [
        "",
        "cam01/../../etc/passwd",
        "cam01@evil.com",
        "http://evil.com/stream",
        "rtsp://10.0.0.1",
        "cam 01",  # whitespace
        "cam01;rm -rf /",
        "cam01?query=1",
        "cam01#fragment",
    ]
    for invalid_id in invalid_ids:
        with pytest.raises(ValidationException):
            validate_camera_id(invalid_id)


# 2. RTSP URL Builder & Credential Encoding
def test_build_rtsp_url_unauthenticated():
    """Verify unauthenticated RTSP URL construction."""
    url = build_rtsp_url(
        camera_id="cam01",
        host="103.250.160.189",
        port=8554,
        username="",
        access_code="",
    )
    assert url == "rtsp://103.250.160.189:8554/stream/cam01"


def test_build_rtsp_url_authenticated_encoding():
    """Verify special characters in email and access code are URL-encoded."""
    url = build_rtsp_url(
        camera_id="cam02",
        host="103.250.160.189",
        port=8554,
        username="officer@police.gov.in",
        access_code="Code#123/Secret%",
    )
    assert "officer%40police.gov.in" in url
    assert "Code%23123%2FSecret%25" in url
    assert url.endswith("/stream/cam02")


def test_build_public_rtsp_path():
    """Verify public RTSP path is relative and contains no credentials."""
    path = build_public_rtsp_path("cam15")
    assert path == "/stream/cam15"


# 3. Universal Secret Redaction
def test_redact_url():
    """Verify passwords and access codes are masked in URLs."""
    raw_url = "rtsp://ishan%40gmail.com:SecretAccessCode123@103.250.160.189:8554/stream/cam01"
    redacted = redact_url(raw_url)
    assert "SecretAccessCode123" not in redacted
    assert "rtsp://***:***@103.250.160.189:8554/stream/cam01" == redacted

    http_url = "http://user:pass123@103.250.160.189:8889/stream/cam01/whep"
    assert redact_url(http_url) == "http://***:***@103.250.160.189:8889/stream/cam01/whep"


# 4. Exponential Backoff Reconnect Calculation
def test_calculate_reconnect_delay():
    """Verify exponential reconnect delay sequence: 1s, 2s, 4s, 8s, 16s, max 30s."""
    client = SentinelClient()
    assert client.calculate_reconnect_delay(0) == 1.0
    assert client.calculate_reconnect_delay(1) == 2.0
    assert client.calculate_reconnect_delay(2) == 4.0
    assert client.calculate_reconnect_delay(3) == 8.0
    assert client.calculate_reconnect_delay(4) == 16.0
    assert client.calculate_reconnect_delay(5) == 30.0
    assert client.calculate_reconnect_delay(10) == 30.0  # capped at max_delay


# 5. Dynamic Camera Fallback Generator
def test_generate_fallback_cameras():
    """Verify fallback camera generator creates configured camera range."""
    cams = catalog_service.generate_fallback_cameras()
    assert len(cams) == 30
    assert cams[0]["camera_id"] == "cam01"
    assert cams[29]["camera_id"] == "cam30"
    assert "Ahmedabad" in cams[0]["location_name"] or "SG Highway" in cams[0]["location_name"]


# 6. API Endpoints (Sync, Health, Test, Preview)
@pytest.mark.asyncio
async def test_camera_sync_and_list_endpoints(async_client):
    """Verify POST /api/cameras/sync and GET /api/cameras endpoints."""
    # Trigger dynamic sync
    sync_res = await async_client.post("/api/cameras/sync")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()["data"]
    assert sync_data["total_discovered"] >= 30

    # List cameras
    list_res = await async_client.get("/api/cameras?page_size=50")
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert len(list_data) >= 30
    assert any(c["external_camera_id"] == "cam01" for c in list_data)


@pytest.mark.asyncio
async def test_camera_test_endpoint_mock(async_client):
    """Verify POST /api/cameras/{camera_id}/test returns structured test result."""
    with patch.object(
        sentinel_client,
        "test_camera",
        return_value={
            "camera_id": "cam01",
            "reachable": True,
            "first_frame_received": True,
            "codec": "h264",
            "width": 1920,
            "height": 1080,
            "fps": 25.0,
            "latency_ms": 14.5,
            "message": "Camera connection and frame grab successful.",
        },
    ):
        res = await async_client.post("/api/cameras/cam01/test")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["camera_id"] == "cam01"
        assert data["reachable"] is True
        assert data["first_frame_received"] is True
        assert data["width"] == 1920


@pytest.mark.asyncio
async def test_camera_health_endpoint(async_client):
    """Verify GET /api/cameras/{camera_id}/health returns live telemetry."""
    res = await async_client.get("/api/cameras/cam01/health")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["camera_id"] == "cam01"
    assert "measured_fps" in data
    assert "latency_ms" in data
    assert "reconnect_count" in data


@pytest.mark.asyncio
async def test_camera_preview_endpoint(async_client):
    """Verify GET /api/cameras/{camera_id}/preview returns image/jpeg content."""
    res = await async_client.get("/api/cameras/cam01/preview")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/jpeg"
    assert len(res.content) > 0


# 7. Optional Live Sentinel Integration Test (Guarded by RUN_SENTINEL_INTEGRATION_TESTS)
@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_SENTINEL_INTEGRATION_TESTS", "").lower() != "true",
    reason="Set RUN_SENTINEL_INTEGRATION_TESTS=true to run live CCTV network probe",
)
async def test_live_sentinel_cam01_connectivity():
    """Live probe against official Sentinel CCTV stream (CAM01)."""
    result = await sentinel_client.test_camera("cam01", timeout_seconds=8.0)
    assert result["camera_id"] == "cam01"
    print(f"\nLive Sentinel CAM01 Test Result: {result}")
