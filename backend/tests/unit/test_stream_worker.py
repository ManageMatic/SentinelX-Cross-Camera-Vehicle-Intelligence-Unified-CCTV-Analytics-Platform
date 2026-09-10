"""Comprehensive Unit Tests for RTSP / TCP Stream Ingestion Worker (Module 6)."""

import time

import pytest
from app.main import app
from app.models.camera import Camera
from app.schemas.stream import StreamWorkerState
from app.services.stream_worker import RTSPStreamWorker, stream_pool
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_rtsp_worker_synthetic_stream():
    """Verify that RTSPStreamWorker decodes synthetic frames, computes FPS, and stops cleanly."""
    captured_frames = []

    def frame_handler(frame):
        captured_frames.append(frame)

    worker = RTSPStreamWorker(
        camera_id="test-cam-uuid-01",
        external_camera_id="TEST-STREAM-CAM-01",
        rtsp_url="rtsp://127.0.0.1:8554/live/test01",
        target_fps=30.0,
        use_synthetic_stream=True,
        frame_callback=frame_handler,
    )

    worker.start()
    assert worker.state in (StreamWorkerState.CONNECTING, StreamWorkerState.STREAMING)

    # Let worker generate frames for 0.25 seconds
    time.sleep(0.25)

    stats = worker.get_stats()
    assert stats.total_frames_read >= 2
    assert stats.state == StreamWorkerState.STREAMING
    assert stats.transport_protocol == "TCP"

    latest_frame = worker.get_latest_frame()
    assert latest_frame is not None
    assert latest_frame.camera_id == "test-cam-uuid-01"
    assert latest_frame.width == 1920
    assert latest_frame.height == 1080
    assert latest_frame.image.shape == (1080, 1920, 3)
    assert len(captured_frames) >= 2

    # Stop worker cleanly
    worker.stop()
    assert worker.state == StreamWorkerState.STOPPED


@pytest.mark.asyncio
async def test_stream_worker_pool_management():
    """Verify StreamWorkerPool lifecycle, status aggregation, and frame dispatch."""
    cam_id = "pool-cam-uuid-02"
    stream_pool.start_worker(
        camera_id=cam_id,
        external_camera_id="POOL-CAM-02",
        rtsp_url="rtsp://127.0.0.1:8554/live/pool02",
        target_fps=25.0,
        use_synthetic_stream=True,
    )

    time.sleep(0.2)

    # Check pool status
    pool_status = stream_pool.get_pool_status()
    assert pool_status.total_active_workers >= 1
    assert pool_status.streaming_count >= 1

    # Check frame retrieval from pool
    frame = stream_pool.get_latest_frame(cam_id)
    assert frame is not None
    assert frame.width == 1920

    # Stop worker
    stream_pool.stop_worker(cam_id)
    assert stream_pool.get_worker(cam_id) is None


@pytest.mark.asyncio
async def test_stream_api_endpoints(db_session: AsyncSession):
    """Verify REST API endpoints for starting, monitoring, and stopping stream workers."""
    # 1. Create test camera in database
    camera = Camera(
        external_camera_id="API-STREAM-CAM-03",
        name="Stream Test Camera 03",
        location_name="Ahmedabad SG Highway",
        department="Traffic Police",
        latitude=23.0338,
        longitude=72.5072,
        rtsp_url="rtsp://127.0.0.1:8554/live/api_stream_03",
        fps=25.0,
        live_status=True,
    )
    db_session.add(camera)
    await db_session.commit()
    await db_session.refresh(camera)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 2. Start worker via POST /api/v1/streams/{id}/start
        resp_start = await client.post(f"/api/v1/streams/{camera.id}/start?use_synthetic=true")
        assert resp_start.status_code == 200
        data_start = resp_start.json()
        assert data_start["success"] is True
        assert data_start["data"]["camera_id"] == camera.id

        # Let worker run briefly
        time.sleep(0.15)

        # 3. Get pool status via GET /api/v1/streams/status
        resp_status = await client.get("/api/v1/streams/status")
        assert resp_status.status_code == 200
        data_status = resp_status.json()
        assert data_status["success"] is True
        assert data_status["data"]["total_active_workers"] >= 1

        # 4. Get individual stats via GET /api/v1/streams/{id}/stats
        resp_stats = await client.get(f"/api/v1/streams/{camera.id}/stats")
        assert resp_stats.status_code == 200
        data_stats = resp_stats.json()
        assert data_stats["data"]["external_camera_id"] == "API-STREAM-CAM-03"

        # 5. Stop worker via POST /api/v1/streams/{id}/stop
        resp_stop = await client.post(f"/api/v1/streams/{camera.id}/stop")
        assert resp_stop.status_code == 200
        data_stop = resp_stop.json()
        assert data_stop["data"]["stopped"] is True
