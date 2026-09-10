"""Real-time WebSocket Alert Dispatcher & Notification Hub Endpoints (Module 19)."""

import json
import logging
from typing import List, Optional

from app.schemas.common import APIResponse
from app.schemas.websocket import (
    AlertBroadcastPayload,
    WebSocketHubStats,
    WebSocketMessageType,
)
from app.services.alert_dispatcher import alert_dispatcher
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

logger = logging.getLogger("sentinelx.alerts_api")

router = APIRouter(prefix="/alerts", tags=["Real-time WebSocket Alert Dispatcher"])


@router.websocket("/ws")
async def websocket_alerts_endpoint(
    websocket: WebSocket,
    channels: Optional[str] = Query(
        None, description="Comma-separated channels (e.g. 'all,priority:CRITICAL')"
    ),
) -> None:
    """Real-time bidirectional WebSocket endpoint pushing instant Red Alerts to command center dashboards."""
    initial_channels = [c.strip() for c in channels.split(",")] if channels else ["all"]
    await alert_dispatcher.register(websocket, initial_channels)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg_json = json.loads(data)
                action = msg_json.get("action", "").upper()

                if action == "SUBSCRIBE":
                    new_channels = msg_json.get("channels", [])
                    if new_channels:
                        alert_dispatcher.subscribe(websocket, new_channels)
                        ack_msg = {
                            "type": WebSocketMessageType.CLIENT_SUBSCRIBE.value,
                            "status": "SUCCESS",
                            "subscribed_channels": new_channels,
                        }
                        await websocket.send_text(json.dumps(ack_msg))

                elif action == "PING":
                    pong_msg = {
                        "type": WebSocketMessageType.HEARTBEAT_PONG.value,
                        "timestamp": msg_json.get("timestamp"),
                    }
                    await websocket.send_text(json.dumps(pong_msg))

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        alert_dispatcher.unregister(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        alert_dispatcher.unregister(websocket)


@router.post("/broadcast", response_model=APIResponse[AlertBroadcastPayload])
async def broadcast_alert_manual(
    payload: AlertBroadcastPayload,
) -> APIResponse[AlertBroadcastPayload]:
    """Manually dispatch a prioritized Red Alert across all connected WebSocket client dashboards."""
    await alert_dispatcher.broadcast_alert(payload)
    return APIResponse(data=payload, message="Alert successfully broadcasted over WebSockets")


@router.get("/backlog", response_model=APIResponse[List[AlertBroadcastPayload]])
async def get_alert_backlog() -> APIResponse[List[AlertBroadcastPayload]]:
    """Retrieve the in-memory recent alert ring buffer for dashboard initialization."""
    backlog = alert_dispatcher.get_backlog()
    return APIResponse(data=backlog, message=f"Retrieved {len(backlog)} backlog alerts")


@router.get("/ws-stats", response_model=APIResponse[WebSocketHubStats])
async def get_websocket_hub_stats() -> APIResponse[WebSocketHubStats]:
    """Retrieve real-time WebSocket connection count, broadcast counts, and channel subscriptions."""
    stats = alert_dispatcher.get_stats()
    return APIResponse(data=stats, message="WebSocket hub statistics retrieved")
