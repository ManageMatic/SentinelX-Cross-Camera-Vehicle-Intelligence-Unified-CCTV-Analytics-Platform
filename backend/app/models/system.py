"""System Health Telemetry and Worker Status Models for SentinelX."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemHealthMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Historical snapshot of system performance, queue depths, and worker telemetry."""

    __tablename__ = "system_health_metrics"

    service_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="HEALTHY", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    cpu_usage_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    memory_usage_mb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    active_streams: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inference_fps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    queue_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (Index("ix_system_health_time", "service_name", "timestamp"),)
