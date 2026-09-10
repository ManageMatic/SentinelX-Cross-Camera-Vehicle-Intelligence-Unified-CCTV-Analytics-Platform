"""Real-time WebSocket Alert Dispatcher & Notification Hub Service (Module 19).

Broadcasts instant audio-visual Red Alerts and live telemetry to connected Police Command
Center dashboards in < 500ms with topic/channel routing and backlog replay.
"""

import asyncio
import json
import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

from app.schemas.websocket import (
    AlertBroadcastPayload,
    WebSocketHubStats,
    WebSocketMessageType,
)

logger = logging.getLogger("sentinelx.alerts_hub")


class AlertDispatcherHub:
    """Central Real-time WebSocket Alert Broadcast & Subscription Manager."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # Mapping from WebSocket to set of subscribed channel strings
        self._active_connections: Dict[WebSocket, Set[str]] = {}

        # Recent alert ring buffer for instant backlog replay on client reconnect
        self._max_backlog = 50
        self._alert_backlog: deque[AlertBroadcastPayload] = deque(maxlen=self._max_backlog)

        # Performance & Telemetry metrics
        self._total_broadcasts: int = 0
        self._total_alerts_dispatched: int = 0
        self._latency_samples: deque[float] = deque(maxlen=200)

    async def register(
        self, websocket: WebSocket, initial_channels: Optional[List[str]] = None
    ) -> None:
        """Accept WebSocket connection, register subscribed channels, and replay recent alert backlog."""
        await websocket.accept()
        channels = set(initial_channels or ["all"])

        with self._lock:
            self._active_connections[websocket] = channels

        logger.info(f"WebSocket client connected. Active clients: {len(self._active_connections)}")

        # Replay recent alert backlog to new connection
        backlog_items = list(self._alert_backlog)
        if backlog_items:
            backlog_msg = {
                "type": WebSocketMessageType.BACKLOG_SYNC.value,
                "data": [item.model_dump(mode="json") for item in backlog_items],
                "count": len(backlog_items),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            try:
                await websocket.send_text(json.dumps(backlog_msg))
            except Exception as e:
                logger.warning(f"Failed to replay backlog to new WebSocket: {e}")

    def unregister(self, websocket: WebSocket) -> None:
        """Remove disconnected WebSocket from connection registry."""
        with self._lock:
            if websocket in self._active_connections:
                del self._active_connections[websocket]
        logger.info(
            f"WebSocket client disconnected. Active clients: {len(self._active_connections)}"
        )

    def subscribe(self, websocket: WebSocket, channels: List[str]) -> None:
        """Update subscribed channels for a connected client."""
        with self._lock:
            if websocket in self._active_connections:
                self._active_connections[websocket].update(channels)

    async def broadcast_alert(self, alert_payload: AlertBroadcastPayload) -> None:
        """Broadcast prioritized hotlist alert to all relevant connected subscribers in < 500ms."""
        start_t = time.perf_counter()
        now_utc = datetime.now(timezone.utc)

        # Append to in-memory backlog
        with self._lock:
            self._alert_backlog.append(alert_payload)
            self._total_alerts_dispatched += 1
            connections_snapshot = dict(self._active_connections)

        msg_text = json.dumps(
            {
                "type": WebSocketMessageType.ALERT_BROADCAST.value,
                "data": alert_payload.model_dump(mode="json"),
                "timestamp": now_utc.isoformat(),
            }
        )

        dead_connections: List[WebSocket] = []

        # Route to subscribers matching channels: "all", "priority:{PRIORITY}", "category:{CATEGORY}", "camera:{CAMERA_ID}"
        target_keys = {
            "all",
            f"priority:{alert_payload.priority.upper()}",
            f"category:{alert_payload.category.upper()}",
            f"camera:{alert_payload.camera_id}",
        }

        tasks = []
        for ws, client_channels in connections_snapshot.items():
            if client_channels.intersection(target_keys):
                tasks.append(self._safe_send(ws, msg_text, dead_connections))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Cleanup dead connections
        for dead_ws in dead_connections:
            self.unregister(dead_ws)

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        with self._lock:
            self._total_broadcasts += 1
            self._latency_samples.append(elapsed_ms)

        logger.debug(
            f"Dispatched alert {alert_payload.alert_id} ({alert_payload.priority}) "
            f"to {len(tasks)} clients in {elapsed_ms:.2f}ms"
        )

    async def _safe_send(
        self, websocket: WebSocket, message: str, dead_list: List[WebSocket]
    ) -> None:
        """Send message safely and record dead socket on failure."""
        try:
            await websocket.send_text(message)
        except Exception:
            dead_list.append(websocket)

    async def broadcast_system_telemetry(self, telemetry_data: Dict[str, Any]) -> None:
        """Broadcast real-time system metrics to subscribers on 'system:telemetry' channel."""
        with self._lock:
            connections_snapshot = dict(self._active_connections)

        msg_text = json.dumps(
            {
                "type": WebSocketMessageType.TELEMETRY_UPDATE.value,
                "data": telemetry_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        dead_connections: List[WebSocket] = []
        tasks = []

        for ws, client_channels in connections_snapshot.items():
            if "system:telemetry" in client_channels or "all" in client_channels:
                tasks.append(self._safe_send(ws, msg_text, dead_connections))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        for dead_ws in dead_connections:
            self.unregister(dead_ws)

    def get_backlog(self) -> List[AlertBroadcastPayload]:
        """Retrieve current in-memory alert backlog."""
        with self._lock:
            return list(self._alert_backlog)

    def get_stats(self) -> WebSocketHubStats:
        """Retrieve real-time WebSocket connection and broadcast telemetry."""
        with self._lock:
            avg_lat = (
                sum(self._latency_samples) / len(self._latency_samples)
                if self._latency_samples
                else 0.0
            )

            # Channel subscription counts
            channel_counts: Dict[str, int] = {}
            for channels in self._active_connections.values():
                for ch in channels:
                    channel_counts[ch] = channel_counts.get(ch, 0) + 1

            return WebSocketHubStats(
                connected_clients=len(self._active_connections),
                total_messages_broadcast=self._total_broadcasts,
                total_alerts_dispatched=self._total_alerts_dispatched,
                backlog_size=len(self._alert_backlog),
                average_broadcast_latency_ms=round(avg_lat, 2),
                channel_counts=channel_counts,
            )


# Global singleton instance
alert_dispatcher = AlertDispatcherHub()
