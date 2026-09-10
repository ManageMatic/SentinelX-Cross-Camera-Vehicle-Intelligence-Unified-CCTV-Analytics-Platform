"""Master API Router for v1 endpoints."""

from app.api.v1 import (
    anpr,
    buffers,
    cameras,
    detection,
    health,
    proxy,
    streams,
    system,
    tracking,
)
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["System"])
api_router.include_router(system.router, prefix="/system", tags=["System Telemetry"])
api_router.include_router(cameras.router, prefix="", tags=["Camera Registry & Ingestion"])
api_router.include_router(streams.router, prefix="", tags=["Live Video Ingestion & Telemetry"])
api_router.include_router(proxy.router, prefix="", tags=["WebRTC & HLS Stream Proxy"])
api_router.include_router(buffers.router, prefix="", tags=["Frame Buffers & Backpressure"])
api_router.include_router(detection.router, prefix="", tags=["AI Vehicle Detection"])
api_router.include_router(tracking.router, prefix="", tags=["Multi-Object Tracking (ByteTrack)"])
api_router.include_router(anpr.router, prefix="", tags=["ANPR & Plate Recognition"])
