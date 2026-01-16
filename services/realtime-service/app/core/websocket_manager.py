from typing import Dict
from fastapi import WebSocket
import json


class WebSocketManager:
    """Manage WebSocket connections for drivers and passengers."""
    
    def __init__(self):
        self.driver_connections: Dict[str, WebSocket] = {}
        self.passenger_connections: Dict[str, WebSocket] = {}
    
    async def connect_driver(self, driver_id: str, websocket: WebSocket):
        """Connect a driver WebSocket."""
        await websocket.accept()
        self.driver_connections[driver_id] = websocket
    
    async def connect_passenger(self, passenger_id: str, websocket: WebSocket):
        """Connect a passenger WebSocket."""
        await websocket.accept()
        self.passenger_connections[passenger_id] = websocket
    
    def disconnect_driver(self, driver_id: str):
        """Disconnect a driver."""
        self.driver_connections.pop(driver_id, None)
    
    def disconnect_passenger(self, passenger_id: str):
        """Disconnect a passenger."""
        self.passenger_connections.pop(passenger_id, None)
    
    async def send_to_driver(self, driver_id: str, payload: dict):
        """Send message to a specific driver."""
        ws = self.driver_connections.get(driver_id)
        if ws:
            try:
                await ws.send_json(payload)
                return True
            except Exception as e:
                print(f"⚠️ Failed to send to driver {driver_id}: {e}")
                return False
        return False
    
    async def send_to_passenger(self, passenger_id: str, payload: dict):
        """Send message to a specific passenger."""
        ws = self.passenger_connections.get(passenger_id)
        if ws:
            try:
                await ws.send_json(payload)
                return True
            except Exception as e:
                print(f"⚠️ Failed to send to passenger {passenger_id}: {e}")
                return False
        return False
    
    async def broadcast_to_drivers(self, payload: dict, exclude_driver_id: str = None):
        """Broadcast message to all connected drivers, optionally excluding one."""
        disconnected = []
        for driver_id, ws in list(self.driver_connections.items()):
            if exclude_driver_id and driver_id == exclude_driver_id:
                continue
            try:
                await ws.send_json(payload)
            except Exception as e:
                print(f"⚠️ Failed to send to driver {driver_id}: {e}")
                disconnected.append(driver_id)
        
        # Clean up disconnected drivers
        for driver_id in disconnected:
            self.driver_connections.pop(driver_id, None)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
