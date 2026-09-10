"""RTSP / TCP Video Stream Ingestion Worker for SentinelX.

Decodes video frames over TCP to eliminate packet loss and visual artifacting on lossy CCTV networks.
Attaches synchronized UTC timestamps, measures live FPS, and feeds downstream AI pipelines.
"""

import collections
import os
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Deque, Dict, Optional

import cv2
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.stream import (
    StreamPoolStatus,
    StreamWorkerState,
    StreamWorkerStats,
    VideoFrame,
)

logger = get_logger(__name__)
settings = get_settings()

# Force OpenCV FFmpeg backend to enforce RTSP over TCP
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"


class RTSPStreamWorker:
    """Threaded RTSP / TCP Video Stream Ingestion Worker for a single camera feed."""

    def __init__(
        self,
        camera_id: str,
        external_camera_id: str,
        rtsp_url: str,
        target_fps: float = 25.0,
        use_synthetic_stream: bool = False,
        frame_callback: Optional[Callable[[VideoFrame], None]] = None,
    ):
        self.camera_id = camera_id
        self.external_camera_id = external_camera_id
        self.rtsp_url = rtsp_url
        self.target_fps = target_fps
        self.use_synthetic_stream = use_synthetic_stream
        self.frame_callback = frame_callback

        self._state = StreamWorkerState.INITIALIZING
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Telemetry & Frame Buffers
        self._latest_frame: Optional[VideoFrame] = None
        self._total_frames_read = 0
        self._dropped_frames = 0
        self._reconnect_attempts = 0
        self._start_time: Optional[float] = None
        self._last_frame_time: Optional[datetime] = None
        self._last_error: Optional[str] = None

        # Sliding window for accurate FPS calculation
        self._frame_timestamps: Deque[float] = collections.deque(maxlen=30)
        self._measured_fps = 0.0

    @property
    def state(self) -> StreamWorkerState:
        return self._state

    def start(self):
        """Start background ingestion thread."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                logger.warning(f"Worker for camera {self.external_camera_id} is already running.")
                return

            self._stop_event.clear()
            self._state = StreamWorkerState.CONNECTING
            self._start_time = time.time()
            self._thread = threading.Thread(
                target=self._run_ingestion_loop,
                name=f"RTSPWorker-{self.external_camera_id}",
                daemon=True,
            )
            self._thread.start()
            logger.info(
                f"Started RTSP/TCP ingestion worker for camera '{self.external_camera_id}' ({self.rtsp_url})"
            )

    def stop(self, timeout: float = 2.0):
        """Signal worker thread to stop and wait for termination."""
        self._stop_event.set()
        with self._lock:
            self._state = StreamWorkerState.STOPPED

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            logger.info(f"Stopped RTSP/TCP worker for camera '{self.external_camera_id}'")

    def get_latest_frame(self) -> Optional[VideoFrame]:
        """Return the most recently captured video frame (thread-safe)."""
        with self._lock:
            return self._latest_frame

    def get_stats(self) -> StreamWorkerStats:
        """Return current performance and telemetry metrics."""
        with self._lock:
            uptime = time.time() - self._start_time if self._start_time else 0.0
            return StreamWorkerStats(
                camera_id=self.camera_id,
                external_camera_id=self.external_camera_id,
                rtsp_url=self.rtsp_url,
                state=self._state,
                measured_fps=round(self._measured_fps, 2),
                target_fps=self.target_fps,
                total_frames_read=self._total_frames_read,
                dropped_frames=self._dropped_frames,
                reconnect_attempts=self._reconnect_attempts,
                uptime_seconds=round(uptime, 2),
                last_frame_time=self._last_frame_time,
                last_error=self._last_error,
                transport_protocol="TCP",
            )

    def _run_ingestion_loop(self):
        """Main loop: chooses between synthetic generator and real RTSP/TCP connection."""
        if self.use_synthetic_stream:
            self._run_synthetic_stream()
        else:
            self._run_rtsp_stream()

    def _run_synthetic_stream(self):
        """Generates realistic synthetic video frames for tests and headless CI."""
        with self._lock:
            self._state = StreamWorkerState.STREAMING

        frame_idx = 0
        frame_interval = 1.0 / max(self.target_fps, 1.0)
        width, height = 1920, 1080

        while not self._stop_event.is_set():
            loop_start = time.perf_counter()
            now_utc = datetime.now(timezone.utc)

            # Create synthetic frame with dynamic background and watermark
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = (20, 25, 40)  # Dark tactical slate background

            # Draw camera ID, frame number, and timestamp watermark
            cv2.putText(
                frame,
                f"SENTINELX SURVEILLANCE FEED: {self.external_camera_id}",
                (50, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 220, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | FRAME: {frame_idx:06d}",
                (50, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (200, 200, 200),
                2,
                cv2.LINE_AA,
            )

            # Draw a simulated moving vehicle box across the frame
            x_pos = int((frame_idx * 15) % (width - 250))
            y_pos = int(500 + 50 * np.sin(frame_idx * 0.05))
            cv2.rectangle(frame, (x_pos, y_pos), (x_pos + 200, y_pos + 120), (0, 255, 100), 3)
            cv2.putText(
                frame,
                "TEST VEHICLE [GJ01AB1234]",
                (x_pos, y_pos - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 100),
                2,
            )

            video_frame = VideoFrame(
                camera_id=self.camera_id,
                frame_index=frame_idx,
                timestamp_utc=now_utc,
                image=frame,
                width=width,
                height=height,
                fps=self.target_fps,
                is_keyframe=(frame_idx % 30 == 0),
            )

            with self._lock:
                self._latest_frame = video_frame
                self._total_frames_read += 1
                self._last_frame_time = now_utc
                self._record_frame_arrival(time.time())

            if self.frame_callback:
                try:
                    self.frame_callback(video_frame)
                except Exception as e:
                    logger.error(f"Error in frame callback for {self.external_camera_id}: {e}")

            frame_idx += 1

            # Sleep remaining time to maintain target FPS
            elapsed = time.perf_counter() - loop_start
            sleep_time = max(0.0, frame_interval - elapsed)
            time.sleep(sleep_time)

    def _run_rtsp_stream(self):
        """Connects to real IP camera or VMS over RTSP/TCP and reads frames."""
        while not self._stop_event.is_set():
            with self._lock:
                self._state = StreamWorkerState.CONNECTING
                self._reconnect_attempts += 1

            logger.info(
                f"Connecting to RTSP/TCP stream for camera '{self.external_camera_id}' (Attempt #{self._reconnect_attempts})"
            )

            # Open VideoCapture with TCP transport
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Drop stale frames to prevent queue lag

            if not cap.isOpened():
                err_msg = f"Failed to open RTSP stream at {self.rtsp_url}"
                logger.warning(f"{err_msg} for camera {self.external_camera_id}")
                with self._lock:
                    self._state = StreamWorkerState.ERROR
                    self._last_error = err_msg

                # Exponential backoff retry sleep
                time.sleep(min(30.0, 1.0 * (1.5 ** min(self._reconnect_attempts, 6))))
                continue

            with self._lock:
                self._state = StreamWorkerState.STREAMING
                self._last_error = None

            frame_idx = 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)
            fps = float(cap.get(cv2.CAP_PROP_FPS) or self.target_fps)

            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning(
                        f"RTSP stream disconnected for camera '{self.external_camera_id}'"
                    )
                    break

                now_utc = datetime.now(timezone.utc)
                video_frame = VideoFrame(
                    camera_id=self.camera_id,
                    frame_index=frame_idx,
                    timestamp_utc=now_utc,
                    image=frame,
                    width=width,
                    height=height,
                    fps=fps,
                    is_keyframe=(frame_idx % 30 == 0),
                )

                with self._lock:
                    self._latest_frame = video_frame
                    self._total_frames_read += 1
                    self._last_frame_time = now_utc
                    self._record_frame_arrival(time.time())

                if self.frame_callback:
                    try:
                        self.frame_callback(video_frame)
                    except Exception as e:
                        logger.error(f"Error in frame callback for {self.external_camera_id}: {e}")

                frame_idx += 1

            cap.release()

            if not self._stop_event.is_set():
                with self._lock:
                    self._state = StreamWorkerState.RECONNECTING
                time.sleep(2.0)

    def _record_frame_arrival(self, arrival_time: float):
        """Record timestamp to calculate sliding window measured FPS."""
        self._frame_timestamps.append(arrival_time)
        if len(self._frame_timestamps) >= 2:
            duration = self._frame_timestamps[-1] - self._frame_timestamps[0]
            if duration > 0:
                self._measured_fps = (len(self._frame_timestamps) - 1) / duration


class StreamWorkerPool:
    """Manages pool of active RTSP stream workers across all registered cameras."""

    def __init__(self):
        self._workers: Dict[str, RTSPStreamWorker] = {}
        self._lock = threading.Lock()

    def start_worker(
        self,
        camera_id: str,
        external_camera_id: str,
        rtsp_url: str,
        target_fps: float = 25.0,
        use_synthetic_stream: bool = False,
        frame_callback: Optional[Callable[[VideoFrame], None]] = None,
    ) -> RTSPStreamWorker:
        """Spawn and start a worker for a camera feed."""
        with self._lock:
            # If already exists and running, return it
            if camera_id in self._workers:
                worker = self._workers[camera_id]
                if worker.state not in (StreamWorkerState.STOPPED, StreamWorkerState.ERROR):
                    return worker
                worker.stop()

            worker = RTSPStreamWorker(
                camera_id=camera_id,
                external_camera_id=external_camera_id,
                rtsp_url=rtsp_url,
                target_fps=target_fps,
                use_synthetic_stream=use_synthetic_stream,
                frame_callback=frame_callback,
            )
            worker.start()
            self._workers[camera_id] = worker
            return worker

    def stop_worker(self, camera_id: str):
        """Stop worker for a specific camera."""
        with self._lock:
            if camera_id in self._workers:
                worker = self._workers.pop(camera_id)
                worker.stop()

    def get_worker(self, camera_id: str) -> Optional[RTSPStreamWorker]:
        """Retrieve active worker by camera ID."""
        with self._lock:
            return self._workers.get(camera_id)

    def get_latest_frame(self, camera_id: str) -> Optional[VideoFrame]:
        """Retrieve latest decoded frame for a camera."""
        worker = self.get_worker(camera_id)
        return worker.get_latest_frame() if worker else None

    def get_pool_status(self) -> StreamPoolStatus:
        """Get aggregate telemetry across all camera workers in the pool."""
        with self._lock:
            worker_list = list(self._workers.values())

        stats_list = [w.get_stats() for w in worker_list]
        streaming_count = sum(1 for s in stats_list if s.state == StreamWorkerState.STREAMING)
        reconnecting_count = sum(
            1
            for s in stats_list
            if s.state in (StreamWorkerState.CONNECTING, StreamWorkerState.RECONNECTING)
        )
        error_count = sum(1 for s in stats_list if s.state == StreamWorkerState.ERROR)
        total_fps = sum(s.measured_fps for s in stats_list)

        return StreamPoolStatus(
            total_registered=len(stats_list),
            total_active_workers=len(stats_list),
            streaming_count=streaming_count,
            reconnecting_count=reconnecting_count,
            error_count=error_count,
            total_aggregate_fps=round(total_fps, 2),
            workers=stats_list,
        )

    def stop_all(self):
        """Stop all workers in the pool."""
        with self._lock:
            workers = list(self._workers.values())
            self._workers.clear()

        for w in workers:
            w.stop()
        logger.info(f"Stopped all {len(workers)} camera stream workers in the pool.")


# Global Singleton Worker Pool
stream_pool = StreamWorkerPool()
