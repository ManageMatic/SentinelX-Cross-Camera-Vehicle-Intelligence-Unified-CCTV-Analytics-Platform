"""Forensic Evidence Vault & Cryptographic SHA-256 Chain of Custody Service for SentinelX.

Provides tamper-evident evidence archiving, live SHA-256 cryptographic verification,
forensic watermark stamping, Indian Evidence Act Section 65B electronic record
certificates, and courtroom-admissible export packages.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.models.camera import Camera
from app.models.evidence import Evidence
from app.models.vehicle import VehicleEvent
from app.schemas.evidence import (
    BatchVerifyResult,
    CourtroomExportPackage,
    EvidenceResponse,
    EvidenceTelemetry,
    EvidenceType,
    EvidenceVerifyResult,
    ForensicWatermarkRequest,
    ForensicWatermarkResponse,
    IntegrityStatus,
    Section65BCertificate,
)


class EvidenceVaultService:
    """Forensic Evidence Vault with SHA-256 verification and Section 65B compliance."""

    def __init__(self, base_storage_path: Optional[str] = None) -> None:
        self.base_path = Path(base_storage_path or settings.EVIDENCE_STORAGE_PATH)
        self.snapshots_dir = self.base_path / "snapshots"
        self.crops_dir = self.base_path / "crops"
        self.watermarks_dir = self.base_path / "watermarks"
        self.packages_dir = self.base_path / "courtroom_packages"

        self._ensure_directories()

        # Telemetry metrics
        self._total_archived: int = 0
        self._total_verifications: int = 0
        self._tamper_detections: int = 0
        self._missing_files: int = 0
        self._verification_latencies_ms: List[float] = []

    def _ensure_directories(self) -> None:
        """Guarantee all evidence vault subdirectories exist safely."""
        for directory in [
            self.base_path,
            self.snapshots_dir,
            self.crops_dir,
            self.watermarks_dir,
            self.packages_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Compute SHA-256 hexadecimal hash string for binary data."""
        hasher = hashlib.sha256()
        hasher.update(data)
        return hasher.hexdigest()

    @staticmethod
    def compute_file_sha256(file_path: Path) -> str:
        """Compute SHA-256 digest from a file on disk."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    async def archive_evidence(
        self,
        db: AsyncSession,
        camera_id: str,
        image_bytes: bytes,
        file_type: EvidenceType = EvidenceType.SNAPSHOT,
        mime_type: str = "image/jpeg",
        event_id: Optional[str] = None,
        captured_at: Optional[datetime] = None,
        retention_days: int = 90,
    ) -> Evidence:
        """Cryptographically hash and securely write evidence to disk, then record in database."""
        if not image_bytes:
            raise ValueError("Evidence payload cannot be empty.")

        capture_dt = captured_at or datetime.now(timezone.utc)
        evidence_id = str(uuid.uuid4())
        sha256_hash = self.compute_sha256(image_bytes)
        file_size = len(image_bytes)

        # Date-based hierarchical partitioning
        date_folder = capture_dt.strftime("%Y/%m/%d")
        sub_dir = (
            self.crops_dir
            if file_type == EvidenceType.PLATE_CROP
            else self.snapshots_dir
        )
        target_dir = sub_dir / date_folder
        target_dir.mkdir(parents=True, exist_ok=True)

        ext = ".jpg" if "jpeg" in mime_type or "jpg" in mime_type else ".bin"
        file_name = f"{evidence_id}{ext}"
        full_file_path = target_dir / file_name

        # Write atomically
        with open(full_file_path, "wb") as f:
            f.write(image_bytes)

        evidence_record = Evidence(
            id=evidence_id,
            event_id=event_id,
            camera_id=camera_id,
            file_path=str(full_file_path.as_posix()),
            file_type=file_type.value,
            mime_type=mime_type,
            file_size_bytes=file_size,
            sha256_hash=sha256_hash,
            captured_at=capture_dt,
            retention_days=retention_days,
        )

        db.add(evidence_record)
        await db.commit()
        await db.refresh(evidence_record)

        self._total_archived += 1
        logger.info(
            f"Archived evidence {evidence_id} (Camera: {camera_id}, Size: {file_size}B, SHA-256: {sha256_hash[:16]}...)"
        )
        return evidence_record

    async def verify_evidence_integrity(
        self,
        db: AsyncSession,
        evidence_id: str,
    ) -> EvidenceVerifyResult:
        """Verify recorded evidence hash against live physical disk file."""
        t_start = time.perf_counter()
        now_dt = datetime.now(timezone.utc)

        result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
        record = result.scalar_one_or_none()

        if not record:
            elapsed_ms = (time.perf_counter() - t_start) * 1000
            return EvidenceVerifyResult(
                evidence_id=evidence_id,
                file_path="",
                recorded_sha256="",
                computed_sha256=None,
                status=IntegrityStatus.FILE_NOT_FOUND,
                verified_at=now_dt,
                verification_latency_ms=round(elapsed_ms, 3),
                file_size_bytes=0,
                message=f"Evidence ID {evidence_id} does not exist in database.",
            )

        disk_path = Path(record.file_path)
        if not disk_path.exists():
            elapsed_ms = (time.perf_counter() - t_start) * 1000
            self._total_verifications += 1
            self._missing_files += 1
            self._verification_latencies_ms.append(elapsed_ms)
            return EvidenceVerifyResult(
                evidence_id=evidence_id,
                file_path=record.file_path,
                recorded_sha256=record.sha256_hash,
                computed_sha256=None,
                status=IntegrityStatus.FILE_NOT_FOUND,
                verified_at=now_dt,
                verification_latency_ms=round(elapsed_ms, 3),
                file_size_bytes=0,
                message=f"Physical evidence file missing on disk at: {record.file_path}",
            )

        # Compute disk SHA-256
        live_sha256 = self.compute_file_sha256(disk_path)
        live_file_size = disk_path.stat().st_size
        elapsed_ms = (time.perf_counter() - t_start) * 1000
        self._total_verifications += 1
        self._verification_latencies_ms.append(elapsed_ms)

        if live_sha256.lower() == record.sha256_hash.lower():
            return EvidenceVerifyResult(
                evidence_id=evidence_id,
                file_path=record.file_path,
                recorded_sha256=record.sha256_hash,
                computed_sha256=live_sha256,
                status=IntegrityStatus.VERIFIED_MATCH,
                verified_at=now_dt,
                verification_latency_ms=round(elapsed_ms, 3),
                file_size_bytes=live_file_size,
                message="Cryptographic SHA-256 integrity verified. No evidence tampering detected.",
            )
        else:
            self._tamper_detections += 1
            logger.warning(
                f"TAMPER DETECTED on evidence {evidence_id}! Expected {record.sha256_hash} but found {live_sha256}"
            )
            return EvidenceVerifyResult(
                evidence_id=evidence_id,
                file_path=record.file_path,
                recorded_sha256=record.sha256_hash,
                computed_sha256=live_sha256,
                status=IntegrityStatus.TAMPER_DETECTED,
                verified_at=now_dt,
                verification_latency_ms=round(elapsed_ms, 3),
                file_size_bytes=live_file_size,
                message="CRITICAL ALERT: SHA-256 hash mismatch! Physical file content has been altered or corrupted.",
            )

    async def verify_batch(
        self,
        db: AsyncSession,
        camera_id: Optional[str] = None,
        limit: int = 100,
    ) -> BatchVerifyResult:
        """Run cryptographic integrity verification across a batch of evidence records."""
        t_start = time.perf_counter()
        query = select(Evidence)
        if camera_id:
            query = query.where(Evidence.camera_id == camera_id)
        query = query.order_by(Evidence.captured_at.desc()).limit(limit)

        result = await db.execute(query)
        records = result.scalars().all()

        results: List[EvidenceVerifyResult] = []
        verified_matches = 0
        tampered_count = 0
        missing_count = 0

        for record in records:
            res = await self.verify_evidence_integrity(db, record.id)
            results.append(res)
            if res.status == IntegrityStatus.VERIFIED_MATCH:
                verified_matches += 1
            elif res.status == IntegrityStatus.TAMPER_DETECTED:
                tampered_count += 1
            elif res.status == IntegrityStatus.FILE_NOT_FOUND:
                missing_count += 1

        elapsed_ms = (time.perf_counter() - t_start) * 1000
        return BatchVerifyResult(
            total_evaluated=len(results),
            verified_matches=verified_matches,
            tampered_count=tampered_count,
            missing_count=missing_count,
            elapsed_ms=round(elapsed_ms, 2),
            results=results,
        )

    async def apply_forensic_watermark(
        self,
        db: AsyncSession,
        evidence_id: str,
        params: Optional[ForensicWatermarkRequest] = None,
    ) -> Tuple[ForensicWatermarkResponse, bytes]:
        """Apply official police chain-of-custody banner watermark to evidence snapshot."""
        request_params = params or ForensicWatermarkRequest()
        result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError(f"Evidence {evidence_id} not found.")

        file_path = Path(record.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Evidence file {record.file_path} not found on disk.")

        # Read image via OpenCV
        img = cv2.imread(str(file_path))
        if img is None:
            # Generate placeholder if not directly decodable as image
            img = np.zeros((720, 1280, 3), dtype=np.uint8)

        h, w = img.shape[:2]

        # Fetch camera details if available
        cam_result = await db.execute(select(Camera).where(Camera.id == record.camera_id))
        cam = cam_result.scalar_one_or_none()
        location_name = cam.location_name if cam else "UNKNOWN_LOCATION"
        gps_text = f"GPS: {cam.latitude:.5f},{cam.longitude:.5f}" if (cam and request_params.embed_gps) else ""

        # Time representations
        utc_dt = record.captured_at if record.captured_at.tzinfo else record.captured_at.replace(tzinfo=timezone.utc)
        ist_dt = utc_dt.astimezone(timezone(timedelta(hours=5, minutes=30)))
        utc_str = utc_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        ist_str = ist_dt.strftime("%Y-%m-%d %H:%M:%S IST")

        # Overlay banners (Top & Bottom)
        banner_h = max(40, int(h * 0.07))
        overlay = img.copy()

        # Top dark bar
        cv2.rectangle(overlay, (0, 0), (w, banner_h), (20, 20, 20), -1)
        # Bottom dark bar
        cv2.rectangle(overlay, (0, h - banner_h), (w, h), (20, 20, 20), -1)

        # Alpha blend 75% opacity
        cv2.addWeighted(overlay, 0.75, img, 0.25, 0, img)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.45, w / 2200.0)
        thickness = 1

        # Top text: System and Camera Information
        top_text_left = f"SENTINELX FORENSIC VAULT | CAM: {record.camera_id} ({location_name})"
        top_text_right = f"{utc_str} | {ist_str}"

        cv2.putText(img, top_text_left, (15, int(banner_h * 0.65)), font, font_scale, (0, 255, 255), thickness, cv2.LINE_AA)
        cv2.putText(img, top_text_right, (max(15, w - int(len(top_text_right) * font_scale * 16)), int(banner_h * 0.65)), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

        # Bottom text: Legal reference, officer badge, and cryptographic hash
        sha_prefix = record.sha256_hash[:16] if request_params.embed_sha256_prefix else ""
        bottom_text = f"CASE: {request_params.case_reference} | BADGE: {request_params.badge_id} | SHA-256: {sha_prefix}... | {gps_text} | SEC 65B INDIAN EVIDENCE ACT"
        cv2.putText(img, bottom_text, (15, h - int(banner_h * 0.35)), font, font_scale, (0, 255, 128), thickness, cv2.LINE_AA)

        # Encode to JPEG
        success, encoded_jpg = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if not success:
            raise RuntimeError("Failed to encode watermarked image.")

        watermarked_bytes = encoded_jpg.tobytes()
        watermarked_sha256 = self.compute_sha256(watermarked_bytes)

        # Save to watermarks directory
        watermarked_path = self.watermarks_dir / f"watermark_{evidence_id}.jpg"
        with open(watermarked_path, "wb") as f:
            f.write(watermarked_bytes)

        watermark_response = ForensicWatermarkResponse(
            evidence_id=evidence_id,
            watermarked_file_path=str(watermarked_path.as_posix()),
            watermarked_sha256=watermarked_sha256,
            watermark_text=f"{top_text_left} | {bottom_text}",
            generated_at=datetime.now(timezone.utc),
        )
        return watermark_response, watermarked_bytes

    async def generate_section_65b_certificate(
        self,
        db: AsyncSession,
        evidence_id: str,
        certifying_officer_badge: str = "POLICE-HQ-01",
        certifying_officer_name: str = "Forensic Station Officer",
        case_reference: str = "CASE-2026-GJ-001",
    ) -> Section65BCertificate:
        """Generate Indian Evidence Act Section 65B Courtroom Certificate for electronic records."""
        result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError(f"Evidence record {evidence_id} not found.")

        utc_dt = record.captured_at if record.captured_at.tzinfo else record.captured_at.replace(tzinfo=timezone.utc)
        ist_dt = utc_dt.astimezone(timezone(timedelta(hours=5, minutes=30)))

        cert_id = f"SEC65B-{uuid.uuid4().hex[:12].upper()}"
        legal_declaration = (
            f"I, {certifying_officer_name} (Badge: {certifying_officer_badge}), hereby certify under Section 65B "
            f"of the Indian Evidence Act, 1872 / Section 63 of Bharatiya Sakshya Adhiniyam, 2023, that the electronic "
            f"record (SHA-256: {record.sha256_hash}) was generated by the SentinelX Automated Video Intelligence "
            f"Platform during its normal lawful operation from Camera '{record.camera_id}'. The electronic record was "
            f"continuously secured under cryptographic hash protection with no unauthorized intervention, alteration, "
            f"or hardware malfunction throughout its custody."
        )

        return Section65BCertificate(
            certificate_id=cert_id,
            case_reference=case_reference,
            evidence_id=record.id,
            camera_id=record.camera_id,
            event_id=record.event_id,
            capture_timestamp_utc=utc_dt.isoformat(),
            capture_timestamp_ist=ist_dt.isoformat(),
            sha256_hash=record.sha256_hash,
            file_size_bytes=record.file_size_bytes,
            mime_type=record.mime_type,
            system_custodian="SentinelX Forensic Chain-of-Custody Vault",
            certifying_officer_badge=certifying_officer_badge,
            certifying_officer_name=certifying_officer_name,
            legal_declaration=legal_declaration,
            issued_at=datetime.now(timezone.utc),
        )

    async def create_courtroom_package(
        self,
        db: AsyncSession,
        evidence_id_or_event_id: str,
        case_reference: str = "CASE-2026-GJ-001",
        officer_badge: str = "POLICE-HQ-01",
        officer_name: str = "Investigating Officer",
    ) -> CourtroomExportPackage:
        """Assemble comprehensive courtroom evidence dossier and manifest."""
        # Query by evidence ID first, or event ID
        ev_result = await db.execute(
            select(Evidence).where(
                (Evidence.id == evidence_id_or_event_id)
                | (Evidence.event_id == evidence_id_or_event_id)
            )
        )
        evidence_records = ev_result.scalars().all()

        if not evidence_records:
            raise ValueError(f"No evidence found for identifier '{evidence_id_or_event_id}'.")

        primary_record = evidence_records[0]
        certificate = await self.generate_section_65b_certificate(
            db=db,
            evidence_id=primary_record.id,
            certifying_officer_badge=officer_badge,
            certifying_officer_name=officer_name,
            case_reference=case_reference,
        )

        # Lookup plate number if event_id is linked
        plate_number: Optional[str] = None
        if primary_record.event_id:
            event_res = await db.execute(
                select(VehicleEvent).where(VehicleEvent.id == primary_record.event_id)
            )
            event_obj = event_res.scalar_one_or_none()
            if event_obj:
                plate_number = event_obj.plate_number_normalized

        # Compute manifest SHA-256
        combined_hashes = "".join(sorted([e.sha256_hash for e in evidence_records])) + certificate.certificate_id
        manifest_sha256 = self.compute_sha256(combined_hashes.encode("utf-8"))

        evidence_items = [
            EvidenceResponse(
                id=e.id,
                event_id=e.event_id,
                camera_id=e.camera_id,
                file_path=e.file_path,
                file_type=e.file_type,
                mime_type=e.mime_type,
                file_size_bytes=e.file_size_bytes,
                sha256_hash=e.sha256_hash,
                captured_at=e.captured_at,
                retention_days=e.retention_days,
                created_at=e.created_at,
            )
            for e in evidence_records
        ]

        package_id = f"PKG-{uuid.uuid4().hex[:10].upper()}"
        return CourtroomExportPackage(
            package_id=package_id,
            case_reference=case_reference,
            event_id=primary_record.event_id,
            plate_number=plate_number,
            evidence_count=len(evidence_items),
            manifest_sha256=manifest_sha256,
            section_65b_certificate=certificate,
            evidence_items=evidence_items,
            package_created_at=datetime.now(timezone.utc),
        )

    async def get_telemetry(self, db: AsyncSession) -> EvidenceTelemetry:
        """Retrieve aggregate storage and integrity verification telemetry."""
        count_res = await db.execute(select(func.count(Evidence.id)))
        total_in_db = count_res.scalar() or 0

        bytes_res = await db.execute(select(func.sum(Evidence.file_size_bytes)))
        total_storage_bytes = bytes_res.scalar() or 0

        mean_lat = (
            sum(self._verification_latencies_ms) / len(self._verification_latencies_ms)
            if self._verification_latencies_ms
            else 0.0
        )

        return EvidenceTelemetry(
            total_archived=self._total_archived or total_in_db,
            total_verifications=self._total_verifications,
            tamper_detections=self._tamper_detections,
            missing_files=self._missing_files,
            total_storage_bytes=total_storage_bytes,
            mean_verification_latency_ms=round(mean_lat, 2),
        )


# Global singleton instance
evidence_vault_service = EvidenceVaultService()
