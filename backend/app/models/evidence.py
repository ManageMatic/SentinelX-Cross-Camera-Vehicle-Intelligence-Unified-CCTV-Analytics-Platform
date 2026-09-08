"""Evidence Vault and Cryptographic Hash Tracking Models for SentinelX."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Evidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Forensic Evidence Record with SHA-256 integrity hash verification."""

    __tablename__ = "evidence"

    event_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("vehicle_events.id", ondelete="SET NULL"), index=True, nullable=True
    )
    camera_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cameras.id", ondelete="CASCADE"), index=True, nullable=False
    )

    file_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    file_type: Mapped[str] = mapped_column(
        String(50), default="SNAPSHOT", nullable=False
    )  # SNAPSHOT, PLATE_CROP, VIDEO_CLIP
    mime_type: Mapped[str] = mapped_column(String(50), default="image/jpeg", nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Cryptographic SHA-256 for non-repudiation and forensic chain-of-custody
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    retention_days: Mapped[int] = mapped_column(BigInteger, default=90, nullable=False)

    __table_args__ = (Index("ix_evidence_captured_type", "captured_at", "file_type"),)
