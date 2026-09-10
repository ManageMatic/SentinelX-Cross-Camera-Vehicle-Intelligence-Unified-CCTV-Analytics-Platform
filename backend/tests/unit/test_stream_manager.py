"""Comprehensive Unit Tests for Resilient Stream Manager & Auto-Reconnect Engine (Module 7)."""

import time

import pytest
from app.main import app
from app.models.camera import Camera, CameraHealth
from app.schemas.resilience import CircuitBreakerState
from app.services.stream_manager import StreamWatchdogManager, stream_manager
from app.services.stream_worker import stream_pool
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_watchdog_backoff_calculation():
    """Verify exponential backoff algorithm with ceiling limits."""
    manager = StreamWatchdogManager(
        initial_backoff_seconds=1.0,
        max_backoff_seconds=30.0,
        backoff_factor=1.5,
    )

    # 0 failures should be close to 1.0s
    assert 0.8 <= manager.calculate_backoff(0) <= 1.2

    # 1 failure: ~1.5s
    assert 1.2 <= manager.calculate_backoff(1) <= 1.8

    # 2 failures: ~2.25s
    assert 1.9 <= manager.calculate_backoff(2) <= 2.6

    # 20 failures: should cap at 30.0s (+/- jitter)
    assert manager.calculate_backoff(20) <= 33.0


@pytest.mark.asyncio
async def test_circuit_breaker_transitions():
    """Verify that repeated stream failures trip circuit breaker from CLOSED to OPEN, and manual reset works."""
    manager = StreamWatchdogManager(
        stall_timeout_seconds=0.1,
        max_consecutive_failures=3,
        circuit_cooldown_seconds=1.0,
    )

    cam_id = "test-failing-cam-01"

    # 1. Initially stopped worker checked by manager -> fails
    rec_1 = manager.check_camera_health(cam_id)
    assert rec_1.consecutive_failures == 1
    assert rec_1.circuit_state == CircuitBreakerState.CLOSED

    # 2. Second failure
    rec_2 = manager.check_camera_health(cam_id)
    assert rec_2.consecutive_failures == 2
    assert rec_2.circuit_state == CircuitBreakerState.CLOSED

    # 3. Third failure -> should trip circuit to OPEN
    rec_3 = manager.check_camera_health(cam_id)
    assert rec_3.consecutive_failures == 3
    assert rec_3.circuit_state == CircuitBreakerState.OPEN

    # 4. Manual circuit reset -> back to CLOSED
    rec_reset = manager.reset_circuit(cam_id)
    assert rec_reset.circuit_state == CircuitBreakerState.CLOSED
    assert rec_reset.consecutive_failures == 0


@pytest.mark.asyncio
async def test_watchdog_health_summary_and_db_sync(db_session: AsyncSession):
    """Verify health aggregation across streaming workers and database telemetry synchronization."""
    cam_id = "sync-cam-uuid-07"
    camera = Camera(
        id=cam_id,
        external_camera_id="SYNC-CAM-07",
        name="Sync Test Camera 07",
        location_name="Gandhinagar Infocity",
        department="Traffic Police",
        latitude=23.1895,
        longitude=72.6284,
        rtsp_url="rtsp://127.0.0.1:8554/live/sync07",
        fps=25.0,
        live_status=False,
    )
    db_session.add(camera)
    await db_session.commit()

    # Start synthetic worker
    stream_pool.start_worker(
        camera_id=cam_id,
        external_camera_id="SYNC-CAM-07",
        rtsp_url=camera.rtsp_url,
        target_fps=25.0,
        use_synthetic_stream=True,
    )

    time.sleep(0.15)

    # Check health summary
    summary = stream_manager.get_health_summary()
    assert summary.total_monitored >= 1
    assert summary.healthy_count >= 1
    assert summary.aggregate_fps > 0.0

    # Sync to DB
    await stream_manager.sync_health_to_db(db_session)

    # Verify Camera record updated to online
    stmt = select(Camera).where(Camera.id == cam_id)
    updated_cam = (await db_session.execute(stmt)).scalar_one()
    assert updated_cam.live_status is True
    assert updated_cam.last_seen is not None

    # Verify CameraHealth record inserted
    health_stmt = select(CameraHealth).where(CameraHealth.camera_id == cam_id)
    health_rec = (await db_session.execute(health_stmt)).scalar_one_or_none()
    assert health_rec is not None
    assert health_rec.is_online is True

    # Cleanup
    stream_pool.stop_worker(cam_id)


@pytest.mark.asyncio
async def test_resilience_api_endpoints(db_session: AsyncSession):
    """Verify REST API endpoints for health monitoring, force reconnect, and circuit reset."""
    cam_id = "api-resilience-cam-08"
    camera = Camera(
        id=cam_id,
        external_camera_id="API-RESILIENCE-CAM-08",
        name="Resilience Test Camera 08",
        location_name="Ahmedabad SG Highway",
        department="Traffic Police",
        latitude=23.0338,
        longitude=72.5072,
        rtsp_url="rtsp://127.0.0.1:8554/live/resilience08",
        fps=25.0,
        live_status=True,
    )
    db_session.add(camera)
    await db_session.commit()

    stream_pool.start_worker(
        camera_id=cam_id,
        external_camera_id="API-RESILIENCE-CAM-08",
        rtsp_url=camera.rtsp_url,
        target_fps=25.0,
        use_synthetic_stream=True,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/v1/streams/health
        resp_health = await client.get("/api/v1/streams/health")
        assert resp_health.status_code == 200
        data_health = resp_health.json()
        assert data_health["success"] is True
        assert data_health["data"]["healthy_count"] >= 1

        # 2. GET /api/v1/streams/{id}/health
        resp_single = await client.get(f"/api/v1/streams/{cam_id}/health")
        assert resp_single.status_code == 200
        data_single = resp_single.json()
        assert data_single["data"]["camera_id"] == cam_id

        # 3. POST /api/v1/streams/{id}/reconnect
        resp_rec = await client.post(f"/api/v1/streams/{cam_id}/reconnect")
        assert resp_rec.status_code == 200
        data_rec = resp_rec.json()
        assert data_rec["success"] is True

        # 4. POST /api/v1/streams/{id}/reset-circuit
        resp_circuit = await client.post(f"/api/v1/streams/{cam_id}/reset-circuit")
        assert resp_circuit.status_code == 200
        data_circuit = resp_circuit.json()
        assert data_circuit["data"]["circuit_state"] == "CLOSED"

    stream_pool.stop_worker(cam_id)
