"""Tamper-Evident Audit Logging Models for SentinelX."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Append-Only Forensic Audit Record tracking all critical user operations."""

    __tablename__ = "audit_logs"

    username: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    action: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )  # VEHICLE_SEARCH, WATCHLIST_EDIT, ALERT_ACK, EVIDENCE_ACCESS
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="SUCCESS", nullable=False)

    __table_args__ = (Index("ix_audit_logs_user_action", "username", "action", "timestamp"),)
