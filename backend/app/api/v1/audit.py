"""Append-Only Immutable Audit Trail REST API Endpoints for SentinelX."""

from datetime import datetime
from typing import Optional

from app.db.session import get_db
from app.models.audit import AuditLog
from app.schemas.audit import (
    AuditChainVerification,
    AuditExportRequest,
    AuditExportResponse,
    AuditLogCreate,
    AuditLogListResponse,
    AuditLogResponse,
    AuditTelemetry,
)
from app.schemas.common import APIResponse
from app.services.audit_service import audit_service
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/audit", tags=["Append-Only Audit Trail"])


@router.post(
    "/log",
    response_model=APIResponse[AuditLogResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Append an immutable audit log record",
)
async def create_audit_log(
    payload: AuditLogCreate,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditLogResponse]:
    """Append a non-destructive audit event to the permanent record."""
    try:
        entry = await audit_service.log_action(
            db=db,
            username=payload.username,
            action=payload.action,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            ip_address=payload.ip_address,
            user_agent=payload.user_agent,
            details=payload.details,
            status=payload.status,
        )
        return APIResponse(
            data=AuditLogResponse(
                id=entry.id,
                username=entry.username,
                action=entry.action,
                resource_type=entry.resource_type,
                resource_id=entry.resource_id,
                timestamp=entry.timestamp,
                ip_address=entry.ip_address,
                user_agent=entry.user_agent,
                details=entry.details,
                status=entry.status,
                created_at=entry.created_at,
            ),
            message="Audit record appended successfully.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record audit log: {str(e)}",
        )


@router.get(
    "",
    response_model=APIResponse[AuditLogListResponse],
    summary="Query audit logs with multi-parameter filtering",
)
async def list_audit_logs(
    username: Optional[str] = Query(None, description="Filter by username or badge ID"),
    action: Optional[str] = Query(None, description="Filter by action category"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by target resource UUID"),
    status_val: Optional[str] = Query(None, alias="status", description="Filter by status (SUCCESS, FAILURE, DENIED)"),
    start_time: Optional[datetime] = Query(None, description="Earliest timestamp"),
    end_time: Optional[datetime] = Query(None, description="Latest timestamp"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditLogListResponse]:
    """Retrieve audit log history for compliance, tracking, and forensic analysis."""
    records, total_count = await audit_service.query_logs(
        db=db,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status_val,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    items = [
        AuditLogResponse(
            id=r.id,
            username=r.username,
            action=r.action,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            timestamp=r.timestamp,
            ip_address=r.ip_address,
            user_agent=r.user_agent,
            details=r.details,
            status=r.status,
            created_at=r.created_at,
        )
        for r in records
    ]
    return APIResponse(
        data=AuditLogListResponse(total=total_count, items=items),
        message=f"Retrieved {len(items)} of {total_count} audit logs.",
    )


@router.get(
    "/telemetry",
    response_model=APIResponse[AuditTelemetry],
    summary="Retrieve audit logging metrics and telemetry",
)
async def get_audit_telemetry(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditTelemetry]:
    """Get metrics on audit log volume, failure rates, and action breakdowns."""
    telemetry = await audit_service.get_telemetry(db)
    return APIResponse(data=telemetry, message="Audit telemetry retrieved.")


@router.get(
    "/{audit_id}",
    response_model=APIResponse[AuditLogResponse],
    summary="Get single audit log entry by ID",
)
async def get_audit_log(
    audit_id: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditLogResponse]:
    """Fetch specific audit record details."""
    result = await db.execute(select(AuditLog).where(AuditLog.id == audit_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log {audit_id} not found.",
        )

    return APIResponse(
        data=AuditLogResponse(
            id=record.id,
            username=record.username,
            action=record.action,
            resource_type=record.resource_type,
            resource_id=record.resource_id,
            timestamp=record.timestamp,
            ip_address=record.ip_address,
            user_agent=record.user_agent,
            details=record.details,
            status=record.status,
            created_at=record.created_at,
        ),
        message="Audit record retrieved.",
    )


@router.post(
    "/export",
    response_model=APIResponse[AuditExportResponse],
    summary="Export compliance audit report in CSV/JSON with SHA-256 checksum",
)
async def export_audit_trail(
    payload: AuditExportRequest = AuditExportRequest(),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditExportResponse]:
    """Generate signed audit export for statutory compliance and internal review."""
    try:
        export_res = await audit_service.export_audit_trail(db, payload)
        return APIResponse(
            data=export_res,
            message=f"Audit trail exported ({export_res.record_count} records) with SHA-256 digest.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate audit export: {str(e)}",
        )


@router.post(
    "/verify-chain",
    response_model=APIResponse[AuditChainVerification],
    summary="Cryptographically verify chronological audit hash chain",
)
async def verify_audit_chain(
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditChainVerification]:
    """Verify cryptographic integrity chain of audit logs to guarantee zero tampering."""
    verification = await audit_service.verify_audit_chain(db, limit=limit)
    return APIResponse(data=verification, message=verification.message)
