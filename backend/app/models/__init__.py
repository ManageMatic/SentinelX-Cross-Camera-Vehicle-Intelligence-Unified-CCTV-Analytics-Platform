"""SentinelX Unified Database Models Package.

Exports all declarative models for migrations, metadata discovery, and ORM operations.
"""

from app.models.alert import Alert, AlertEvent, AlertStatus
from app.models.audit import AuditLog
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.models.camera import Camera, CameraHealth, CameraSource
from app.models.evidence import Evidence
from app.models.system import SystemHealthMetric
from app.models.user import Permission, Role, RoleType, User
from app.models.vehicle import (
    VehicleDetection,
    VehicleEmbedding,
    VehicleEvent,
    VehiclePlate,
    VehicleTrack,
)
from app.models.watchlist import (
    Watchlist,
    WatchlistCategory,
    WatchlistEntry,
    WatchlistPriority,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "utc_now",
    "User",
    "Role",
    "Permission",
    "RoleType",
    "Camera",
    "CameraSource",
    "CameraHealth",
    "VehicleDetection",
    "VehicleTrack",
    "VehicleEvent",
    "VehiclePlate",
    "VehicleEmbedding",
    "Watchlist",
    "WatchlistEntry",
    "WatchlistCategory",
    "WatchlistPriority",
    "Alert",
    "AlertEvent",
    "AlertStatus",
    "Evidence",
    "AuditLog",
    "SystemHealthMetric",
]
