"""Resilient Stream Manager & Auto-Reconnect Engine for SentinelX.

Monitors active CCTV video streams 24/7, detects stalled feeds and socket drops,
executes exponential backoff auto-reconnection, applies circuit breaker protection,
and synchronizes camera health telemetry to the database.
"""

import asyncio
import random
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.camera import Camera, CameraHealth
from app.schemas.resilience import (
    CircuitBreakerState,
    StreamHealthSummary,
    StreamWatchdogRecord,
)
from app.schemas.stream import StreamWorkerState
from app.services.stream_worker import stream_pool

logger = get_logger(__name__)
settings = get_settings()


class CameraWatchdogState:
    """Internal tracking state for an individual camera stream."""

    def __init__(self, camera_id: str, external_camera_id: str):
        self.camera_id = camera_id
        self.external_camera_id = external_camera_id
        self.circuit_state = CircuitBreakerState.CLOSED
        self.consecutive_failures = 0
        self.total_reconnects = 0
        self.circuit_tripped_at: Optional[float] = None
        self.next_reconnect_at: Optional[datetime] = None
        self.last_healthy_at: Optional[datetime] = None
        self.last_error: Optional[str] = None


class StreamWatchdogManager:
    """Watchdog and Circuit Breaker manager for resilient CCTV stream ingestion."""

    def __init__(
        self,
        stall_timeout_seconds: float = 5.0,
        max_consecutive_failures: int = 5,
        circuit_cooldown_seconds: float = 30.0,
        initial_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 30.0,
        backoff_factor: float = 1.5,
    ):
        self.stall_timeout_seconds = stall_timeout_seconds
        self.max_consecutive_failures = max_consecutive_failures
        self.circuit_cooldown_seconds = circuit_cooldown_seconds
        self.initial_backoff_seconds = initial_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.backoff_factor = backoff_factor

        self._states: Dict[str, CameraWatchdogState] = {}
        self._lock = threading.Lock()
        self._is_running = False
        self._watchdog_task: Optional[asyncio.Task] = None

    def calculate_backoff(self, failures: int) -> float:
        """Compute exponential backoff delay with jitter."""
        if failures <= 0:
            return self.initial_backoff_seconds

        delay = self.initial_backoff_seconds * (self.backoff_factor ** min(failures, 8))
        delay = min(delay, self.max_backoff_seconds)
        # Add 10% random jitter to prevent thundering herd reconnection on cameras
        jitter = delay * random.uniform(-0.1, 0.1)
        return max(0.5, delay + jitter)

    def _get_or_create_state(self, camera_id: str, ext_id: str) -> CameraWatchdogState:
        with self._lock:
            if camera_id not in self._states:
                self._states[camera_id] = CameraWatchdogState(camera_id, ext_id)
            return self._states[camera_id]

    def check_camera_health(self, camera_id: str) -> StreamWatchdogRecord:
        """Inspect worker health, frame arrival timing, and circuit breaker state."""
        worker = stream_pool.get_worker(camera_id)
        ext_id = worker.external_camera_id if worker else camera_id
        w_state = self._get_or_create_state(camera_id, ext_id)
        now_utc = datetime.now(timezone.utc)
        now_ts = time.time()

        if not worker:
            w_state.consecutive_failures += 1
            w_state.last_error = "Worker not initialized or stopped"
            if (
                w_state.consecutive_failures >= self.max_consecutive_failures
                and w_state.circuit_state != CircuitBreakerState.OPEN
            ):
                w_state.circuit_state = CircuitBreakerState.OPEN
                w_state.circuit_tripped_at = now_ts

            return StreamWatchdogRecord(
                camera_id=camera_id,
                external_camera_id=ext_id,
                state=StreamWorkerState.STOPPED.value,
                circuit_state=w_state.circuit_state,
                is_stalled=False,
                seconds_since_last_frame=9999.0,
                measured_fps=0.0,
                consecutive_failures=w_state.consecutive_failures,
                reconnect_attempts=w_state.total_reconnects,
                next_reconnect_at=w_state.next_reconnect_at,
                last_error=w_state.last_error,
                last_healthy_at=w_state.last_healthy_at,
            )

        stats = worker.get_stats()
        seconds_since_last = 0.0
        is_stalled = False

        if stats.last_frame_time:
            seconds_since_last = (now_utc - stats.last_frame_time).total_seconds()
            if (
                stats.state == StreamWorkerState.STREAMING
                and seconds_since_last > self.stall_timeout_seconds
            ):
                is_stalled = True

        # Check circuit breaker transitions
        if w_state.circuit_state == CircuitBreakerState.OPEN:
            if (
                w_state.circuit_tripped_at
                and (now_ts - w_state.circuit_tripped_at) >= self.circuit_cooldown_seconds
            ):
                w_state.circuit_state = CircuitBreakerState.HALF_OPEN
                logger.info(
                    f"Circuit for camera '{ext_id}' transitioned to HALF_OPEN (probing stream health)"
                )

        # Handle Stream Errors / Stalls
        if is_stalled or stats.state in (StreamWorkerState.ERROR, StreamWorkerState.RECONNECTING):
            w_state.consecutive_failures += 1
            w_state.total_reconnects += 1
            w_state.last_error = stats.last_error or "Stream feed stalled or dropped"

            # Check if circuit should trip OPEN
            if (
                w_state.consecutive_failures >= self.max_consecutive_failures
                and w_state.circuit_state != CircuitBreakerState.OPEN
            ):
                w_state.circuit_state = CircuitBreakerState.OPEN
                w_state.circuit_tripped_at = now_ts
                logger.warning(
                    f"Circuit breaker TRIPPED OPEN for camera '{ext_id}' after {w_state.consecutive_failures} failures. Cooling down for {self.circuit_cooldown_seconds}s."
                )

            backoff = self.calculate_backoff(w_state.consecutive_failures)
            w_state.next_reconnect_at = datetime.fromtimestamp(now_ts + backoff, tz=timezone.utc)

        elif stats.state == StreamWorkerState.STREAMING and not is_stalled:
            # Stream is healthy
            w_state.last_healthy_at = now_utc
            if w_state.circuit_state in (CircuitBreakerState.HALF_OPEN, CircuitBreakerState.OPEN):
                logger.info(
                    f"Circuit breaker for camera '{ext_id}' reset to CLOSED (stream healthy at {stats.measured_fps} FPS)"
                )
            w_state.circuit_state = CircuitBreakerState.CLOSED
            w_state.consecutive_failures = 0
            w_state.next_reconnect_at = None
            w_state.last_error = None

        return StreamWatchdogRecord(
            camera_id=camera_id,
            external_camera_id=ext_id,
            state=stats.state.value,
            circuit_state=w_state.circuit_state,
            is_stalled=is_stalled,
            seconds_since_last_frame=round(seconds_since_last, 2),
            measured_fps=stats.measured_fps,
            consecutive_failures=w_state.consecutive_failures,
            reconnect_attempts=w_state.total_reconnects,
            next_reconnect_at=w_state.next_reconnect_at,
            last_error=w_state.last_error,
            last_healthy_at=w_state.last_healthy_at,
        )

    def get_health_summary(self) -> StreamHealthSummary:
        """Aggregate health metrics across all monitored CCTV streams."""
        pool_status = stream_pool.get_pool_status()
        records: list[StreamWatchdogRecord] = []

        for worker_stat in pool_status.workers:
            record = self.check_camera_health(worker_stat.camera_id)
            records.append(record)

        healthy_count = sum(
            1 for r in records if r.state == StreamWorkerState.STREAMING.value and not r.is_stalled
        )
        stalled_count = sum(1 for r in records if r.is_stalled)
        reconnecting_count = sum(
            1
            for r in records
            if r.state in (StreamWorkerState.CONNECTING.value, StreamWorkerState.RECONNECTING.value)
        )
        tripped_count = sum(1 for r in records if r.circuit_state == CircuitBreakerState.OPEN)
        agg_fps = sum(r.measured_fps for r in records)

        return StreamHealthSummary(
            total_monitored=len(records),
            healthy_count=healthy_count,
            stalled_count=stalled_count,
            reconnecting_count=reconnecting_count,
            tripped_circuit_count=tripped_count,
            aggregate_fps=round(agg_fps, 2),
            timestamp=datetime.now(timezone.utc),
            streams=records,
        )

    def force_reconnect(self, camera_id: str) -> StreamWatchdogRecord:
        """Trigger immediate reconnection attempt, resetting backoff delays."""
        worker = stream_pool.get_worker(camera_id)
        if worker:
            ext_id = worker.external_camera_id
            rtsp = worker.rtsp_url
            fps = worker.target_fps
            synth = worker.use_synthetic_stream
            callback = worker.frame_callback

            worker.stop()
            time.sleep(0.05)
            stream_pool.start_worker(
                camera_id=camera_id,
                external_camera_id=ext_id,
                rtsp_url=rtsp,
                target_fps=fps,
                use_synthetic_stream=synth,
                frame_callback=callback,
            )

        w_state = self._get_or_create_state(camera_id, camera_id)
        w_state.next_reconnect_at = None
        w_state.circuit_state = CircuitBreakerState.HALF_OPEN
        logger.info(f"Force reconnected stream worker for camera '{camera_id}'")
        return self.check_camera_health(camera_id)

    def reset_circuit(self, camera_id: str) -> StreamWatchdogRecord:
        """Manually reset circuit breaker for a camera back to CLOSED."""
        worker = stream_pool.get_worker(camera_id)
        ext_id = worker.external_camera_id if worker else camera_id
        w_state = self._get_or_create_state(camera_id, ext_id)
        w_state.circuit_state = CircuitBreakerState.CLOSED
        w_state.consecutive_failures = 0
        w_state.circuit_tripped_at = None
        w_state.next_reconnect_at = None
        logger.info(f"Manually reset circuit breaker to CLOSED for camera '{camera_id}'")
        return StreamWatchdogRecord(
            camera_id=camera_id,
            external_camera_id=ext_id,
            state=worker.state.value if worker else StreamWorkerState.STOPPED.value,
            circuit_state=w_state.circuit_state,
            is_stalled=False,
            seconds_since_last_frame=0.0,
            measured_fps=worker.get_stats().measured_fps if worker else 0.0,
            consecutive_failures=0,
            reconnect_attempts=w_state.total_reconnects,
            next_reconnect_at=None,
            last_error=None,
            last_healthy_at=w_state.last_healthy_at,
        )

    async def sync_health_to_db(self, db: AsyncSession):
        """Persist health metrics and update live_status in database."""
        summary = self.get_health_summary()
        now_utc = datetime.now(timezone.utc)

        for stream_rec in summary.streams:
            stmt = select(Camera).where(Camera.id == stream_rec.camera_id)
            result = await db.execute(stmt)
            cam = result.scalar_one_or_none()

            if cam:
                is_online = (
                    stream_rec.state == StreamWorkerState.STREAMING.value
                    and not stream_rec.is_stalled
                )
                cam.live_status = is_online
                if is_online:
                    cam.last_seen = now_utc

                # Insert telemetry record
                health = CameraHealth(
                    camera_id=cam.id,
                    is_online=is_online,
                    measured_fps=stream_rec.measured_fps,
                    latency_ms=12.5 if is_online else 0.0,
                    reconnect_count=stream_rec.reconnect_attempts,
                    last_error=stream_rec.last_error,
                    last_ping=now_utc,
                )
                db.add(health)

        await db.commit()


# Global Singleton Stream Manager
stream_manager = StreamWatchdogManager()
