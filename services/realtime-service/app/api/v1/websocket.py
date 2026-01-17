from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import time
from uuid import UUID

from app.core.redis_client import redis_conn, decode_dict, decode_val
from app.core.websocket_manager import ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/driver/{driver_id}")
async def driver_websocket(websocket: WebSocket, driver_id: str):
    """WebSocket endpoint for drivers to receive ride requests and send location updates."""
    await ws_manager.connect_driver(driver_id, websocket)
    
    # Add driver to available drivers set
    redis_conn.sadd("available_drivers", driver_id)
    print(f"🚗 Driver {driver_id} connected")
    
    # Check for ongoing ride (restore state on reconnect)
    ride_key = f"ride:driver:{driver_id}"
    ride_data = redis_conn.hgetall(ride_key)
    
    if ride_data:
        ride = decode_dict(ride_data)
        passenger_id = ride.get("passenger_id")
        pickup_lat = ride.get("pickup_lat")
        pickup_lon = ride.get("pickup_lon")
        request_id = ride.get("request_id")
        status = ride.get("status", "assigned")
        
        if passenger_id and pickup_lat is not None and pickup_lon is not None:
            try:
                await ws_manager.send_to_driver(driver_id, {
                    "type": "ongoing_ride",
                    "passenger_id": passenger_id,
                    "pickup_lat": float(pickup_lat),
                    "pickup_lon": float(pickup_lon),
                    "request_id": request_id,
                    "status": status
                })
                print(f"✅ Restored ride for driver {driver_id}")
            except ValueError:
                print(f"⚠️ Invalid lat/lon for driver {driver_id}")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle ride acceptance
            if data.get("type") == "accept_ride":
                request_id = data.get("request_id")
                print(f"✅ Driver {driver_id} ACCEPTED ride {request_id}")
                await handle_driver_accept(driver_id, request_id)
                continue
            
            # Handle ride completion
            if data.get("type") == "completed_ride":
                request_id = data.get("request_id")
                await handle_ride_completion(driver_id, request_id)
                continue
            
            # Handle location update
            lon = data.get("lon")
            lat = data.get("lat")
            
            if lon is None or lat is None:
                print("❌ Missing lat/lon:", data)
                continue
            
            try:
                lon = float(lon)
                lat = float(lat)
            except (ValueError, TypeError):
                print("❌ Invalid float:", data)
                continue
            
            # Update driver location in Redis GEO
            redis_conn.geoadd("drivers_geo", [lon, lat, driver_id])
            
            # Update driver info
            redis_conn.hset(
                f"driver:{driver_id}",
                mapping={
                    "lat": lat,
                    "lon": lon,
                    "status": data.get("status", "available")
                }
            )
            
            # If driver is in a ride, send location to passenger
            passenger_id = redis_conn.hget(f"ride:driver:{driver_id}", "passenger_id")
            if passenger_id:
                passenger_id = decode_val(passenger_id)
                await ws_manager.send_to_passenger(passenger_id, {
                    "type": "driver_location_update",
                    "driver_id": driver_id,
                    "lat": lat,
                    "lon": lon
                })
                print(f"📡 Sent driver location to passenger {passenger_id}")
    
    except WebSocketDisconnect:
        print(f"🚗 Driver {driver_id} disconnected")
        redis_conn.srem("available_drivers", driver_id)
        ws_manager.disconnect_driver(driver_id)
    except Exception as e:
        print(f"❌ Error in driver WebSocket {driver_id}: {e}")
        redis_conn.srem("available_drivers", driver_id)
        ws_manager.disconnect_driver(driver_id)


@router.websocket("/ws/passenger/{passenger_id}")
async def passenger_websocket(websocket: WebSocket, passenger_id: str):
    """WebSocket endpoint for passengers to receive ride updates."""
    await ws_manager.connect_passenger(passenger_id, websocket)
    print(f"👤 Passenger {passenger_id} connected")
    
    # Check for ongoing ride (restore state on reconnect)
    ride_key = f"ride:passenger:{passenger_id}"
    ride_data = redis_conn.hgetall(ride_key)
    
    if ride_data:
        ride = decode_dict(ride_data)
        driver_id = ride.get("driver_id")
        pickup_lat = ride.get("pickup_lat")
        pickup_lon = ride.get("pickup_lon")
        status = ride.get("status", "assigned")
        
        if driver_id and pickup_lat is not None and pickup_lon is not None:
            try:
                await ws_manager.send_to_passenger(passenger_id, {
                    "type": "ongoing_ride",
                    "driver_id": driver_id,
                    "pickup_lat": float(pickup_lat),
                    "pickup_lon": float(pickup_lon),
                    "status": status
                })
            except ValueError:
                print("⚠️ Invalid passenger ride lat/lon:", ride)
    
    try:
        while True:
            msg = await websocket.receive_text()
            print(f"👤 Passenger {passenger_id}: {msg}")
            # Handle passenger messages if needed
    
    except WebSocketDisconnect:
        print(f"👤 Passenger {passenger_id} disconnected")
        ws_manager.disconnect_passenger(passenger_id)
    except Exception as e:
        print(f"❌ Error in passenger WebSocket {passenger_id}: {e}")
        ws_manager.disconnect_passenger(passenger_id)


async def handle_driver_accept(driver_id: str, request_id: str):
    """Handle driver accepting a ride request."""
    ride_key = f"ride_request:{request_id}"
    ride_data = redis_conn.hgetall(ride_key)
    
    if not ride_data:
        await ws_manager.send_to_driver(driver_id, {"type": "ride_taken"})
        return
    
    ride = decode_dict(ride_data)
    
    # Atomic assignment using Lua script
    lua_script = """
    local k = KEYS[1]
    local expected = ARGV[1]
    local driver = ARGV[2]
    local cur = redis.call('HGET', k, 'status')
    if not cur then return -1 end
    if cur ~= expected then return 0 end
    redis.call('HSET', k, 'status', 'assigned')
    redis.call('HSET', k, 'driver_id', driver)
    return 1
    """
    
    res = redis_conn.eval(lua_script, 1, ride_key, "pending", driver_id)
    
    if res != 1:
        await ws_manager.send_to_driver(driver_id, {"type": "ride_taken"})
        return
    
    # Success - assign ride
    passenger_id = ride.get("passenger_id")
    try:
        pickup_lat = float(ride.get("pickup_lat"))
        pickup_lon = float(ride.get("pickup_lon"))
    except (ValueError, TypeError):
        await ws_manager.send_to_driver(driver_id, {
            "type": "ride_error",
            "message": "Invalid pickup coordinates."
        })
        return
    
    # Save driver's ongoing ride
    redis_conn.hset(f"ride:driver:{driver_id}", mapping={
        "request_id": request_id,
        "passenger_id": passenger_id,
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon,
        "status": "assigned"
    })
    redis_conn.expire(f"ride:driver:{driver_id}", 3600)
    
    # Save passenger's ride
    redis_conn.hset(f"ride:passenger:{passenger_id}", mapping={
        "request_id": request_id,
        "driver_id": driver_id,
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon,
        "status": "assigned"
    })
    redis_conn.expire(f"ride:passenger:{passenger_id}", 3600)
    
    # Notify passenger
    await ws_manager.send_to_passenger(passenger_id, {
        "type": "driver_assigned",
        "driver_id": driver_id,
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon
    })
    
    # Confirm to driver
    await ws_manager.send_to_driver(driver_id, {
        "type": "ride_confirmed",
        "passenger_id": passenger_id,
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon,
        "request_id": request_id
    })
    
    # Remove driver from available set
    redis_conn.srem("available_drivers", driver_id)
    
    # Notify other drivers that ride is taken
    await ws_manager.broadcast_to_drivers(
        {"type": "ride_taken", "request_id": request_id},
        exclude_driver_id=driver_id
    )


async def handle_ride_completion(driver_id: str, request_id: str):
    """Handle ride completion."""
    ride_key = f"ride_request:{request_id}"
    ride_data = redis_conn.hgetall(ride_key)
    
    if not ride_data:
        await ws_manager.send_to_driver(driver_id, {
            "type": "error",
            "message": "Ride not found"
        })
        return
    
    ride = decode_dict(ride_data)
    
    # Mark ride as completed
    redis_conn.hset(ride_key, "status", "completed")
    print(f"✅ Ride {request_id} completed by driver {driver_id}")
    
    passenger_id = ride.get("passenger_id")
    
    # Notify passenger
    if passenger_id:
        await ws_manager.send_to_passenger(passenger_id, {
            "type": "ride_completed",
            "request_id": request_id
        })
    
    # Add driver back to available list
    redis_conn.sadd("available_drivers", driver_id)
    
    # Cleanup
    redis_conn.delete(ride_key)
    redis_conn.delete(f"ride:driver:{driver_id}")
    if passenger_id:
        redis_conn.delete(f"ride:passenger:{passenger_id}")
    
    # Confirm to driver
    await ws_manager.send_to_driver(driver_id, {
        "type": "ride_completed_ack",
        "request_id": request_id
    })
