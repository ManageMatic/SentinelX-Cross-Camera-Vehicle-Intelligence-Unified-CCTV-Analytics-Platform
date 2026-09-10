"""Comprehensive Unit Tests for ByteTrack Multi-Object Tracking Engine (Module 11)."""

from datetime import datetime, timezone

import numpy as np
import pytest
from app.main import app
from app.models.camera import Camera
from app.schemas.detection import BoundingBox, DetectedVehicle, VehicleClass
from app.schemas.tracking import TrackState
from app.services.byte_tracker import (
    ByteTracker,
    KalmanFilterTracker,
    calculate_iou_matrix,
    camera_tracker_manager,
)
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def create_detection(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    conf: float = 0.85,
    frame_idx: int = 1,
    camera_id: str = "cam-trk-test-01",
    v_class: VehicleClass = VehicleClass.CAR,
) -> DetectedVehicle:
    """Helper creating DetectedVehicle instance with pixel and normalized coordinates."""
    w, h = x2 - x1, y2 - y1
    bbox = BoundingBox(
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        norm_x1=x1 / 1920.0,
        norm_y1=y1 / 1080.0,
        norm_x2=x2 / 1920.0,
        norm_y2=y2 / 1080.0,
        width=w,
        height=h,
    )
    return DetectedVehicle(
        camera_id=camera_id,
        frame_index=frame_idx,
        timestamp_utc=datetime.now(timezone.utc),
        vehicle_class=v_class,
        confidence=conf,
        bbox=bbox,
        has_crop=True,
        crop_width=int(w),
        crop_height=int(h),
        color_estimate="White",
    )


@pytest.mark.asyncio
async def test_kalman_filter_step():
    """Verify Kalman Filter initializes, predicts, and updates state without numerical deviation."""
    kf = KalmanFilterTracker()
    measurement = np.array([500.0, 500.0, 1.5, 200.0], dtype=np.float32)

    mean, cov = kf.initiate(measurement)
    assert mean.shape == (8,)
    assert cov.shape == (8, 8)
    assert np.allclose(mean[:4], measurement)

    # Predict
    pred_mean, pred_cov = kf.predict(mean, cov)
    assert pred_mean.shape == (8,)

    # Update with shifted measurement (moving right)
    new_meas = np.array([510.0, 500.0, 1.5, 200.0], dtype=np.float32)
    upd_mean, upd_cov = kf.update(pred_mean, pred_cov, new_meas)
    assert upd_mean[0] > 500.0  # State shifted towards measurement


@pytest.mark.asyncio
async def test_iou_cost_matrix():
    """Verify IoU distance matrix matches identical boxes with 0.0 distance."""
    boxes_a = [np.array([100, 100, 200, 200], dtype=np.float32)]
    boxes_b = [
        np.array([100, 100, 200, 200], dtype=np.float32),  # Identical -> cost 0.0
        np.array([300, 300, 400, 400], dtype=np.float32),  # Disjoint -> cost 1.0
    ]
    cost = calculate_iou_matrix(boxes_a, boxes_b)
    assert cost.shape == (1, 2)
    assert pytest.approx(cost[0, 0], abs=1e-3) == 0.0
    assert pytest.approx(cost[0, 1], abs=1e-3) == 1.0


@pytest.mark.asyncio
async def test_bytetrack_id_continuity_and_trajectory():
    """Verify ByteTracker maintains identical track_id and builds breadcrumbs across sequential frames."""
    tracker = ByteTracker()
    now_utc = datetime.now(timezone.utc)

    # Frame 1: Vehicle appears at x=100
    det_f1 = [create_detection(100.0, 200.0, 250.0, 350.0, conf=0.90, frame_idx=1)]
    tracks_f1 = tracker.update(det_f1, frame_idx=1, timestamp_utc=now_utc)
    assert len(tracks_f1) == 1
    track_id = tracks_f1[0].track_id

    # Frame 2: Vehicle moves smoothly to x=115
    det_f2 = [create_detection(115.0, 200.0, 265.0, 350.0, conf=0.88, frame_idx=2)]
    tracks_f2 = tracker.update(det_f2, frame_idx=2, timestamp_utc=now_utc)
    assert len(tracks_f2) == 1
    assert tracks_f2[0].track_id == track_id  # Track ID MUST be preserved
    assert tracks_f2[0].total_frames_tracked == 2
    assert tracks_f2[0].is_confirmed is True
    assert len(tracks_f2[0].trajectory) == 2

    # Frame 3: Vehicle moves smoothly to x=130
    det_f3 = [create_detection(130.0, 200.0, 280.0, 350.0, conf=0.92, frame_idx=3)]
    tracks_f3 = tracker.update(det_f3, frame_idx=3, timestamp_utc=now_utc)
    assert len(tracks_f3) == 1
    assert tracks_f3[0].track_id == track_id
    assert len(tracks_f3[0].trajectory) == 3


@pytest.mark.asyncio
async def test_bytetrack_best_crop_upgrade():
    """Verify that the highest confidence detection upgrades best_crop_bbox for downstream ANPR."""
    tracker = ByteTracker()
    now_utc = datetime.now(timezone.utc)

    # Frame 1: Vehicle detection with 0.65 confidence
    det1 = [create_detection(100.0, 100.0, 200.0, 200.0, conf=0.65, frame_idx=1)]
    t1 = tracker.update(det1, frame_idx=1, timestamp_utc=now_utc)[0]
    assert t1.best_crop_confidence == 0.65

    # Frame 2: Crisp closer detection with 0.94 confidence
    det2 = [create_detection(105.0, 100.0, 210.0, 205.0, conf=0.94, frame_idx=2)]
    t2 = tracker.update(det2, frame_idx=2, timestamp_utc=now_utc)[0]
    assert t2.best_crop_confidence == 0.94
    assert t2.best_crop_frame_idx == 2


@pytest.mark.asyncio
async def test_bytetrack_low_confidence_second_stage_recovery():
    """Verify 2nd stage association recovers low-score detection (e.g. motion blur / occlusion)."""
    tracker = ByteTracker()
    now_utc = datetime.now(timezone.utc)

    # Frame 1: High confidence detection (0.90)
    det1 = [create_detection(300.0, 300.0, 450.0, 450.0, conf=0.90, frame_idx=1)]
    t1 = tracker.update(det1, frame_idx=1, timestamp_utc=now_utc)[0]
    track_id = t1.track_id

    # Frame 2: Low confidence detection (0.25) due to simulated tree branch occlusion
    det2 = [create_detection(310.0, 305.0, 458.0, 452.0, conf=0.25, frame_idx=2)]
    tracks_f2 = tracker.update(det2, frame_idx=2, timestamp_utc=now_utc)

    assert len(tracks_f2) == 1
    assert tracks_f2[0].track_id == track_id  # Successfully recovered without losing identity
    assert tracks_f2[0].state == TrackState.TRACKED


@pytest.mark.asyncio
async def test_tracking_api_endpoints(db_session: AsyncSession):
    """Test REST API routes for multi-object tracking."""
    camera = Camera(
        id="track-cam-uuid-01",
        external_camera_id="GJ-TRK-CAM-01",
        name="Airport Road Tracker",
        location_name="Airport Circle",
        latitude=23.0700,
        longitude=72.6300,
        rtsp_url="rtsp://localhost:8554/live/airport",
        fps=25.0,
        live_status=True,
    )
    db_session.add(camera)
    await db_session.commit()

    # Feed frames to tracker manager
    dets = [
        create_detection(100.0, 100.0, 250.0, 250.0, conf=0.88, frame_idx=1, camera_id=camera.id)
    ]
    res = camera_tracker_manager.track_camera_frame(camera.id, frame_idx=1, detections=dets)
    assert res.active_tracks_count == 1
    track_id = res.tracks[0].track_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /tracking/telemetry
        res_telemetry = await ac.get("/api/v1/tracking/telemetry")
        assert res_telemetry.status_code == 200
        assert res_telemetry.json()["data"]["total_tracks_created"] > 0

        # 2. GET /tracking/{camera_id}/active
        res_active = await ac.get(f"/api/v1/tracking/{camera.id}/active")
        assert res_active.status_code == 200
        active_list = res_active.json()["data"]
        assert len(active_list) == 1
        assert active_list[0]["track_id"] == track_id

        # 3. GET /tracking/{camera_id}/trajectory/{track_id}
        res_traj = await ac.get(f"/api/v1/tracking/{camera.id}/trajectory/{track_id}")
        assert res_traj.status_code == 200
        traj_data = res_traj.json()["data"]
        assert len(traj_data) == 1
        assert "x" in traj_data[0]
        assert "norm_x" in traj_data[0]

        # 4. POST /tracking/{camera_id}/reset
        res_reset = await ac.post(f"/api/v1/tracking/{camera.id}/reset")
        assert res_reset.status_code == 200
        assert res_reset.json()["data"]["cleared"] is True
