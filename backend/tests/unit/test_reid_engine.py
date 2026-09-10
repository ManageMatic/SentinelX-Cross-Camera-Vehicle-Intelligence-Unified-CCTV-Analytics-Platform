"""Unit tests for Vehicle Appearance Re-ID & Visual Embedding Generator (Module 13)."""

import numpy as np
import pytest
from app.schemas.reid import BodyStyle, ReIDConfig, VehicleColor
from app.services.reid_engine import ReIDEngine


@pytest.fixture
def reid_engine_inst():
    return ReIDEngine()


def test_reid_color_classification(reid_engine_inst):
    # Create pure red crop (BGR: 0, 0, 255)
    red_crop = np.zeros((100, 100, 3), dtype=np.uint8)
    red_crop[:, :] = [0, 0, 255]
    dom_color, conf, sec = reid_engine_inst.classify_dominant_color(red_crop)
    assert dom_color == VehicleColor.RED
    assert conf > 0.5

    # Create pure blue crop (BGR: 255, 0, 0)
    blue_crop = np.zeros((100, 100, 3), dtype=np.uint8)
    blue_crop[:, :] = [255, 0, 0]
    dom_color, conf, sec = reid_engine_inst.classify_dominant_color(blue_crop)
    assert dom_color == VehicleColor.BLUE
    assert conf > 0.5

    # Create pure white crop (BGR: 255, 255, 255)
    white_crop = np.full((100, 100, 3), 255, dtype=np.uint8)
    dom_color, conf, sec = reid_engine_inst.classify_dominant_color(white_crop)
    assert dom_color == VehicleColor.WHITE
    assert conf > 0.5


def test_reid_body_style_estimation(reid_engine_inst):
    # Wide crop (aspect ratio > 1.75) -> Sedan
    sedan_crop = np.zeros((100, 190, 3), dtype=np.uint8)
    style, conf = reid_engine_inst.classify_body_style(sedan_crop)
    assert style == BodyStyle.SEDAN
    assert conf >= 0.80

    # Tall vertical crop (aspect ratio < 0.65) -> Motorcycle
    bike_crop = np.zeros((200, 100, 3), dtype=np.uint8)
    style, conf = reid_engine_inst.classify_body_style(bike_crop)
    assert style == BodyStyle.MOTORCYCLE
    assert conf >= 0.85


def test_crop_quality_scoring(reid_engine_inst):
    # Blank zero image
    blank = np.zeros((50, 50, 3), dtype=np.uint8)
    q_blank = reid_engine_inst.compute_crop_quality(blank)
    assert 0.0 <= q_blank <= 0.5

    # Rich textured image (Gaussian noise)
    textured = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
    q_text = reid_engine_inst.compute_crop_quality(textured)
    assert q_text > q_blank
    assert 0.0 <= q_text <= 1.0


def test_embedding_l2_normalization_and_similarity(reid_engine_inst):
    crop = np.random.randint(0, 256, (120, 120, 3), dtype=np.uint8)
    res = reid_engine_inst.extract_embedding(crop)

    assert len(res.embedding) == 512
    assert res.embedding_dim == 512

    # Verify L2 norm is 1.0
    vec = np.array(res.embedding, dtype=np.float32)
    norm = np.linalg.norm(vec)
    assert np.isclose(norm, 1.0, atol=1e-2)

    # Self-comparison similarity should be 1.0
    sim_self = reid_engine_inst.compare_embeddings(res.embedding, res.embedding)
    assert np.isclose(sim_self.cosine_similarity, 1.0, atol=1e-3)
    assert sim_self.is_match is True
    assert sim_self.match_status == "HIGH_MATCH"

    # Orthogonal comparison
    vec_b = [-x for x in res.embedding]
    sim_opp = reid_engine_inst.compare_embeddings(res.embedding, vec_b)
    assert sim_opp.is_match is False
    assert sim_opp.match_status == "NO_MATCH"


def test_reid_telemetry(reid_engine_inst):
    crop = np.zeros((80, 80, 3), dtype=np.uint8)
    reid_engine_inst.extract_embedding(crop)

    telem = reid_engine_inst.get_telemetry()
    assert telem.total_embeddings_extracted >= 1
    assert "white" in telem.color_distribution or "black" in telem.color_distribution
    assert telem.last_extraction_at is not None


def test_reid_configuration_update(reid_engine_inst):
    cfg = ReIDConfig(similarity_threshold=0.88, use_synthetic_reid=True)
    reid_engine_inst.configure(cfg)
    assert reid_engine_inst.config.similarity_threshold == 0.88
    assert reid_engine_inst.is_mock is True
