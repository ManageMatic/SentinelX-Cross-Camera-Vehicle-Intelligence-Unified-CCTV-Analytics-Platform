"""Comprehensive Unit Tests for Multi-Class Vehicle Detection Engine (Module 10)."""

import io
from datetime import datetime, timezone

import cv2
import numpy as np
import pytest
from app.main import app
from app.schemas.detection import (
    BoundingBox,
    DetectorConfig,
    VehicleClass,
)
from app.schemas.stream import VideoFrame
from app.services.vehicle_detector import VehicleDetector
from httpx import ASGITransport, AsyncClient


def create_test_frame(w: int = 1280, h: int = 720, frame_idx: int = 1) -> VideoFrame:
    """Helper creating synthetic video frame image."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.rectangle(img, (200, 300), (500, 600), (0, 255, 0), -1)
    cv2.rectangle(img, (700, 350), (900, 550), (255, 0, 0), -1)
    return VideoFrame(
        camera_id="cam-det-test-01",
        frame_index=frame_idx,
        timestamp_utc=datetime.now(timezone.utc),
        image=img,
        width=w,
        height=h,
        fps=25.0,
    )


@pytest.mark.asyncio
async def test_letterbox_preprocessing():
    """Verify letterbox maintains aspect ratio and calculates correct scales and offsets."""
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    padded, r, (dw, dh) = VehicleDetector.letterbox(img, target_shape=(640, 640))

    assert padded.shape == (640, 640, 3)
    assert r == 640 / 1280  # 0.5
    assert dw == 0.0  # Width fits exactly
    assert dh == (640 - (720 * 0.5)) / 2  # 140.0 padding top/bottom


@pytest.mark.asyncio
async def test_nms_suppression():
    """Verify Non-Maximum Suppression suppresses overlapping bounding boxes."""
    # Box 1: high score, Box 2: identical overlapping with lower score, Box 3: separate box
    boxes = [
        (100.0, 100.0, 200.0, 200.0),
        (105.0, 102.0, 202.0, 198.0),  # Heavy overlap with box 1
        (400.0, 400.0, 500.0, 500.0),  # Distinct
    ]
    scores = [0.95, 0.75, 0.88]

    keep = VehicleDetector.nms_boxes(boxes, scores, iou_threshold=0.45)
    assert 0 in keep  # Box 0 kept (highest confidence)
    assert 1 not in keep  # Box 1 suppressed by NMS
    assert 2 in keep  # Box 2 kept (distinct area)


@pytest.mark.asyncio
async def test_extract_vehicle_crop():
    """Verify safe crop extraction clamps bounds correctly."""
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.circle(img, (300, 300), 50, (255, 255, 255), -1)

    bbox = BoundingBox(
        x1=250.0,
        y1=250.0,
        x2=350.0,
        y2=350.0,
        norm_x1=250 / 1280,
        norm_y1=250 / 720,
        norm_x2=350 / 1280,
        norm_y2=350 / 720,
        width=100.0,
        height=100.0,
    )

    crop = VehicleDetector.extract_vehicle_crop(img, bbox)
    assert crop is not None
    assert crop.shape[0] == 100
    assert crop.shape[1] == 100


@pytest.mark.asyncio
async def test_vehicle_detection_inference():
    """Verify detection pipeline generates normalized bounding boxes and telemetry."""
    detector = VehicleDetector(
        DetectorConfig(use_synthetic_detector=True, confidence_threshold=0.5)
    )
    frame = create_test_frame()

    result = detector.detect(frame)
    assert result.total_vehicles > 0
    assert result.inference_time_ms >= 0.0
    assert result.camera_id == frame.camera_id

    for v in result.vehicles:
        assert v.confidence >= 0.5
        assert v.vehicle_class in [
            VehicleClass.CAR,
            VehicleClass.MOTORCYCLE,
            VehicleClass.BUS,
            VehicleClass.TRUCK,
            VehicleClass.AUTO_RICKSHAW,
            VehicleClass.VAN,
        ]
        assert 0.0 <= v.bbox.norm_x1 <= 1.0
        assert 0.0 <= v.bbox.norm_y1 <= 1.0
        assert 0.0 <= v.bbox.norm_x2 <= 1.0
        assert 0.0 <= v.bbox.norm_y2 <= 1.0

    telemetry = detector.get_telemetry()
    assert telemetry.total_frames_processed == 1
    assert telemetry.total_vehicles_detected == result.total_vehicles


@pytest.mark.asyncio
async def test_detection_api_routes():
    """Verify REST API routes for vehicle detection engine."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /detection/telemetry
        res_telemetry = await ac.get("/api/v1/detection/telemetry")
        assert res_telemetry.status_code == 200
        assert "execution_provider" in res_telemetry.json()["data"]

        # 2. GET /detection/classes
        res_classes = await ac.get("/api/v1/detection/classes")
        assert res_classes.status_code == 200
        data_classes = res_classes.json()["data"]
        assert "car" in data_classes["classes"]
        assert "auto_rickshaw" in data_classes["classes"]

        # 3. POST /detection/configure
        config_payload = {
            "confidence_threshold": 0.40,
            "nms_iou_threshold": 0.50,
            "use_synthetic_detector": True,
            "input_width": 640,
            "input_height": 640,
            "enabled_classes": ["car", "bus", "truck", "motorcycle", "auto_rickshaw"],
        }
        res_cfg = await ac.post("/api/v1/detection/configure", json=config_payload)
        assert res_cfg.status_code == 200
        assert res_cfg.json()["data"]["is_mock"] is True

        # 4. POST /detection/detect-frame (Multipart image upload)
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(
            img, "SentinelX Test", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2
        )
        _, img_encoded = cv2.imencode(".jpg", img)
        file_bytes = io.BytesIO(img_encoded.tobytes())

        res_upload = await ac.post(
            "/api/v1/detection/detect-frame",
            files={"file": ("test_frame.jpg", file_bytes, "image/jpeg")},
        )
        assert res_upload.status_code == 200
        upload_data = res_upload.json()["data"]
        assert upload_data["total_vehicles"] > 0
        assert len(upload_data["vehicles"]) == upload_data["total_vehicles"]
