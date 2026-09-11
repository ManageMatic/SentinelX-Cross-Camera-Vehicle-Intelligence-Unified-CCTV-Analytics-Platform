"""Sentinel CCTV RTSP Client and Diagnostics Engine.

Responsible for authenticated RTSP stream connections over TCP, metadata probing,
frame grabbing, connectivity testing, exponential backoff, and secret masking.
"""

import asyncio
import os
import time
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.sentinel.rtsp import (
    build_public_rtsp_path,
    build_rtsp_url,
    redact_url,
    validate_camera_id,
)

logger = get_logger(__name__)


class SentinelClient:
    """High-res, authenticated RTSP client for Gujarat Police Sentinel CCTV streams."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        access_code: Optional[str] = None,
    ):
        self.settings = get_settings()
        self.host = host or self.settings.SENTINEL_RTSP_HOST
        self.port = port or self.settings.SENTINEL_RTSP_PORT
        self.username = username or self.settings.effective_sentinel_username
        self.access_code = access_code or self.settings.SENTINEL_ACCESS_CODE

    def get_rtsp_url(self, camera_id: str) -> str:
        """Construct raw authenticated RTSP URL for internal worker usage."""
        return build_rtsp_url(
            camera_id=camera_id,
            host=self.host,
            port=self.port,
            username=self.username,
            access_code=self.access_code,
        )

    def get_sanitized_path(self, camera_id: str) -> str:
        """Construct sanitized path for public exposure: /stream/cam01."""
        return build_public_rtsp_path(camera_id)

    @staticmethod
    def calculate_reconnect_delay(attempt: int, max_delay: float = 30.0) -> float:
        """Compute exponential reconnect delay: 1s, 2s, 4s, 8s, 16s, max 30s."""
        if attempt <= 0:
            return 1.0
        delay = 1.0 * (2 ** min(attempt, 5))
        return min(delay, max_delay)

    def _configure_tcp_transport(self) -> None:
        """Enforce RTSP over TCP for reliable frame transit through firewalls."""
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    def _probe_sync(self, camera_id: str, timeout_seconds: float = 6.0) -> Dict[str, Any]:
        """Synchronously probe RTSP stream via OpenCV with strict TCP transport."""
        valid_id = validate_camera_id(camera_id)
        raw_url = self.get_rtsp_url(valid_id)
        redacted = redact_url(raw_url)

        self._configure_tcp_transport()
        logger.info(f"Testing Sentinel RTSP connectivity for {valid_id} at {redacted}")

        cap = None
        start_time = time.time()
        try:
            cap = cv2.VideoCapture(raw_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                return {
                    "camera_id": valid_id,
                    "reachable": False,
                    "first_frame_received": False,
                    "codec": "unknown",
                    "width": 0,
                    "height": 0,
                    "fps": 0.0,
                    "latency_ms": round((time.time() - start_time) * 1000, 1),
                    "message": f"Unable to open RTSP stream at {redacted}. Check credentials and network connectivity.",
                }

            # Attempt to read first frame
            ret, frame = cap.read()
            latency_ms = round((time.time() - start_time) * 1000, 1)

            if not ret or frame is None or frame.size == 0:
                return {
                    "camera_id": valid_id,
                    "reachable": True,
                    "first_frame_received": False,
                    "codec": "h264",
                    "width": 0,
                    "height": 0,
                    "fps": 0.0,
                    "latency_ms": latency_ms,
                    "message": "Connected to RTSP endpoint but no valid video frame received.",
                }

            height, width = frame.shape[:2]
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            if fps <= 0 or fps > 120:
                fps = 25.0

            return {
                "camera_id": valid_id,
                "reachable": True,
                "first_frame_received": True,
                "codec": "h264",
                "width": int(width),
                "height": int(height),
                "fps": float(fps),
                "latency_ms": latency_ms,
                "message": "Camera connection and frame grab successful.",
            }
        except Exception as e:
            err_msg = redact_url(str(e))
            logger.error(f"Error testing camera {valid_id}: {err_msg}")
            return {
                "camera_id": valid_id,
                "reachable": False,
                "first_frame_received": False,
                "codec": "unknown",
                "width": 0,
                "height": 0,
                "fps": 0.0,
                "latency_ms": round((time.time() - start_time) * 1000, 1),
                "message": f"Connection error: {err_msg}",
            }
        finally:
            if cap is not None:
                cap.release()

    async def test_camera(self, camera_id: str, timeout_seconds: float = 6.0) -> Dict[str, Any]:
        """Asynchronously test connectivity and first frame grab for a camera."""
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._probe_sync, camera_id, timeout_seconds),
                timeout=timeout_seconds + 1.0,
            )
        except asyncio.TimeoutError:
            valid_id = validate_camera_id(camera_id)
            return {
                "camera_id": valid_id,
                "reachable": False,
                "first_frame_received": False,
                "codec": "unknown",
                "width": 0,
                "height": 0,
                "fps": 0.0,
                "latency_ms": round((timeout_seconds * 1000), 1),
                "message": f"Connection timed out after {timeout_seconds}s.",
            }

    def _grab_snapshot_sync(self, camera_id: str) -> Optional[bytes]:
        """Synchronously grab a single frame and encode as JPEG."""
        valid_id = validate_camera_id(camera_id)
        raw_url = self.get_rtsp_url(valid_id)
        self._configure_tcp_transport()

        cap = None
        try:
            cap = cv2.VideoCapture(raw_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not cap.isOpened():
                return None
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                return None

            success, encoded_jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if success:
                return encoded_jpg.tobytes()
            return None
        except Exception as e:
            logger.warning(f"Failed to grab snapshot for {valid_id}: {redact_url(str(e))}")
            return None
        finally:
            if cap is not None:
                cap.release()

    async def fetch_snapshot(self, camera_id: str) -> Optional[bytes]:
        """Asynchronously grab a snapshot JPEG."""
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._grab_snapshot_sync, camera_id),
                timeout=5.0,
            )
        except Exception:
            return None


# Global singleton client
sentinel_client = SentinelClient()
