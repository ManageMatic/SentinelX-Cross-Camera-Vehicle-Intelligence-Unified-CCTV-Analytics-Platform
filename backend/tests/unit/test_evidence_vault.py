"""Comprehensive Unit Tests for Forensic Evidence Vault & Cryptographic Chain of Custody (Module 20)."""

import hashlib
import os
from pathlib import Path

import cv2
import numpy as np
import pytest
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.camera import Camera
from app.schemas.evidence import (
    EvidenceType,
    ForensicWatermarkRequest,
    IntegrityStatus,
)
from app.services.evidence_vault import evidence_vault_service
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def synthetic_jpeg() -> bytes:
    """Generate a valid test synthetic JPEG image byte string."""
    img = np.zeros((240, 320, 3), dtype=np.uint8)
    img[:, :] = (120, 150, 200)
    cv2.putText(img, "TEST-EVIDENCE", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    _, encoded = cv2.imencode(".jpg", img)
    return encoded.tobytes()


@pytest.mark.asyncio
async def test_archive_evidence_and_sha256(synthetic_jpeg):
    """Test cryptographic SHA-256 calculation and atomic disk archiving."""
    import uuid
    uid = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as session:
        # Create test camera
        cam = Camera(
            id=f"CAM-VAULT-{uid}",
            external_camera_id=f"EXT-VAULT-{uid}",
            name="Forensic Vault Test Cam",
            location_name="Junction Alpha",
            latitude=23.0225,
            longitude=72.5714,
            rtsp_url=f"rtsp://localhost:8554/{uid}",
            live_status=True,
        )
        session.add(cam)
        await session.commit()

        expected_hash = hashlib.sha256(synthetic_jpeg).hexdigest()

        evidence_rec = await evidence_vault_service.archive_evidence(
            db=session,
            camera_id=f"CAM-VAULT-{uid}",
            image_bytes=synthetic_jpeg,
            file_type=EvidenceType.SNAPSHOT,
        )

        assert evidence_rec.id is not None
        assert evidence_rec.sha256_hash == expected_hash
        assert evidence_rec.file_size_bytes == len(synthetic_jpeg)
        assert Path(evidence_rec.file_path).exists()


@pytest.mark.asyncio
async def test_verify_evidence_integrity_match_and_tamper(synthetic_jpeg):
    """Test verification matching and tamper detection when file content is altered."""
    import uuid
    uid = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as session:
        cam = Camera(
            id=f"CAM-VAULT-{uid}",
            external_camera_id=f"EXT-VAULT-{uid}",
            name="Forensic Cam 2",
            location_name="Highway Beta",
            latitude=23.03,
            longitude=72.58,
            rtsp_url=f"rtsp://localhost:8554/{uid}",
            live_status=True,
        )
        session.add(cam)
        await session.commit()

        evidence_rec = await evidence_vault_service.archive_evidence(
            db=session,
            camera_id=f"CAM-VAULT-{uid}",
            image_bytes=synthetic_jpeg,
            file_type=EvidenceType.SNAPSHOT,
        )

        # 1. Verification Match
        result = await evidence_vault_service.verify_evidence_integrity(session, evidence_rec.id)
        assert result.status == IntegrityStatus.VERIFIED_MATCH
        assert result.computed_sha256 == evidence_rec.sha256_hash

        # 2. Tamper file content directly on disk
        with open(evidence_rec.file_path, "ab") as f:
            f.write(b"TAMPER_PAYLOAD_CORRUPT")

        # 3. Verification should immediately detect tamper
        tamper_res = await evidence_vault_service.verify_evidence_integrity(session, evidence_rec.id)
        assert tamper_res.status == IntegrityStatus.TAMPER_DETECTED
        assert tamper_res.computed_sha256 != evidence_rec.sha256_hash
        assert "CRITICAL ALERT" in tamper_res.message


@pytest.mark.asyncio
async def test_missing_file_integrity():
    """Test missing file verification handling."""
    import uuid
    uid = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as session:
        cam = Camera(
            id=f"CAM-VAULT-{uid}",
            external_camera_id=f"EXT-VAULT-{uid}",
            name="Forensic Cam 3",
            location_name="Missing Cam Point",
            latitude=23.04,
            longitude=72.59,
            rtsp_url=f"rtsp://localhost:8554/{uid}",
            live_status=True,
        )
        session.add(cam)
        await session.commit()

        evidence_rec = await evidence_vault_service.archive_evidence(
            db=session,
            camera_id=f"CAM-VAULT-{uid}",
            image_bytes=b"sample-bytes-to-delete",
            file_type=EvidenceType.PLATE_CROP,
        )

        # Remove file from disk
        if os.path.exists(evidence_rec.file_path):
            os.remove(evidence_rec.file_path)

        res = await evidence_vault_service.verify_evidence_integrity(session, evidence_rec.id)
        assert res.status == IntegrityStatus.FILE_NOT_FOUND


@pytest.mark.asyncio
async def test_forensic_watermarking_and_section_65b(synthetic_jpeg):
    """Test stamping legal metadata banner and generating Section 65B legal certificate."""
    import uuid
    uid = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as session:
        cam = Camera(
            id=f"CAM-VAULT-{uid}",
            external_camera_id=f"EXT-VAULT-{uid}",
            name="Forensic Cam 4",
            location_name="SG Highway Junction",
            latitude=23.05,
            longitude=72.60,
            rtsp_url=f"rtsp://localhost:8554/{uid}",
            live_status=True,
        )
        session.add(cam)
        await session.commit()


        evidence_rec = await evidence_vault_service.archive_evidence(
            db=session,
            camera_id=f"CAM-VAULT-{uid}",
            image_bytes=synthetic_jpeg,
            file_type=EvidenceType.SNAPSHOT,
        )


        # Watermark
        req = ForensicWatermarkRequest(
            badge_id="GJ-INSP-404",
            case_reference="FIR-2026-AHM-089",
            officer_name="Inspector R. Patel",
        )
        wm_res, wm_bytes = await evidence_vault_service.apply_forensic_watermark(
            db=session,
            evidence_id=evidence_rec.id,
            params=req,
        )

        assert wm_res.evidence_id == evidence_rec.id
        assert Path(wm_res.watermarked_file_path).exists()
        assert len(wm_bytes) > 0
        assert "FIR-2026-AHM-089" in wm_res.watermark_text

        # Section 65B Certificate
        cert = await evidence_vault_service.generate_section_65b_certificate(
            db=session,
            evidence_id=evidence_rec.id,
            certifying_officer_badge="GJ-INSP-404",
            certifying_officer_name="Inspector R. Patel",
            case_reference="FIR-2026-AHM-089",
        )

        assert cert.certificate_id.startswith("SEC65B-")
        assert cert.sha256_hash == evidence_rec.sha256_hash
        assert "Section 65B of the Indian Evidence Act" in cert.legal_declaration

        # Courtroom dossier package
        pkg = await evidence_vault_service.create_courtroom_package(
            db=session,
            evidence_id_or_event_id=evidence_rec.id,
            case_reference="FIR-2026-AHM-089",
            officer_badge="GJ-INSP-404",
            officer_name="Inspector R. Patel",
        )

        assert pkg.package_id.startswith("PKG-")
        assert pkg.evidence_count == 1
        assert len(pkg.manifest_sha256) == 64


@pytest.mark.asyncio
async def test_evidence_rest_api(synthetic_jpeg):
    """Test full REST API integration for Evidence Vault endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Archive Evidence via API
        import base64
        b64_img = base64.b64encode(synthetic_jpeg).decode("utf-8")
        archive_resp = await client.post(
            "/api/v1/evidence/archive",
            json={
                "camera_id": "CAM-REST-01",
                "file_type": "SNAPSHOT",
                "image_base64": b64_img,
            },
        )
        assert archive_resp.status_code == 201
        ev_data = archive_resp.json()["data"]
        ev_id = ev_data["id"]
        assert ev_data["sha256_hash"] is not None

        # 2. Get Evidence Details
        detail_resp = await client.get(f"/api/v1/evidence/{ev_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["data"]["id"] == ev_id

        # 3. List Evidence
        list_resp = await client.get("/api/v1/evidence?camera_id=CAM-REST-01")
        assert list_resp.status_code == 200
        assert list_resp.json()["data"]["total"] >= 1

        # 4. Verify Integrity via API
        verify_resp = await client.post(f"/api/v1/evidence/{ev_id}/verify")
        assert verify_resp.status_code == 200
        assert verify_resp.json()["data"]["status"] == "VERIFIED_MATCH"

        # 5. Batch Verify
        batch_resp = await client.post("/api/v1/evidence/verify-batch?camera_id=CAM-REST-01")
        assert batch_resp.status_code == 200
        assert batch_resp.json()["data"]["verified_matches"] >= 1

        # 6. Generate Watermark
        wm_resp = await client.post(
            f"/api/v1/evidence/{ev_id}/watermark",
            json={"case_reference": "FIR-TEST-001", "badge_id": "OFFICER-99"},
        )
        assert wm_resp.status_code == 200
        assert "watermarked_sha256" in wm_resp.json()["data"]

        # 7. Download Watermarked Snapshot
        dl_resp = await client.get(f"/api/v1/evidence/{ev_id}/download?watermark=true")
        assert dl_resp.status_code == 200
        assert dl_resp.headers.get("x-evidence-watermarked") == "true"

        # 8. Section 65B Certificate
        cert_resp = await client.post(f"/api/v1/evidence/{ev_id}/section-65b?case_ref=FIR-TEST-001")
        assert cert_resp.status_code == 200
        assert "SEC65B-" in cert_resp.json()["data"]["certificate_id"]

        # 9. Courtroom Package
        pkg_resp = await client.post(f"/api/v1/evidence/courtroom-package?target_id={ev_id}&case_reference=FIR-TEST-001")
        assert pkg_resp.status_code == 200
        assert pkg_resp.json()["data"]["evidence_count"] >= 1

        # 10. Telemetry
        telem_resp = await client.get("/api/v1/evidence/telemetry")
        assert telem_resp.status_code == 200
        assert telem_resp.json()["data"]["total_archived"] >= 1
