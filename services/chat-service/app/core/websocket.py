from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections grouped by room id."""

    def __init__(self):
        # room_id -> list of WebSocket
        self.active_connections: Dict[str, list] = {}

    async def connect(self, websocket: WebSocket, room_id: str) -> None:
        connections = self.active_connections.setdefault(room_id, [])
        connections.append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str) -> None:
        connections = self.active_connections.get(room_id)
        if not connections:
            return
        try:
            connections.remove(websocket)
        except ValueError:
            pass
        if len(connections) == 0:
            # cleanup empty room
            self.active_connections.pop(room_id, None)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    async def broadcast(self, message: str, room_id: str) -> None:
        connections = self.active_connections.get(room_id, set())
        for connection in set(connections):
            try:
                await connection.send_text(message)
            except Exception:
                # ignore failures; client will be cleaned up on disconnect
                pass


manager = ConnectionManager()


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """A WebSocket-only endpoint for joining a room and broadcasting messages.

    Example:
      ws://localhost:8012/ws/general
    """
    # Accept only WebSocket connections; normal HTTP requests will get 405
    await websocket.accept()
    await manager.connect(websocket, room_id)
    try:
        await manager.send_personal_message(f"Connected to room: {room_id}", websocket)
        while True:
            data = await websocket.receive_text()
            # Simple protocol: client sends plain text messages
            await manager.broadcast(data, room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    except Exception:
        # on unexpected errors, ensure disconnect
        manager.disconnect(websocket, room_id)
        try:
            await websocket.close()
        except Exception:
            pass
