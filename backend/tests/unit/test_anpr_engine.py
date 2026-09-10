"""Comprehensive Unit Tests for ANPR Engine & Indian License Plate Normalizer (Module 12)."""

import io

import cv2
import numpy as np
import pytest
from app.main import app
from app.schemas.anpr import PlateCategory
from app.services.anpr_engine import ANPREngine
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_standard_indian_plate_normalization():
    """Verify parsing and normalization of standard Indian vehicle registration plates."""
    engine = ANPREngine()

    # Gujarat Plate with spaces and lowercase
    res1 = engine.normalize_plate("gj 01 ab 1234", confidence=0.92)
    assert res1.plate_normalized == "GJ01AB1234"
    assert res1.state_code == "GJ"
    assert res1.district_code == "01"
    assert res1.series == "AB"
    assert res1.number == "1234"
    assert res1.is_valid_syntax is True
    assert res1.category == PlateCategory.STANDARD

    # Maharashtra Plate with 1-digit RTO (MH 4 AB 5678 -> MH04AB5678)
    res2 = engine.normalize_plate("MH 4 CD 5678", confidence=0.88)
    assert res2.plate_normalized == "MH04CD5678"
    assert res2.state_code == "MH"
    assert res2.district_code == "04"
    assert res2.is_valid_syntax is True

    # Delhi 3-letter series (DL 3C AB 9999)
    res3 = engine.normalize_plate("DL 3C AB 9999", confidence=0.95)
    assert res3.plate_normalized == "DL03CAB9999"
    assert res3.state_code == "DL"
    assert res3.is_valid_syntax is True


@pytest.mark.asyncio
async def test_bharat_series_plate_normalization():
    """Verify Bharat (BH) series registration plates."""
    engine = ANPREngine()
    res = engine.normalize_plate("22 BH 1234 AA", confidence=0.91)
    assert res.plate_normalized == "22BH1234AA"
    assert res.category == PlateCategory.BHARAT_SERIES
    assert res.district_code == "22"
    assert res.number == "1234"
    assert res.series == "AA"
    assert res.is_valid_syntax is True


@pytest.mark.asyncio
async def test_character_disambiguation_correction():
    """Verify position-aware correction of common OCR confusion pairs (O/0, I/1, S/5, B/8)."""
    engine = ANPREngine()

    # Raw OCR misread '0' as 'O' in district code and '1' as 'I' in number: "GJ O1 AB I234"
    res = engine.normalize_plate("GJ O1 AB I234", confidence=0.85)
    assert res.plate_normalized == "GJ01AB1234"
    assert res.is_valid_syntax is True

    # Raw OCR misread '5' as 'S' and '8' as 'B' in number: "MH 12 CD S67B"
    res2 = engine.normalize_plate("MH 12 CD S67B", confidence=0.89)
    assert res2.plate_normalized == "MH12CD5678"
    assert res2.is_valid_syntax is True


@pytest.mark.asyncio
async def test_anpr_clahe_preprocessing():
    """Verify CLAHE enhancement and bilateral denoising filters."""
    crop = np.zeros((50, 150, 3), dtype=np.uint8)
    cv2.putText(crop, "GJ01AB1234", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    enhanced = ANPREngine.preprocess_image(crop, enable_clahe=True)
    assert enhanced.ndim == 2  # Grayscale
    assert enhanced.shape[0] >= 70  # Upscaled to >= 70px


@pytest.mark.asyncio
async def test_anpr_crop_recognition_telemetry():
    """Verify full crop recognition pipeline and telemetry stats."""
    engine = ANPREngine()
    crop = np.zeros((80, 200, 3), dtype=np.uint8)
    cv2.putText(crop, "GJ01AB1234", (15, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    res = engine.recognize_crop(crop, camera_id="test-cam-anpr-01", frame_idx=5)
    assert res.is_valid_syntax is True
    assert res.processing_time_ms >= 0.0

    telemetry = engine.get_telemetry()
    assert telemetry.total_plates_processed == 1
    assert telemetry.valid_syntax_count == 1
    assert telemetry.syntax_validity_rate_pct == 100.0


@pytest.mark.asyncio
async def test_anpr_api_endpoints():
    """Verify REST API routes for ANPR (/telemetry, /states, /normalize-text, /recognize-crop, /configure)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /anpr/telemetry
        res_telemetry = await ac.get("/api/v1/anpr/telemetry")
        assert res_telemetry.status_code == 200
        assert "engine_name" in res_telemetry.json()["data"]

        # 2. GET /anpr/states
        res_states = await ac.get("/api/v1/anpr/states")
        assert res_states.status_code == 200
        data_states = res_states.json()["data"]
        assert "GJ" in data_states["states"]
        assert "MH" in data_states["states"]
        assert data_states["total_states"] >= 30

        # 3. POST /anpr/normalize-text
        res_norm = await ac.post(
            "/api/v1/anpr/normalize-text",
            json={"raw_text": "gj 01 ab 1234", "confidence": 0.95},
        )
        assert res_norm.status_code == 200
        norm_data = res_norm.json()["data"]
        assert norm_data["plate_normalized"] == "GJ01AB1234"
        assert norm_data["is_valid_syntax"] is True

        # 4. POST /anpr/configure
        res_cfg = await ac.post(
            "/api/v1/anpr/configure",
            json={"confidence_threshold": 0.55, "enable_clahe_enhancement": True},
        )
        assert res_cfg.status_code == 200

        # 5. POST /anpr/recognize-crop (Multipart upload)
        crop = np.zeros((80, 200, 3), dtype=np.uint8)
        cv2.putText(crop, "GJ01AB1234", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        _, crop_encoded = cv2.imencode(".jpg", crop)
        file_bytes = io.BytesIO(crop_encoded.tobytes())

        res_crop = await ac.post(
            "/api/v1/anpr/recognize-crop",
            files={"file": ("plate_crop.jpg", file_bytes, "image/jpeg")},
        )
        assert res_crop.status_code == 200
        crop_data = res_crop.json()["data"]
        assert "plate_normalized" in crop_data
        assert crop_data["confidence"] > 0.0
