"""Forensic Evidence Vault, SHA-256 Chain of Custody, and Courtroom Export Schemas for SentinelX."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Types of evidence files archived in the vault."""
    SNAPSHOT = "SNAPSHOT"
    PLATE_CROP = "PLATE_CROP"
    VIDEO_CLIP = "VIDEO_CLIP"
    WATERMARKED_SNAPSHOT = "WATERMARKED_SNAPSHOT"
    COURTROOM_ARCHIVE = "COURTROOM_ARCHIVE"


class IntegrityStatus(str, Enum):
    """Cryptographic SHA-256 verification results."""
    VERIFIED_MATCH = "VERIFIED_MATCH"
    TAMPER_DETECTED = "TAMPER_DETECTED"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"


class EvidenceArchiveRequest(BaseModel):
    """Request to securely ingest and archive evidence."""
    camera_id: str = Field(..., description="Camera UUID or identifier where frame was captured")
    event_id: Optional[str] = Field(None, description="Associated vehicle event UUID if known")
    file_type: EvidenceType = Field(default=EvidenceType.SNAPSHOT, description="Type of evidence artifact")
    mime_type: str = Field(default="image/jpeg", description="MIME content type")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image or binary payload")
    captured_at: Optional[datetime] = Field(None, description="Capture timestamp (defaults to current UTC)")
    retention_days: int = Field(default=90, ge=1, le=3650, description="Retention policy in days")


class EvidenceResponse(BaseModel):
    """Forensic evidence record with cryptographic SHA-256 hash."""
    id: str = Field(..., description="Unique Evidence UUID")
    event_id: Optional[str] = Field(None, description="Linked Vehicle Event ID")
    camera_id: str = Field(..., description="Camera ID")
    file_path: str = Field(..., description="Secure storage path on disk")
    file_type: str = Field(..., description="Evidence type (SNAPSHOT, PLATE_CROP, etc.)")
    mime_type: str = Field(..., description="MIME type")
    file_size_bytes: int = Field(..., description="Physical file size in bytes")
    sha256_hash: str = Field(..., description="Cryptographic SHA-256 digest")
    captured_at: datetime = Field(..., description="Timestamp of frame capture")
    retention_days: int = Field(..., description="Days until automated retention pruning")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")


class EvidenceListResponse(BaseModel):
    """Paginated collection of archived evidence."""
    total: int
    items: List[EvidenceResponse]


class EvidenceVerifyResult(BaseModel):
    """Detailed cryptographic integrity check result."""
    evidence_id: str
    file_path: str
    recorded_sha256: str
    computed_sha256: Optional[str] = None
    status: IntegrityStatus
    verified_at: datetime
    verification_latency_ms: float
    file_size_bytes: int
    message: str


class BatchVerifyResult(BaseModel):
    """Batch forensic integrity audit summary."""
    total_evaluated: int
    verified_matches: int
    tampered_count: int
    missing_count: int
    elapsed_ms: float
    results: List[EvidenceVerifyResult]


class ForensicWatermarkRequest(BaseModel):
    """Parameters to generate a watermarked inspection copy."""
    badge_id: Optional[str] = Field(default="POLICE-HQ-01", description="Investigating officer badge")
    case_reference: Optional[str] = Field(default="CASE-2026-GJ-001", description="Police Case / FIR Number")
    officer_name: Optional[str] = Field(default="Duty Officer", description="Name of certifying officer")
    embed_gps: bool = Field(default=True, description="Whether to stamp camera GPS coordinates")
    embed_sha256_prefix: bool = Field(default=True, description="Whether to stamp SHA-256 digest prefix")


class ForensicWatermarkResponse(BaseModel):
    """Watermarked evidence metadata."""
    evidence_id: str
    watermarked_file_path: str
    watermarked_sha256: str
    watermark_text: str
    generated_at: datetime


class Section65BCertificate(BaseModel):
    """Courtroom-admissible electronic record certificate under Section 65B of Indian Evidence Act."""
    certificate_id: str
    case_reference: str
    evidence_id: str
    camera_id: str
    event_id: Optional[str]
    capture_timestamp_utc: str
    capture_timestamp_ist: str
    sha256_hash: str
    file_size_bytes: int
    mime_type: str
    system_custodian: str
    certifying_officer_badge: str
    certifying_officer_name: str
    legal_declaration: str
    issued_at: datetime


class CourtroomExportPackage(BaseModel):
    """Complete forensic dossier package for legal proceedings."""
    package_id: str
    case_reference: str
    event_id: Optional[str]
    plate_number: Optional[str]
    evidence_count: int
    manifest_sha256: str
    section_65b_certificate: Section65BCertificate
    evidence_items: List[EvidenceResponse]
    package_created_at: datetime


class EvidenceTelemetry(BaseModel):
    """Evidence vault performance and integrity telemetry."""
    total_archived: int
    total_verifications: int
    tamper_detections: int
    missing_files: int
    total_storage_bytes: int
    mean_verification_latency_ms: float
