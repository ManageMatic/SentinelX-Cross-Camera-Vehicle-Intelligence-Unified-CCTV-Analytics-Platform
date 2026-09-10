"""Pydantic Schemas Package for SentinelX."""

from app.schemas.anpr import (
    ANPRBatchResult,
    ANPRConfig,
    ANPRResult,
    ANPRTelemetry,
    PlateCategory,
)
from app.schemas.buffer import (
    BackpressureLevel,
    BufferConfig,
    BufferPoolStatus,
    CameraBufferStats,
    FrameDropStrategy,
)
from app.schemas.camera import (
    CameraBase,
    CameraCreate,
    CameraDetailResponse,
    CameraHealthResponse,
    CameraResponse,
    CameraSourceResponse,
    CameraSyncResult,
    CameraUpdate,
    SentinelIngestCameraItem,
)
from app.schemas.common import (
    APIResponse,
    ErrorDetail,
    PaginatedResponse,
    PaginationMetadata,
    PaginationParams,
    utc_now_iso,
)
from app.schemas.detection import (
    BoundingBox,
    DetectedVehicle,
    DetectorConfig,
    DetectorTelemetry,
    FrameDetectionResult,
    VehicleClass,
)
from app.schemas.proxy import (
    CameraStreamEndpoints,
    StreamProxyInfo,
    WHEPExchangeRequest,
    WHEPExchangeResponse,
)
from app.schemas.resilience import (
    CircuitBreakerState,
    StreamHealthSummary,
    StreamWatchdogRecord,
)
from app.schemas.stream import (
    StreamPoolStatus,
    StreamWorkerState,
    StreamWorkerStats,
    VideoFrame,
)
from app.schemas.system import (
    ComponentHealth,
    HealthData,
    SystemStatusData,
    VersionData,
)
from app.schemas.tracking import (
    FrameTrackingResult,
    TrackedVehicle,
    TrackerConfig,
    TrackerTelemetry,
    TrackState,
    TrajectoryPoint,
)

__all__ = [
    "APIResponse",
    "PaginatedResponse",
    "PaginationMetadata",
    "PaginationParams",
    "ErrorDetail",
    "utc_now_iso",
    "HealthData",
    "VersionData",
    "ComponentHealth",
    "SystemStatusData",
    "SentinelIngestCameraItem",
    "CameraBase",
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "CameraDetailResponse",
    "CameraSourceResponse",
    "CameraHealthResponse",
    "CameraSyncResult",
    "VideoFrame",
    "StreamWorkerState",
    "StreamWorkerStats",
    "StreamPoolStatus",
    "CircuitBreakerState",
    "StreamWatchdogRecord",
    "StreamHealthSummary",
    "WHEPExchangeRequest",
    "WHEPExchangeResponse",
    "StreamProxyInfo",
    "CameraStreamEndpoints",
    "BackpressureLevel",
    "FrameDropStrategy",
    "BufferConfig",
    "CameraBufferStats",
    "BufferPoolStatus",
    "VehicleClass",
    "BoundingBox",
    "DetectedVehicle",
    "FrameDetectionResult",
    "DetectorConfig",
    "DetectorTelemetry",
    "TrackState",
    "TrajectoryPoint",
    "TrackedVehicle",
    "FrameTrackingResult",
    "TrackerConfig",
    "TrackerTelemetry",
    "PlateCategory",
    "ANPRResult",
    "ANPRBatchResult",
    "ANPRConfig",
    "ANPRTelemetry",
]
