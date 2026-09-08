"""Real-Time Alert and Notification Models for SentinelX."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.vehicle import VehicleEvent
    from app.models.watchlist import WatchlistEntry


class AlertStatus(str, Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Alert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Real-Time Watchlist Hit Alert Dispatched to Command Center Dashboard."""

    __tablename__ = "alerts"

    vehicle_event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicle_events.id", ondelete="CASCADE"), index=True, nullable=False
    )
    watchlist_entry_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("watchlist_entries.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    camera_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cameras.id", ondelete="CASCADE"), index=True, nullable=False
    )

    registration_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="STOLEN", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="HIGH", index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default=AlertStatus.NEW.value, index=True, nullable=False
    )

    alert_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    location_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    snapshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Operator Acknowledgement Tracking
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships with selectin loading
    event: Mapped["VehicleEvent"] = relationship(
        "VehicleEvent", back_populates="alerts", lazy="selectin"
    )
    watchlist_entry: Mapped[Optional["WatchlistEntry"]] = relationship(
        "WatchlistEntry", back_populates="alerts", lazy="selectin"
    )
    audit_events: Mapped[List["AlertEvent"]] = relationship(
        "AlertEvent", back_populates="alert", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (Index("ix_alerts_status_time", "status", "alert_time"),)


class AlertEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Lifecycle event on an alert (e.g. Dispatched, Viewed, Acknowledged, Resolved)."""

    __tablename__ = "alert_events"

    alert_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("alerts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # DISPATCHED, ACKNOWLEDGED, RESOLVED
    performed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    alert: Mapped[Alert] = relationship("Alert", back_populates="audit_events", lazy="selectin")
