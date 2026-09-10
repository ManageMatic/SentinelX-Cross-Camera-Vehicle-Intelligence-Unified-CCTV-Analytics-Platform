"""Pydantic schemas and enums for Stream Resilience, Watchdogs, and Circuit Breakers."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CircuitBreakerState(str, Enum):
    """Circuit breaker operational state."""

    CLOSED = "CLOSED"  # Normal operation: requests / streams pass through
    OPEN = "OPEN"  # Tripped: stream failed too many times, backoff active
    HALF_OPEN = "HALF_OPEN"  # Trial mode: attempting single reconnect to probe camera health


class StreamWatchdogRecord(BaseModel):
    """Watchdog tracking telemetry for an individual camera stream."""

    camera_id: str
    external_camera_id: str
    state: str
    circuit_state: CircuitBreakerState
    is_stalled: bool
    seconds_since_last_frame: float
    measured_fps: float
    consecutive_failures: int
    reconnect_attempts: int
    next_reconnect_at: Optional[datetime] = None
    last_error: Optional[str] = None
    last_healthy_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StreamHealthSummary(BaseModel):
    """Aggregate health and watchdog summary across all camera streams."""

    total_monitored: int
    healthy_count: int
    stalled_count: int
    reconnecting_count: int
    tripped_circuit_count: int
    aggregate_fps: float
    timestamp: datetime
    streams: List[StreamWatchdogRecord] = Field(default_factory=list)
