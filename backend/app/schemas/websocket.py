"""Pydantic schemas for Real-time WebSocket Alert Dispatcher & Notification Hub (Module 19)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class WebSocketMessageType(str, Enum):
    """Types of messages transmitted over SentinelX WebSockets."""

    ALERT_BROADCAST = "ALERT_BROADCAST"
    HEARTBEAT_PING = "HEARTBEAT_PING"
    HEARTBEAT_PONG = "HEARTBEAT_PONG"
    CLIENT_SUBSCRIBE = "CLIENT_SUBSCRIBE"
    BACKLOG_SYNC = "BACKLOG_SYNC"
    TELEMETRY_UPDATE = "TELEMETRY_UPDATE"


class AlertBroadcastPayload(BaseModel):
    """Real-time hotlist hit alert dispatched to connected control rooms in < 500ms."""

    alert_id: str
    registration_number: str
    category: str
    priority: str
    camera_id: str
    camera_name: str
    location_name: str
    latitude: float
    longitude: float
    snapshot_path: Optional[str] = None
    alert_time: datetime
    audio_alert: bool = True
    visual_color: str = "#ef4444"  # Default critical red
    message: str
    dispatch_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebSocketClientMessage(BaseModel):
    """Inbound message from a connected client dashboard."""

    action: str = Field("SUBSCRIBE", description="SUBSCRIBE, PING, ACK")
    channels: Optional[List[str]] = Field(default_factory=lambda: ["all"])


class WebSocketHubStats(BaseModel):
    """Real-time throughput and connection telemetry for WebSocket dispatcher."""

    connected_clients: int
    total_messages_broadcast: int
    total_alerts_dispatched: int
    backlog_size: int
    average_broadcast_latency_ms: float
    channel_counts: Dict[str, int]
