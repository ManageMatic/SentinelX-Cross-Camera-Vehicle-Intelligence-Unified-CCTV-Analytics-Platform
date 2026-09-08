"""Camera Registry, Stream Sources, and Health Models for SentinelX."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.vehicle import VehicleEvent


class Camera(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Dynamic Camera Registry entry synchronized from Sentinel /api/ingest."""

    __tablename__ = "cameras"

    external_camera_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    location_name: Mapped[str] = mapped_column(String(255), default="Ahmedabad", nullable=False)
    department: Mapped[str] = mapped_column(String(100), default="Traffic Police", nullable=False)

    # Geospatial Coordinates (Compatible with Leaflet & PostGIS)
    latitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, index=True, nullable=False)

    # Technical Stream Specs
    vendor: Mapped[str] = mapped_column(String(100), default="Generic RTSP", nullable=False)
    vms: Mapped[str] = mapped_column(String(100), default="Sentinel VMS", nullable=False)
    protocol: Mapped[str] = mapped_column(String(50), default="RTSP/TCP", nullable=False)
    codec: Mapped[str] = mapped_column(String(50), default="H264", nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=1920, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=1080, nullable=False)
    fps: Mapped[float] = mapped_column(Float, default=25.0, nullable=False)

    # Stream URLs (Stored securely server-side; NEVER leaked directly to public frontend)
    rtsp_url: Mapped[str] = mapped_column(String(500), nullable=False)
    whep_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hls_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Operational Status
    live_status: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    is_active_for_ai: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=False
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships with selectin loading for async safety
    sources: Mapped[List["CameraSource"]] = relationship(
        "CameraSource",
        back_populates="camera",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    health_records: Mapped[List["CameraHealth"]] = relationship(
        "CameraHealth",
        back_populates="camera",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    vehicle_events: Mapped[List["VehicleEvent"]] = relationship(
        "VehicleEvent",
        back_populates="camera",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_cameras_lat_lon", "latitude", "longitude"),
        Index("ix_cameras_dept_status", "department", "live_status"),
    )


class CameraSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Auxiliary stream profiles (sub-stream, mobile HLS, high-res RTSP)."""

    __tablename__ = "camera_sources"

    camera_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False
    )
    stream_type: Mapped[str] = mapped_column(
        String(50), default="MAIN", nullable=False
    )  # MAIN, SUB, SNAPSHOT
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    codec: Mapped[str] = mapped_column(String(50), default="H264", nullable=False)
    resolution: Mapped[str] = mapped_column(String(50), default="1080p", nullable=False)

    camera: Mapped[Camera] = relationship("Camera", back_populates="sources", lazy="selectin")


class CameraHealth(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Real-time camera health telemetry, reconnection events, and FPS monitoring."""

    __tablename__ = "camera_health"

    camera_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cameras.id", ondelete="CASCADE"), index=True, nullable=False
    )
    is_online: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    measured_fps: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reconnect_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_ping: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    camera: Mapped[Camera] = relationship(
        "Camera", back_populates="health_records", lazy="selectin"
    )
