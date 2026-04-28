from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio


class ConnectionManager:
    """Manage WebSocket connections for real-time alerts."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

    async def broadcast_to_user(self, user_id: str, message: dict):
        """Send message to all connections for a user."""
        if user_id in self.active_connections:
            for ws in list(self.active_connections[user_id]):
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(user_id, ws)

    async def broadcast_to_org(self, org_id: str, message: dict):
        """Send message to all users in an organization."""
        if org_id in self.active_connections:
            for ws in list(self.active_connections[org_id]):
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(org_id, ws)


manager = ConnectionManager()

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/alerts/{user_id}")
async def websocket_alerts(websocket: WebSocket, user_id: str):
    """Real-time alert stream for a user."""
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                try:
                    payload = json.loads(data)
                    await websocket.send_json({"type": "ack", "message_id": payload.get("id")})
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)


@router.websocket("/ws/org/{org_id}")
async def websocket_org_alerts(websocket: WebSocket, org_id: str):
    """Real-time alert stream for an organization."""
    await manager.connect(org_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(org_id, websocket)