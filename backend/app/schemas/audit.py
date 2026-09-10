"""Audit Logging, Tamper-Evident Chain, and Compliance Export Schemas for SentinelX."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    """Categorized critical operator and system actions."""
    VEHICLE_SEARCH = "VEHICLE_SEARCH"
    WATCHLIST_CREATE = "WATCHLIST_CREATE"
    WATCHLIST_EDIT = "WATCHLIST_EDIT"
    WATCHLIST_DELETE = "WATCHLIST_DELETE"
    ALERT_ACK = "ALERT_ACK"
    ALERT_RESOLVE = "ALERT_RESOLVE"
    ALERT_DISMISS = "ALERT_DISMISS"
    EVIDENCE_ACCESS = "EVIDENCE_ACCESS"
    EVIDENCE_DOWNLOAD = "EVIDENCE_DOWNLOAD"
    EVIDENCE_WATERMARK = "EVIDENCE_WATERMARK"
    COURTROOM_EXPORT = "COURTROOM_EXPORT"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    CAMERA_CONFIG = "CAMERA_CONFIG"
    SYSTEM_CONFIG = "SYSTEM_CONFIG"
    OTHER = "OTHER"


class AuditStatus(str, Enum):
    """Outcome status of the audited operation."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    DENIED = "DENIED"
    ERROR = "ERROR"


class AuditExportFormat(str, Enum):
    """Format options for compliance export."""
    CSV = "CSV"
    JSON = "JSON"
    NDJSON = "NDJSON"


class AuditLogCreate(BaseModel):
    """Schema for recording a new append-only audit event."""
    username: str = Field(..., description="Badge ID or username of actor")
    action: Union[AuditAction, str] = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of target resource (e.g., VEHICLE_EVENT, WATCHLIST, EVIDENCE)")
    resource_id: Optional[str] = Field(None, description="Resource identifier or record UUID")
    ip_address: Optional[str] = Field("127.0.0.1", description="Client IP address")
    user_agent: Optional[str] = Field("SentinelX-Client", description="Client user agent / browser")
    details: Optional[Union[Dict[str, Any], str]] = Field(None, description="Action context or search query parameters")
    status: AuditStatus = Field(default=AuditStatus.SUCCESS, description="Operation outcome")


class AuditLogResponse(BaseModel):
    """Forensic immutable audit log record."""
    id: str
    username: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None


class AuditLogListResponse(BaseModel):
    """Paginated collection of audit log entries."""
    total: int
    items: List[AuditLogResponse]


class AuditExportRequest(BaseModel):
    """Parameters for exporting compliance audit reports."""
    username: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    export_format: AuditExportFormat = Field(default=AuditExportFormat.JSON)
    officer_badge: Optional[str] = Field(default="POLICE-HQ-01")


class AuditExportResponse(BaseModel):
    """Metadata and integrity checksum for generated audit export."""
    export_id: str
    record_count: int
    format: str
    export_sha256: str
    content: str
    generated_at: datetime


class AuditChainVerification(BaseModel):
    """Sequential cryptographic hash verification of audit logs."""
    total_records: int
    verified_chain: bool
    chain_sha256: str
    anomalies_detected: int
    verified_at: datetime
    message: str


class AuditTelemetry(BaseModel):
    """Audit engine performance and volume telemetry."""
    total_logs: int
    logs_last_24h: int
    actions_breakdown: Dict[str, int]
    failed_actions_count: int
    mean_logging_latency_ms: float
