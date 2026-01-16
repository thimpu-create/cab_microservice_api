from fastapi import APIRouter, HTTPException, status
import uuid
import time
from typing import List, Tuple

from app.core.redis_client import redis_conn, decode_val
from app.core.websocket_manager import ws_manager
from app.schemas.ride import RideRequest

router = APIRouter(prefix="/rides", tags=["Ride Requests"])


@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_ride(data: RideRequest):
    """
    Request a ride. Finds nearby drivers and sends ride request via WebSocket.
    """
    passenger_id = data.passenger_id
    lat, lon = data.lat, data.lon
    
    # Check if passenger already has an active ride
    existing_ride = redis_conn.get(f"ride:passenger:{passenger_id}")
    if existing_ride:
        return {
            "status": "already_in_ride",
            "ride_id": decode_val(existing_ride)
        }
    
    # Check if passenger already has a pending request
    for key in redis_conn.scan_iter("ride_request:*"):
        ride_info = redis_conn.hgetall(key)
        if ride_info:
            pid = decode_val(ride_info.get("passenger_id", b""))
            ride_status = decode_val(ride_info.get("status", b""))
            
            if pid == passenger_id and ride_status == "pending":
                request_id = decode_val(key).split(":", 1)[1] if isinstance(key, bytes) else key.split(":", 1)[1]
                return {
                    "status": "already_requested",
                    "request_id": request_id
                }
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Save passenger location
    redis_conn.hset(
        f"passenger:{passenger_id}",
        mapping={
            "lat": lat,
            "lon": lon,
            "timestamp": time.time()
        }
    )
    
    # Find nearby drivers (within 10km)
    nearby = redis_conn.georadius(
        "drivers_geo",
        lon,
        lat,
        10,
        unit="km",
        withdist=True
    )
    
    # Decode driver IDs
    available_drivers: List[Tuple[str, float]] = []
    for raw_id, dist in nearby:
        d_id = decode_val(raw_id)
        # Check if driver is available
        if redis_conn.sismember("available_drivers", d_id):
            available_drivers.append((d_id, dist))
    
    if not available_drivers:
        return {"status": "no_drivers_available"}
    
    # Create ride request in Redis
    redis_conn.hset(
        f"ride_request:{request_id}",
        mapping={
            "passenger_id": passenger_id,
            "pickup_lat": lat,
            "pickup_lon": lon,
            "status": "pending"
        }
    )
    redis_conn.expire(f"ride_request:{request_id}", 300)  # Expire after 5 minutes
    
    # Send ride request to nearby available drivers
    notified_count = 0
    for driver_id, distance in available_drivers:
        if driver_id in ws_manager.driver_connections:
            await ws_manager.send_to_driver(driver_id, {
                "type": "ride_request",
                "request_id": request_id,
                "passenger_id": passenger_id,
                "pickup_lat": lat,
                "pickup_lon": lon,
                "distance_km": round(distance, 2)
            })
            notified_count += 1
    
    return {
        "status": "request_sent",
        "request_id": request_id,
        "drivers_notified": notified_count
    }
