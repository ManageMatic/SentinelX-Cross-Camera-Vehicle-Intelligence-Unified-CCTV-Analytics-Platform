"""Comprehensive Unit Tests for Low-Latency WebRTC (WHEP) & HLS Proxy (Module 8)."""

import time

import pytest
from app.main import app
from app.models.camera import Camera
from app.services.stream_proxy import stream_proxy_service
from app.services.stream_worker import stream_pool
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_whep_sdp_negotiation():
    """Verify that WHEP WebRTC SDP negotiation returns valid SDP answer structure."""
    camera = Camera(
        id="proxy-cam-uuid-01",
        external_camera_id="GJ-AHM-CAM-01",
        name="SG Highway Junction",
        location_name="Ahmedabad Km 12",
        latitude=23.0338,
        longitude=72.5072,
        rtsp_url="rtsp://admin:SecretPass123@10.20.1.50:554/live/cam01",
        whep_url="http://127.0.0.1:8889/gj_ahm_cam_01/whep",
        fps=25.0,
    )

    client_offer = (
        "v=0\r\n"
        "o=- 48291048 2 IN IP4 127.0.0.1\r\n"
        "s=-\r\n"
        "t=0 0\r\n"
        "m=video 9 UDP/TLS/RTP/SAVPF 96\r\n"
    )

    answer_resp = await stream_proxy_service.exchange_whep_sdp(camera, client_offer)
    assert answer_resp.sdp is not None
    assert "v=0" in answer_resp.sdp
    assert "m=video" in answer_resp.sdp
    assert "H264" in answer_resp.sdp


@pytest.mark.asyncio
async def test_stream_proxy_info_sanitization():
    """Verify that stream proxy info exposes safe endpoints without leaking RTSP passwords."""
    camera = Camera(
        id="proxy-cam-uuid-02",
        external_camera_id="GJ-GND-CAM-02",
        name="CH-0 Gandhinagar",
        location_name="Sector 1",
        latitude=23.2156,
        longitude=72.6369,
        rtsp_url="rtsp://admin:SuperSecretPass@192.168.1.100:554/stream1",
        fps=25.0,
        live_status=True,
    )

    info = stream_proxy_service.get_stream_proxy_info(camera)
    assert info.camera_id == "proxy-cam-uuid-02"
    assert info.external_camera_id == "GJ-GND-CAM-02"
    assert info.whep_endpoint == "/api/v1/proxy/proxy-cam-uuid-02/whep"
    assert info.snapshot_endpoint == "/api/v1/proxy/proxy-cam-uuid-02/snapshot"
    # Verify that secret password is NEVER present in the proxy info
    assert "SuperSecretPass" not in str(info.model_dump())


@pytest.mark.asyncio
async def test_camera_snapshot_generation_with_active_worker():
    """Verify JPEG snapshot generation from active stream worker."""
    cam_id = "snapshot-cam-uuid-03"
    stream_pool.start_worker(
        camera_id=cam_id,
        external_camera_id="SNAPSHOT-CAM-03",
        rtsp_url="rtsp://127.0.0.1:8554/live/snap03",
        target_fps=25.0,
        use_synthetic_stream=True,
    )

    time.sleep(0.15)

    jpeg_bytes = stream_proxy_service.get_camera_snapshot_jpeg(cam_id)
    assert len(jpeg_bytes) > 1000
    # Check standard JPEG magic bytes: 0xFF 0xD8 start and 0xFF 0xD9 end
    assert jpeg_bytes[:2] == b"\xff\xd8"
    assert jpeg_bytes[-2:] == b"\xff\xd9"

    stream_pool.stop_worker(cam_id)


@pytest.mark.asyncio
async def test_proxy_api_endpoints(db_session: AsyncSession):
    """Verify REST API proxy endpoints for endpoints catalog, info, WHEP exchange, and snapshot."""
    cam_id = "api-proxy-cam-04"
    camera = Camera(
        id=cam_id,
        external_camera_id="API-PROXY-CAM-04",
        name="API Proxy Test Camera",
        location_name="Ahmedabad S.G. Highway",
        department="Traffic Police",
        latitude=23.0338,
        longitude=72.5072,
        rtsp_url="rtsp://127.0.0.1:8554/live/proxy04",
        fps=25.0,
        live_status=True,
    )
    db_session.add(camera)
    await db_session.commit()

    # Start worker so snapshot has live frame
    stream_pool.start_worker(
        camera_id=cam_id,
        external_camera_id="API-PROXY-CAM-04",
        rtsp_url=camera.rtsp_url,
        target_fps=25.0,
        use_synthetic_stream=True,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/v1/proxy/endpoints
        resp_catalog = await client.get("/api/v1/proxy/endpoints")
        assert resp_catalog.status_code == 200
        data_catalog = resp_catalog.json()
        assert data_catalog["success"] is True
        assert data_catalog["data"]["total_cameras"] >= 1

        # 2. GET /api/v1/proxy/{id}/info
        resp_info = await client.get(f"/api/v1/proxy/{cam_id}/info")
        assert resp_info.status_code == 200
        data_info = resp_info.json()
        assert data_info["data"]["camera_id"] == cam_id
        assert "whep" in data_info["data"]["whep_endpoint"]

        # 3. POST /api/v1/proxy/{id}/whep
        offer_payload = {"sdp": "v=0\r\no=- 12345 2 IN IP4 127.0.0.1\r\ns=-\r\n"}
        resp_whep = await client.post(f"/api/v1/proxy/{cam_id}/whep", json=offer_payload)
        assert resp_whep.status_code == 200
        data_whep = resp_whep.json()
        assert data_whep["success"] is True
        assert "v=0" in data_whep["data"]["sdp"]

        # 4. GET /api/v1/proxy/{id}/snapshot
        resp_snap = await client.get(f"/api/v1/proxy/{cam_id}/snapshot")
        assert resp_snap.status_code == 200
        assert resp_snap.headers["content-type"] == "image/jpeg"
        assert len(resp_snap.content) > 1000
        assert resp_snap.content[:2] == b"\xff\xd8"

    stream_pool.stop_worker(cam_id)
