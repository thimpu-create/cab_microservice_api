from typing import Dict, Optional
from fastapi import WebSocket
import json
import time
import asyncio


class WebSocketManager:
    """Manage WebSocket connections for drivers and passengers with health checks."""
    
    def __init__(self):
        self.driver_connections: Dict[str, WebSocket] = {}
        self.passenger_connections: Dict[str, WebSocket] = {}
        self.driver_last_ping: Dict[str, float] = {}
        self.passenger_last_ping: Dict[str, float] = {}
        self.connection_timeout = 300  # 5 minutes
    
    async def connect_driver(self, driver_id: str, websocket: WebSocket):
        """Connect a driver WebSocket."""
        # Disconnect existing connection if any
        if driver_id in self.driver_connections:
            try:
                old_ws = self.driver_connections[driver_id]
                await old_ws.close()
            except:
                pass
        
        await websocket.accept()
        self.driver_connections[driver_id] = websocket
        self.driver_last_ping[driver_id] = time.time()
    
    async def connect_passenger(self, passenger_id: str, websocket: WebSocket):
        """Connect a passenger WebSocket."""
        # Disconnect existing connection if any
        if passenger_id in self.passenger_connections:
            try:
                old_ws = self.passenger_connections[passenger_id]
                await old_ws.close()
            except:
                pass
        
        await websocket.accept()
        self.passenger_connections[passenger_id] = websocket
        self.passenger_last_ping[passenger_id] = time.time()
    
    def disconnect_driver(self, driver_id: str):
        """Disconnect a driver."""
        self.driver_connections.pop(driver_id, None)
        self.driver_last_ping.pop(driver_id, None)
    
    def disconnect_passenger(self, passenger_id: str):
        """Disconnect a passenger."""
        self.passenger_connections.pop(passenger_id, None)
        self.passenger_last_ping.pop(passenger_id, None)
    
    def update_driver_ping(self, driver_id: str):
        """Update last ping time for driver."""
        if driver_id in self.driver_connections:
            self.driver_last_ping[driver_id] = time.time()
    
    def update_passenger_ping(self, passenger_id: str):
        """Update last ping time for passenger."""
        if passenger_id in self.passenger_connections:
            self.passenger_last_ping[passenger_id] = time.time()
    
    def is_connection_alive(self, websocket: WebSocket) -> bool:
        """Check if WebSocket connection is still alive."""
        try:
            # Check connection state
            return websocket.client_state.name == "CONNECTED"
        except:
            return False
    
    async def send_to_driver(self, driver_id: str, payload: dict) -> bool:
        """Send message to a specific driver with error handling."""
        ws = self.driver_connections.get(driver_id)
        if not ws:
            return False
        
        # Check if connection is alive
        if not self.is_connection_alive(ws):
            print(f"⚠️ Driver {driver_id} connection is dead, removing")
            self.disconnect_driver(driver_id)
            return False
        
        try:
            await ws.send_json(payload)
            return True
        except Exception as e:
            print(f"⚠️ Failed to send to driver {driver_id}: {e}")
            self.disconnect_driver(driver_id)
            return False
    
    async def send_to_passenger(self, passenger_id: str, payload: dict) -> bool:
        """Send message to a specific passenger with error handling."""
        ws = self.passenger_connections.get(passenger_id)
        if not ws:
            return False
        
        # Check if connection is alive
        if not self.is_connection_alive(ws):
            print(f"⚠️ Passenger {passenger_id} connection is dead, removing")
            self.disconnect_passenger(passenger_id)
            return False
        
        try:
            await ws.send_json(payload)
            return True
        except Exception as e:
            print(f"⚠️ Failed to send to passenger {passenger_id}: {e}")
            self.disconnect_passenger(passenger_id)
            return False
    
    async def broadcast_to_drivers(self, payload: dict, exclude_driver_id: str = None):
        """Broadcast message to all connected drivers, optionally excluding one."""
        disconnected = []
        for driver_id, ws in list(self.driver_connections.items()):
            if exclude_driver_id and driver_id == exclude_driver_id:
                continue
            
            if not self.is_connection_alive(ws):
                disconnected.append(driver_id)
                continue
            
            try:
                await ws.send_json(payload)
            except Exception as e:
                print(f"⚠️ Failed to send to driver {driver_id}: {e}")
                disconnected.append(driver_id)
        
        # Clean up disconnected drivers
        for driver_id in disconnected:
            self.disconnect_driver(driver_id)
    
    async def cleanup_stale_connections(self):
        """Periodically cleanup stale connections."""
        current_time = time.time()
        
        # Check driver connections
        stale_drivers = []
        for driver_id, last_ping in list(self.driver_last_ping.items()):
            if current_time - last_ping > self.connection_timeout:
                stale_drivers.append(driver_id)
        
        for driver_id in stale_drivers:
            print(f"🧹 Cleaning up stale driver connection: {driver_id}")
            self.disconnect_driver(driver_id)
        
        # Check passenger connections
        stale_passengers = []
        for passenger_id, last_ping in list(self.passenger_last_ping.items()):
            if current_time - last_ping > self.connection_timeout:
                stale_passengers.append(passenger_id)
        
        for passenger_id in stale_passengers:
            print(f"🧹 Cleaning up stale passenger connection: {passenger_id}")
            self.disconnect_passenger(passenger_id)
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "active_drivers": len(self.driver_connections),
            "active_passengers": len(self.passenger_connections),
            "total_connections": len(self.driver_connections) + len(self.passenger_connections)
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()

# Start background task for cleanup (would be started in lifespan)
async def start_cleanup_task():
    """Start background task to cleanup stale connections."""
    while True:
        await asyncio.sleep(60)  # Check every minute
        await ws_manager.cleanup_stale_connections()
