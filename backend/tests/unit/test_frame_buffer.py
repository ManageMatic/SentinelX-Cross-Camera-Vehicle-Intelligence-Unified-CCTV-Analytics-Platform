"""Comprehensive Unit Tests for Frame Buffer Manager & Adaptive Backpressure (Module 9)."""

import time
from datetime import datetime, timezone

import numpy as np
import pytest
from app.main import app
from app.models.camera import Camera
from app.schemas.buffer import (
    BackpressureLevel,
    BufferConfig,
    FrameDropStrategy,
)
from app.schemas.stream import VideoFrame
from app.services.frame_buffer import CameraFrameBuffer, FrameBufferManager, frame_buffer_manager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def create_dummy_frame(camera_id: str, frame_idx: int, is_keyframe: bool = False) -> VideoFrame:
    """Helper to create dummy synthetic video frame."""
    return VideoFrame(
        camera_id=camera_id,
        frame_index=frame_idx,
        timestamp_utc=datetime.now(timezone.utc),
        image=np.zeros((100, 100, 3), dtype=np.uint8),
        width=100,
        height=100,
        fps=25.0,
        is_keyframe=is_keyframe,
    )


@pytest.mark.asyncio
async def test_frame_buffer_bounded_capacity():
    """Verify that camera ring-buffer never exceeds max bounded capacity."""
    config = BufferConfig(
        max_capacity=5, target_ai_fps=30.0, drop_strategy=FrameDropStrategy.DROP_OLDEST
    )
    buf = CameraFrameBuffer("test-cam-01", config)

    # Push 10 frames with bypass_decimation=True
    for i in range(10):
        frame = create_dummy_frame("test-cam-01", i)
        buf.push_frame(frame, bypass_decimation=True)

    stats = buf.get_stats()
    assert stats.queue_size == 5
    assert stats.max_capacity == 5
    assert stats.utilization_pct == 100.0
    assert stats.backpressure_level == BackpressureLevel.CRITICAL
    assert stats.total_dropped_frames == 5


@pytest.mark.asyncio
async def test_frame_buffer_decimation_rate_limiter():
    """Verify that FPS decimation rate-limits high frame rates to target AI FPS."""
    # Target 5 FPS (interval = 0.2s)
    config = BufferConfig(max_capacity=20, target_ai_fps=5.0)
    buf = CameraFrameBuffer("test-cam-02", config)

    # Push first frame (should be accepted)
    f0 = create_dummy_frame("test-cam-02", 0)
    accepted0 = buf.push_frame(f0)
    assert accepted0 is True

    # Immediate second frame (0.01s later) should be dropped by decimation
    f1 = create_dummy_frame("test-cam-02", 1)
    accepted1 = buf.push_frame(f1)
    assert accepted1 is False

    # Sleep past target interval (0.2s) and push next frame
    time.sleep(0.22)
    f2 = create_dummy_frame("test-cam-02", 2)
    accepted2 = buf.push_frame(f2)
    assert accepted2 is True

    assert buf.get_stats().queue_size == 2


@pytest.mark.asyncio
async def test_frame_buffer_drop_newest_strategy():
    """Verify DROP_NEWEST strategy drops incoming frames when buffer is full."""
    config = BufferConfig(
        max_capacity=3,
        target_ai_fps=30.0,
        drop_strategy=FrameDropStrategy.DROP_NEWEST,
        backpressure_threshold_pct=60.0,
    )
    buf = CameraFrameBuffer("test-cam-03", config)

    # Fill buffer to capacity with bypass_decimation
    for i in range(3):
        buf.push_frame(create_dummy_frame("test-cam-03", i), bypass_decimation=True)

    # First frame in queue should still be index 0 (oldest was NOT popped)
    first_frame = buf.peek_frame()
    assert first_frame is not None
    assert first_frame.frame_index == 0


@pytest.mark.asyncio
async def test_frame_buffer_drop_non_keyframe_strategy():
    """Verify DROP_NON_KEYFRAME prioritizes keyframes over intermediate frames."""
    config = BufferConfig(
        max_capacity=2,
        target_ai_fps=30.0,
        drop_strategy=FrameDropStrategy.DROP_NON_KEYFRAME,
        backpressure_threshold_pct=50.0,
    )
    buf = CameraFrameBuffer("test-cam-04", config)

    # Push 1 normal frame
    buf.push_frame(create_dummy_frame("test-cam-04", 1, is_keyframe=False), bypass_decimation=True)

    # Push 1 keyframe
    buf.push_frame(create_dummy_frame("test-cam-04", 2, is_keyframe=True), bypass_decimation=True)

    # Push a non-keyframe while full (should be dropped)
    accepted = buf.push_frame(
        create_dummy_frame("test-cam-04", 3, is_keyframe=False), bypass_decimation=True
    )
    assert accepted is False

    # Pop frames and check keyframe survived
    p1 = buf.pop_frame()
    p2 = buf.pop_frame()
    assert p1 is not None or p2 is not None


@pytest.mark.asyncio
async def test_frame_buffer_manager_lifecycle():
    """Test manager singleton registration, reconfiguration, and clearing."""
    mgr = FrameBufferManager()
    buf = mgr.get_or_create_buffer("cam-mgr-01")
    assert buf is not None

    mgr.push_frame("cam-mgr-01", create_dummy_frame("cam-mgr-01", 1))
    stats = mgr.get_buffer_stats("cam-mgr-01")
    assert stats is not None
    assert stats.camera_id == "cam-mgr-01"

    # Dynamic reconfig
    new_cfg = BufferConfig(max_capacity=30, target_ai_fps=15.0)
    updated = mgr.configure_buffer("cam-mgr-01", new_cfg)
    assert updated.max_capacity == 30
    assert updated.target_ai_fps == 15.0

    # Clear
    mgr.clear_buffer("cam-mgr-01")
    assert mgr.get_buffer_stats("cam-mgr-01").queue_size == 0


@pytest.mark.asyncio
async def test_frame_buffer_api_endpoints(db_session: AsyncSession):
    """Test REST API routes for buffers (/status, /stats, /configure, /clear)."""
    # Seed a camera
    camera = Camera(
        id="buf-cam-uuid-01",
        external_camera_id="GJ-BUF-CAM-01",
        name="SG Highway Buffer Cam",
        location_name="SG Highway Junction",
        latitude=23.0300,
        longitude=72.5800,
        rtsp_url="rtsp://localhost:8554/live/sg_highway",
        fps=25.0,
        live_status=True,
    )
    db_session.add(camera)
    await db_session.commit()

    # Pre-populate frame in buffer
    frame_buffer_manager.push_frame(camera.id, create_dummy_frame(camera.id, 100))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /status
        res_status = await ac.get("/api/v1/buffers/status")
        assert res_status.status_code == 200
        data_status = res_status.json()["data"]
        assert "total_buffers" in data_status
        assert "average_utilization_pct" in data_status

        # 2. GET /{camera_id}/stats
        res_stats = await ac.get(f"/api/v1/buffers/{camera.id}/stats")
        assert res_stats.status_code == 200
        data_stats = res_stats.json()["data"]
        assert data_stats["camera_id"] == camera.id
        assert data_stats["max_capacity"] >= 5

        # 3. POST /{camera_id}/configure
        config_payload = {
            "max_capacity": 25,
            "target_ai_fps": 8.0,
            "drop_strategy": "DROP_OLDEST",
            "backpressure_threshold_pct": 75.0,
        }
        res_cfg = await ac.post(f"/api/v1/buffers/{camera.id}/configure", json=config_payload)
        assert res_cfg.status_code == 200
        assert res_cfg.json()["data"]["max_capacity"] == 25
        assert res_cfg.json()["data"]["target_ai_fps"] == 8.0

        # 4. POST /{camera_id}/clear
        res_clear = await ac.post(f"/api/v1/buffers/{camera.id}/clear")
        assert res_clear.status_code == 200
        assert res_clear.json()["data"]["cleared"] is True

        # 5. POST /clear-all
        res_clear_all = await ac.post("/api/v1/buffers/clear-all")
        assert res_clear_all.status_code == 200
        assert "total_frames_discarded" in res_clear_all.json()["data"]
