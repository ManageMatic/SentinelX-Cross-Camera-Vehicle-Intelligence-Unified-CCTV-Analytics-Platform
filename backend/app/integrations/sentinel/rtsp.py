"""RTSP URL Builder, Camera ID Validator, and Secret Redaction Engine for Sentinel CCTV.

Handles secure authenticated RTSP URL construction using URL-encoded credentials,
strict camera identifier validation (SSRF prevention), and universal secret redaction.
"""

import re
import urllib.parse
from typing import Optional

from app.core.config import get_settings
from app.core.exceptions import ValidationException

CAMERA_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
URL_CREDENTIAL_PATTERN = re.compile(r"://([^:@]+):([^@]+)@")


def validate_camera_id(camera_id: str) -> str:
    """Validate camera ID format to prevent SSRF, path traversal, or injection.

    Accepts: 'cam01', 'cam02', 'cam30', 'CAM-01', 'ahmedabad_cctv_01', etc.
    Rejects: URLs, IPs, special characters, path traversal ('../'), whitespace.
    """
    if not camera_id or not isinstance(camera_id, str):
        raise ValidationException("camera_id must be a non-empty string.")

    cleaned_id = camera_id.strip()
    if not CAMERA_ID_PATTERN.match(cleaned_id):
        raise ValidationException(
            f"Invalid camera ID '{camera_id}'. Must be 1-64 alphanumeric characters, hyphens, or underscores."
        )

    # Explicit protection against URL scheme injection
    lower = cleaned_id.lower()
    if any(forbidden in lower for forbidden in [":", "/", "\\", "@", "?", "#", "http", "rtsp"]):
        raise ValidationException(f"Invalid characters in camera ID '{camera_id}'.")

    return cleaned_id


def build_public_rtsp_path(camera_id: str) -> str:
    """Construct sanitized RTSP relative path for database storage and client display."""
    valid_id = validate_camera_id(camera_id)
    return f"/stream/{valid_id}"


def build_rtsp_url(
    camera_id: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    access_code: Optional[str] = None,
) -> str:
    """Construct a full authenticated RTSP URL with URL-encoded credentials.

    Example output:
    rtsp://user%40domain.com:secret%23123@103.250.160.189:8554/stream/cam01

    WARNING: NEVER return the output of this function to the frontend or log it raw.
    """
    valid_id = validate_camera_id(camera_id)
    settings = get_settings()

    rtsp_host = host or settings.SENTINEL_RTSP_HOST or settings.SENTINEL_DIRECT_IP
    rtsp_port = port or settings.SENTINEL_RTSP_PORT or 8554

    user = username if username is not None else settings.effective_sentinel_username
    code = access_code if access_code is not None else settings.SENTINEL_ACCESS_CODE

    if user and code:
        # Quote credentials to safely handle '@', ':', '%', etc. in email or password
        encoded_user = urllib.parse.quote(str(user), safe="")
        encoded_code = urllib.parse.quote(str(code), safe="")
        return f"rtsp://{encoded_user}:{encoded_code}@{rtsp_host}:{rtsp_port}/stream/{valid_id}"

    return f"rtsp://{rtsp_host}:{rtsp_port}/stream/{valid_id}"


def redact_url(url: Optional[str]) -> str:
    """Universally redact passwords, tokens, and access codes from any URL.

    Example:
    'rtsp://user:secret123@103.250.160.189:8554/stream/cam01' ->
    'rtsp://***:***@103.250.160.189:8554/stream/cam01'
    """
    if not url:
        return ""

    if not isinstance(url, str):
        url = str(url)

    # Fast regex redaction for standard URLs with credentials
    return URL_CREDENTIAL_PATTERN.sub(r"://***:***@", url)
