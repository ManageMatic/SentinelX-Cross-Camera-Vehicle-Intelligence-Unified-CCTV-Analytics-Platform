"""Frame Buffer Manager and Adaptive Backpressure Queue Service (Module 9).

Provides bounded, thread-safe per-camera ring buffers with intelligent frame-dropping,
FPS decimation rate-limiting, and congestion monitoring to prevent memory exhaustion
and AI pipeline latency spikes.
"""

import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.schemas.buffer import (
    BackpressureLevel,
    BufferConfig,
    BufferPoolStatus,
    CameraBufferStats,
    FrameDropStrategy,
)
from app.schemas.stream import VideoFrame

logger = logging.getLogger("sentinelx.buffer")


class CameraFrameBuffer:
    """Thread-safe, bounded ring-buffer queue for an individual CCTV camera stream."""

    def __init__(self, camera_id: str, config: Optional[BufferConfig] = None) -> None:
        self.camera_id = camera_id
        self.config = config or BufferConfig()
        self._lock = threading.Lock()
        self._queue: deque[VideoFrame] = deque(maxlen=self.config.max_capacity)

        # Counters & Telemetry
        self._total_ingested: int = 0
        self._total_dispatched: int = 0
        self._total_dropped: int = 0
        self._last_ingested_at: Optional[datetime] = None
        self._last_dispatched_at: Optional[datetime] = None

        # Decimation & Rate-limiting state
        self._last_enqueued_time: float = 0.0

        # Sliding window timestamps for FPS calculation
        self._ingest_timestamps: deque[float] = deque(maxlen=50)
        self._dispatch_timestamps: deque[float] = deque(maxlen=50)

    def configure(self, config: BufferConfig) -> None:
        """Update buffer configuration dynamically."""
        with self._lock:
            self.config = config
            # Resize deque if max_capacity changed
            if self._queue.maxlen != config.max_capacity:
                old_items = list(self._queue)
                self._queue = deque(old_items[-config.max_capacity :], maxlen=config.max_capacity)

    def push_frame(self, frame: VideoFrame, bypass_decimation: bool = False) -> bool:
        """Push a newly decoded video frame into the bounded buffer applying decimation and backpressure.

        Returns True if the frame was accepted into the buffer, False if dropped.
        """
        now_ts = time.time()
        now_dt = datetime.now(timezone.utc)

        with self._lock:
            self._total_ingested += 1
            self._last_ingested_at = now_dt
            self._ingest_timestamps.append(now_ts)

            # 1. FPS Decimation Filter
            if not bypass_decimation and self.config.target_ai_fps < 60.0:
                target_interval = 1.0 / max(0.1, self.config.target_ai_fps)
                time_since_last = now_ts - self._last_enqueued_time

                # If not enough time has elapsed since last enqueued frame, drop for decimation
                if self._last_enqueued_time > 0 and time_since_last < (target_interval * 0.90):
                    self._total_dropped += 1
                    return False

            # 2. Backpressure and Queue Capacity Checks
            current_len = len(self._queue)
            threshold_capacity = max(
                1, int(self.config.max_capacity * (self.config.backpressure_threshold_pct / 100.0))
            )

            if current_len >= threshold_capacity:
                # Buffer is congested — apply drop strategy
                if self.config.drop_strategy == FrameDropStrategy.DROP_NEWEST:
                    if current_len >= self.config.max_capacity:
                        self._total_dropped += 1
                        return False

                elif self.config.drop_strategy == FrameDropStrategy.DROP_NON_KEYFRAME:
                    if frame.is_keyframe:
                        if len(self._queue) >= self.config.max_capacity:
                            # Evict oldest non-keyframe or oldest item
                            non_kf_idx = next(
                                (i for i, f in enumerate(self._queue) if not f.is_keyframe), None
                            )
                            if non_kf_idx is not None:
                                del self._queue[non_kf_idx]
                            else:
                                self._queue.popleft()
                            self._total_dropped += 1
                    else:
                        # Non-keyframe arrives during congestion -> drop it
                        self._total_dropped += 1
                        return False

                elif self.config.drop_strategy == FrameDropStrategy.DECIMATE_DYNAMIC:
                    target_interval = 1.0 / max(0.1, self.config.target_ai_fps)
                    time_since_last = now_ts - self._last_enqueued_time
                    if time_since_last < (target_interval * 1.5):
                        self._total_dropped += 1
                        return False
                    if len(self._queue) >= self.config.max_capacity:
                        self._queue.popleft()
                        self._total_dropped += 1

                else:  # FrameDropStrategy.DROP_OLDEST (Default)
                    if len(self._queue) >= self.config.max_capacity:
                        self._queue.popleft()
                        self._total_dropped += 1

            # 3. Enqueue frame
            self._queue.append(frame)
            self._last_enqueued_time = now_ts
            return True

    def pop_frame(self) -> Optional[VideoFrame]:
        """Pop the next available video frame for AI inference."""
        now_ts = time.time()
        now_dt = datetime.now(timezone.utc)

        with self._lock:
            if not self._queue:
                return None

            frame = self._queue.popleft()
            self._total_dispatched += 1
            self._last_dispatched_at = now_dt
            self._dispatch_timestamps.append(now_ts)
            return frame

    def peek_frame(self) -> Optional[VideoFrame]:
        """Peek at the oldest frame without removing it from queue."""
        with self._lock:
            return self._queue[0] if self._queue else None

    def clear(self) -> int:
        """Clear all frames currently held in the queue. Returns count of discarded frames."""
        with self._lock:
            discarded = len(self._queue)
            self._queue.clear()
            self._total_dropped += discarded
            return discarded

    def get_stats(self) -> CameraBufferStats:
        """Compute real-time queue utilization, drop rates, and backpressure telemetry."""
        with self._lock:
            queue_len = len(self._queue)
            max_cap = self.config.max_capacity
            utilization = (queue_len / max_cap * 100.0) if max_cap > 0 else 0.0

            if utilization < 60.0:
                backpressure = BackpressureLevel.NORMAL
            elif utilization <= 85.0:
                backpressure = BackpressureLevel.MODERATE
            else:
                backpressure = BackpressureLevel.CRITICAL

            # Calculate FPS based on sliding window
            now = time.time()
            cutoff = now - 3.0

            valid_ingests = [t for t in self._ingest_timestamps if t >= cutoff]
            ingest_fps = len(valid_ingests) / 3.0 if valid_ingests else 0.0

            valid_dispatches = [t for t in self._dispatch_timestamps if t >= cutoff]
            dispatch_fps = len(valid_dispatches) / 3.0 if valid_dispatches else 0.0

            total_processed = self._total_dispatched + self._total_dropped
            drop_rate_pct = (
                (self._total_dropped / total_processed * 100.0) if total_processed > 0 else 0.0
            )

            return CameraBufferStats(
                camera_id=self.camera_id,
                queue_size=queue_len,
                max_capacity=max_cap,
                utilization_pct=round(utilization, 2),
                backpressure_level=backpressure,
                target_ai_fps=self.config.target_ai_fps,
                ingest_fps=round(ingest_fps, 2),
                dispatch_fps=round(dispatch_fps, 2),
                total_ingested_frames=self._total_ingested,
                total_dispatched_frames=self._total_dispatched,
                total_dropped_frames=self._total_dropped,
                drop_rate_pct=round(drop_rate_pct, 2),
                last_ingested_at=self._last_ingested_at,
                last_dispatched_at=self._last_dispatched_at,
            )


class FrameBufferManager:
    """Platform-wide coordinator managing bounded frame buffers across all dynamic camera streams."""

    def __init__(self) -> None:
        self._buffers: Dict[str, CameraFrameBuffer] = {}
        self._lock = threading.Lock()

    def get_or_create_buffer(
        self, camera_id: str, config: Optional[BufferConfig] = None
    ) -> CameraFrameBuffer:
        """Retrieve existing camera buffer or initialize a new bounded ring-buffer."""
        with self._lock:
            if camera_id not in self._buffers:
                self._buffers[camera_id] = CameraFrameBuffer(camera_id, config)
            elif config is not None:
                self._buffers[camera_id].configure(config)
            return self._buffers[camera_id]

    def push_frame(
        self, camera_id: str, frame: VideoFrame, bypass_decimation: bool = False
    ) -> bool:
        """Push a video frame into the appropriate camera buffer."""
        buffer = self.get_or_create_buffer(camera_id)
        return buffer.push_frame(frame, bypass_decimation=bypass_decimation)

    def pop_frame(self, camera_id: str) -> Optional[VideoFrame]:
        """Pop the next video frame from the specified camera buffer."""
        with self._lock:
            buffer = self._buffers.get(camera_id)
        if buffer is None:
            return None
        return buffer.pop_frame()

    def get_buffer_stats(self, camera_id: str) -> Optional[CameraBufferStats]:
        """Retrieve buffer telemetry for a specific camera."""
        with self._lock:
            buffer = self._buffers.get(camera_id)
        if buffer is None:
            return None
        return buffer.get_stats()

    def configure_buffer(self, camera_id: str, config: BufferConfig) -> CameraBufferStats:
        """Dynamically tune configuration for a specific camera buffer."""
        buffer = self.get_or_create_buffer(camera_id, config)
        return buffer.get_stats()

    def clear_buffer(self, camera_id: str) -> bool:
        """Clear all frames in a camera's buffer queue."""
        with self._lock:
            buffer = self._buffers.get(camera_id)
        if buffer is None:
            return False
        buffer.clear()
        return True

    def clear_all(self) -> int:
        """Clear all buffers across the platform."""
        with self._lock:
            buffers = list(self._buffers.values())
        total = sum(b.clear() for b in buffers)
        return total

    def get_pool_status(self) -> BufferPoolStatus:
        """Aggregate telemetry across all camera frame buffers."""
        with self._lock:
            buffers = list(self._buffers.values())

        stats_list: List[CameraBufferStats] = [b.get_stats() for b in buffers]
        active_queues = sum(1 for s in stats_list if s.queue_size > 0)
        critical_queues = sum(
            1 for s in stats_list if s.backpressure_level == BackpressureLevel.CRITICAL
        )
        total_buffered = sum(s.queue_size for s in stats_list)
        total_dropped = sum(s.total_dropped_frames for s in stats_list)
        avg_utilization = (
            (sum(s.utilization_pct for s in stats_list) / len(stats_list)) if stats_list else 0.0
        )

        return BufferPoolStatus(
            total_buffers=len(stats_list),
            active_queues=active_queues,
            critical_queues=critical_queues,
            total_buffered_frames=total_buffered,
            total_dropped_frames=total_dropped,
            average_utilization_pct=round(avg_utilization, 2),
            timestamp=datetime.now(timezone.utc),
            buffers=stats_list,
        )


# Global singleton instance
frame_buffer_manager = FrameBufferManager()
