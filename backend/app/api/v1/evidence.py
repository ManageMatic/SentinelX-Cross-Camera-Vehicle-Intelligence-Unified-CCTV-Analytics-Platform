"""Evidence Vault & Forensic Cryptographic Chain-of-Custody REST API Endpoints for SentinelX."""

import base64
from typing import Optional

from app.db.session import get_db
from app.models.evidence import Evidence
from app.schemas.common import APIResponse
from app.schemas.evidence import (
    BatchVerifyResult,
    CourtroomExportPackage,
    EvidenceArchiveRequest,
    EvidenceListResponse,
    EvidenceResponse,
    EvidenceTelemetry,
    EvidenceVerifyResult,
    ForensicWatermarkRequest,
    ForensicWatermarkResponse,
    Section65BCertificate,
)
from app.services.evidence_vault import evidence_vault_service
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/evidence", tags=["Forensic Evidence Vault"])


@router.post(
    "/archive",
    response_model=APIResponse[EvidenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Cryptographically archive snapshot or plate crop evidence",
)
async def archive_evidence(
    payload: EvidenceArchiveRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[EvidenceResponse]:
    """Securely hash and store evidence file with SHA-256 integrity digest."""
    try:
        if payload.image_base64:
            # Handle base64 payload
            b64_str = payload.image_base64
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            image_bytes = base64.b64decode(b64_str)
        else:
            # Generate deterministic synthetic JPEG pattern if no raw image provided
            import cv2
            import numpy as np
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                blank,
                f"CAM: {payload.camera_id}",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
            )
            _, encoded = cv2.imencode(".jpg", blank)
            image_bytes = encoded.tobytes()

        record = await evidence_vault_service.archive_evidence(
            db=db,
            camera_id=payload.camera_id,
            image_bytes=image_bytes,
            file_type=payload.file_type,
            mime_type=payload.mime_type,
            event_id=payload.event_id,
            captured_at=payload.captured_at,
            retention_days=payload.retention_days,
        )

        resp = EvidenceResponse(
            id=record.id,
            event_id=record.event_id,
            camera_id=record.camera_id,
            file_path=record.file_path,
            file_type=record.file_type,
            mime_type=record.mime_type,
            file_size_bytes=record.file_size_bytes,
            sha256_hash=record.sha256_hash,
            captured_at=record.captured_at,
            retention_days=record.retention_days,
            created_at=record.created_at,
        )
        return APIResponse(data=resp, message="Evidence archived securely with SHA-256 digest.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to archive evidence: {str(e)}",
        )


@router.get(
    "",
    response_model=APIResponse[EvidenceListResponse],
    summary="Query archived evidence records",
)
async def list_evidence(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    event_id: Optional[str] = Query(None, description="Filter by linked vehicle event ID"),
    file_type: Optional[str] = Query(None, description="Filter by evidence file type"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[EvidenceListResponse]:
    """Retrieve list of archived evidence with cryptographic hashes."""
    query = select(Evidence)
    if camera_id:
        query = query.where(Evidence.camera_id == camera_id)
    if event_id:
        query = query.where(Evidence.event_id == event_id)
    if file_type:
        query = query.where(Evidence.file_type == file_type)

    query = query.order_by(Evidence.captured_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    items = [
        EvidenceResponse(
            id=r.id,
            event_id=r.event_id,
            camera_id=r.camera_id,
            file_path=r.file_path,
            file_type=r.file_type,
            mime_type=r.mime_type,
            file_size_bytes=r.file_size_bytes,
            sha256_hash=r.sha256_hash,
            captured_at=r.captured_at,
            retention_days=r.retention_days,
            created_at=r.created_at,
        )
        for r in records
    ]
    return APIResponse(
        data=EvidenceListResponse(total=len(items), items=items),
        message=f"Retrieved {len(items)} evidence records.",
    )


@router.get(
    "/telemetry",
    response_model=APIResponse[EvidenceTelemetry],
    summary="Evidence vault storage and integrity verification telemetry",
)
async def get_evidence_telemetry(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[EvidenceTelemetry]:
    """Get live metrics on total archived evidence, storage usage, and verification checks."""
    telemetry = await evidence_vault_service.get_telemetry(db)
    return APIResponse(data=telemetry, message="Evidence telemetry retrieved.")


@router.get(
    "/{evidence_id}",
    response_model=APIResponse[EvidenceResponse],
    summary="Get evidence details and cryptographic hash",
)
async def get_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[EvidenceResponse]:
    """Fetch single evidence record by ID."""
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence {evidence_id} not found.",
        )

    return APIResponse(
        data=EvidenceResponse(
            id=record.id,
            event_id=record.event_id,
            camera_id=record.camera_id,
            file_path=record.file_path,
            file_type=record.file_type,
            mime_type=record.mime_type,
            file_size_bytes=record.file_size_bytes,
            sha256_hash=record.sha256_hash,
            captured_at=record.captured_at,
            retention_days=record.retention_days,
            created_at=record.created_at,
        ),
        message="Evidence details retrieved.",
    )


@router.get(
    "/{evidence_id}/download",
    summary="Download raw or watermarked forensic evidence image with cryptographic headers",
)
async def download_evidence(
    evidence_id: str,
    watermark: bool = Query(False, description="Whether to download watermarked inspection copy"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download physical evidence file directly with SHA-256 integrity verification header."""
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence {evidence_id} not found.",
        )

    if watermark:
        try:
            _, watermarked_bytes = await evidence_vault_service.apply_forensic_watermark(db, evidence_id)
            return Response(
                content=watermarked_bytes,
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f"inline; filename=watermark_{evidence_id}.jpg",
                    "X-Evidence-ID": record.id,
                    "X-Evidence-Original-SHA256": record.sha256_hash,
                    "X-Evidence-Watermarked": "true",
                },
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate watermark: {str(e)}",
            )

    from pathlib import Path
    p = Path(record.file_path)
    if not p.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical evidence file missing on disk.",
        )

    return FileResponse(
        path=str(p),
        media_type=record.mime_type,
        filename=p.name,
        headers={
            "X-Evidence-ID": record.id,
            "X-Evidence-SHA256": record.sha256_hash,
            "X-Evidence-Camera": record.camera_id,
            "X-Evidence-Captured-At": record.captured_at.isoformat(),
        },
    )


@router.post(
    "/{evidence_id}/verify",
    response_model=APIResponse[EvidenceVerifyResult],
    summary="Cryptographically verify physical evidence against recorded SHA-256 hash",
)
async def verify_evidence_hash(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[EvidenceVerifyResult]:
    """Execute live SHA-256 hash check on disk file vs custody database record."""
    verification = await evidence_vault_service.verify_evidence_integrity(db, evidence_id)
    return APIResponse(
        data=verification,
        message=verification.message,
    )


@router.post(
    "/verify-batch",
    response_model=APIResponse[BatchVerifyResult],
    summary="Execute batch forensic integrity audit",
)
async def verify_batch_evidence(
    camera_id: Optional[str] = Query(None, description="Optional camera ID filter"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BatchVerifyResult]:
    """Audit up to N evidence items for tamper detection."""
    batch_res = await evidence_vault_service.verify_batch(db, camera_id=camera_id, limit=limit)
    return APIResponse(
        data=batch_res,
        message=f"Batch audit completed: {batch_res.verified_matches}/{batch_res.total_evaluated} verified match.",
    )


@router.post(
    "/{evidence_id}/watermark",
    response_model=APIResponse[ForensicWatermarkResponse],
    summary="Generate forensic watermarked inspection copy",
)
async def create_watermark(
    evidence_id: str,
    payload: ForensicWatermarkRequest = ForensicWatermarkRequest(),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ForensicWatermarkResponse]:
    """Stamp forensic legal and cryptographic watermark onto snapshot."""
    try:
        watermark_info, _ = await evidence_vault_service.apply_forensic_watermark(
            db, evidence_id, payload
        )
        return APIResponse(
            data=watermark_info,
            message="Forensic watermark applied successfully.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate watermark: {str(e)}",
        )


@router.post(
    "/{evidence_id}/section-65b",
    response_model=APIResponse[Section65BCertificate],
    summary="Generate Section 65B Indian Evidence Act Certificate",
)
async def get_section_65b_certificate(
    evidence_id: str,
    badge_id: str = Query("POLICE-HQ-01", description="Certifying officer badge"),
    officer_name: str = Query("Forensic Station Officer", description="Certifying officer name"),
    case_ref: str = Query("CASE-2026-GJ-001", description="FIR / Police Case Number"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Section65BCertificate]:
    """Produce Section 65B Electronic Evidence Certificate for courtroom submission."""
    try:
        cert = await evidence_vault_service.generate_section_65b_certificate(
            db=db,
            evidence_id=evidence_id,
            certifying_officer_badge=badge_id,
            certifying_officer_name=officer_name,
            case_reference=case_ref,
        )
        return APIResponse(
            data=cert,
            message="Section 65B Electronic Evidence Certificate generated.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate Section 65B certificate: {str(e)}",
        )


@router.post(
    "/courtroom-package",
    response_model=APIResponse[CourtroomExportPackage],
    summary="Generate complete courtroom dossier and manifest",
)
async def generate_courtroom_package(
    target_id: str = Query(..., description="Evidence ID or Vehicle Event ID"),
    case_reference: str = Query("CASE-2026-GJ-001", description="Case / FIR number"),
    officer_badge: str = Query("POLICE-HQ-01", description="Investigating officer badge"),
    officer_name: str = Query("Investigating Officer", description="Officer full name"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CourtroomExportPackage]:
    """Assemble complete courtroom dossier with Section 65B certificate and manifest hash."""
    try:
        package = await evidence_vault_service.create_courtroom_package(
            db=db,
            evidence_id_or_event_id=target_id,
            case_reference=case_reference,
            officer_badge=officer_badge,
            officer_name=officer_name,
        )
        return APIResponse(
            data=package,
            message="Courtroom evidence dossier generated successfully.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assemble courtroom package: {str(e)}",
        )
