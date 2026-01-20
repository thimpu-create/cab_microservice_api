from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import time
from uuid import UUID

from app.core.redis_client import redis_conn, decode_dict, decode_val
from app.core.websocket_manager import ws_manager
from app.core.security import authenticate_websocket, verify_role
from app.core.ride_manager import ride_manager, RideStatus
from app.core.utils import calculate_eta_to_pickup, calculate_eta_to_dropoff
from app.core.notification_client import notification_client

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/driver/{driver_id}")
async def driver_websocket(websocket: WebSocket, driver_id: str):
    """
    WebSocket endpoint for drivers to receive ride requests and send location updates.
    Requires JWT token in query params: ?token=<jwt_token>
    """
    # Authenticate WebSocket connection
    user_id, role, error = await authenticate_websocket(websocket)
    if error:
        return  # Connection already closed
    
    # Verify user is a driver
    if not verify_role(role, ["IndependentDriver", "CompanyDriver", "Driver"]):
        await websocket.close(code=1008, reason="Unauthorized: Driver role required")
        return
    
    # Verify driver_id matches authenticated user_id (optional: could also fetch from driver service)
    # For now, we'll trust the driver_id parameter but log the user_id
    print(f"🚗 Driver {driver_id} (user_id: {user_id}) connected")
    
    await ws_manager.connect_driver(driver_id, websocket)
    
    # Add driver to available drivers set
    redis_conn.sadd("available_drivers", driver_id)
    
    # Store user_id mapping for verification
    redis_conn.hset(f"driver:{driver_id}", "user_id", str(user_id))
    
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
        dropoff_lat = ride.get("dropoff_lat")
        dropoff_lon = ride.get("dropoff_lon")
        
        if passenger_id and pickup_lat is not None and pickup_lon is not None:
            try:
                ride_info = {
                    "type": "ongoing_ride",
                    "passenger_id": passenger_id,
                    "pickup_lat": float(pickup_lat),
                    "pickup_lon": float(pickup_lon),
                    "request_id": request_id,
                    "status": status
                }
                if dropoff_lat:
                    ride_info["dropoff_lat"] = float(dropoff_lat)
                if dropoff_lon:
                    ride_info["dropoff_lon"] = float(dropoff_lon)
                
                await ws_manager.send_to_driver(driver_id, ride_info)
                print(f"✅ Restored ride for driver {driver_id}")
            except ValueError:
                print(f"⚠️ Invalid lat/lon for driver {driver_id}")
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            # Handle ride acceptance
            if msg_type == "accept_ride":
                request_id = data.get("request_id")
                print(f"✅ Driver {driver_id} ACCEPTED ride {request_id}")
                await handle_driver_accept(driver_id, request_id)
                continue
            
            # Handle ride rejection
            if msg_type == "reject_ride":
                request_id = data.get("request_id")
                reason = data.get("reason")
                print(f"❌ Driver {driver_id} REJECTED ride {request_id}")
                await ride_manager.reject_ride(request_id, driver_id, reason)
                continue
            
            # Handle ride cancellation
            if msg_type == "cancel_ride":
                request_id = data.get("request_id")
                reason = data.get("reason")
                print(f"🚫 Driver {driver_id} CANCELLED ride {request_id}")
                success = await ride_manager.cancel_ride(request_id, "driver", driver_id)
                if success:
                    await ws_manager.send_to_driver(driver_id, {
                        "type": "ride_cancelled_ack",
                        "request_id": request_id
                    })
                else:
                    await ws_manager.send_to_driver(driver_id, {
                        "type": "error",
                        "message": "Failed to cancel ride"
                    })
                continue
            
            # Handle ride status update (assigned -> in_progress -> completed)
            if msg_type == "update_ride_status":
                request_id = data.get("request_id")
                new_status = data.get("status")
                
                if new_status == "in_progress":
                    success = await ride_manager.update_ride_status(request_id, RideStatus.IN_PROGRESS)
                    if success:
                        # Update local ride status
                        redis_conn.hset(f"ride:driver:{driver_id}", "status", RideStatus.IN_PROGRESS)
                        redis_conn.hset(f"ride_request:{request_id}", "status", RideStatus.IN_PROGRESS)
                        
                        # Notify passenger
                        ride_data = redis_conn.hgetall(f"ride_request:{request_id}")
                        if ride_data:
                            ride = decode_dict(ride_data)
                            passenger_id = ride.get("passenger_id")
                            if passenger_id:
                                await ws_manager.send_to_passenger(passenger_id, {
                                    "type": "ride_started",
                                    "request_id": request_id,
                                    "driver_id": driver_id
                                })
                                # Send notification to passenger
                                await notification_client.notify_ride_started(
                                    passenger_id, driver_id, request_id
                                )
                
                elif new_status == "completed":
                    await handle_ride_completion(driver_id, request_id)
                continue
            
            # Handle ride completion (legacy support)
            if msg_type == "completed_ride":
                request_id = data.get("request_id")
                await handle_ride_completion(driver_id, request_id)
                continue
            
            # Handle ping/heartbeat
            if msg_type == "ping":
                ws_manager.update_driver_ping(driver_id)
                await ws_manager.send_to_driver(driver_id, {"type": "pong"})
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
            
            # Update ping time on location update
            ws_manager.update_driver_ping(driver_id)
            
            # Update driver location in Redis GEO
            redis_conn.geoadd("drivers_geo", [lon, lat, driver_id])
            
            # Update driver info
            redis_conn.hset(
                f"driver:{driver_id}",
                mapping={
                    "lat": str(lat),
                    "lon": str(lon),
                    "status": data.get("status", "available"),
                    "last_update": str(time.time())
                }
            )
            
            # If driver is in a ride, send location to passenger with ETA
            passenger_id = redis_conn.hget(f"ride:driver:{driver_id}", "passenger_id")
            if passenger_id:
                passenger_id = decode_val(passenger_id)
                
                # Get ride details for ETA calculation
                ride_data = redis_conn.hgetall(f"ride:driver:{driver_id}")
                ride = decode_dict(ride_data)
                ride_status = ride.get("status", "assigned")
                
                location_update = {
                    "type": "driver_location_update",
                    "driver_id": driver_id,
                    "lat": lat,
                    "lon": lon,
                    "timestamp": time.time()
                }
                
                # Calculate ETA based on ride status
                if ride_status == RideStatus.ASSIGNED:
                    # Calculate ETA to pickup
                    pickup_lat = ride.get("pickup_lat")
                    pickup_lon = ride.get("pickup_lon")
                    if pickup_lat and pickup_lon:
                        try:
                            distance, eta = calculate_eta_to_pickup(
                                lat, lon, float(pickup_lat), float(pickup_lon)
                            )
                            location_update["eta_to_pickup_minutes"] = eta
                            location_update["distance_to_pickup_km"] = round(distance, 2)
                        except (ValueError, TypeError):
                            pass
                
                elif ride_status == RideStatus.IN_PROGRESS:
                    # Calculate ETA to dropoff
                    dropoff_lat = ride.get("dropoff_lat")
                    dropoff_lon = ride.get("dropoff_lon")
                    if dropoff_lat and dropoff_lon:
                        try:
                            distance, eta = calculate_eta_to_dropoff(
                                lat, lon, float(dropoff_lat), float(dropoff_lon)
                            )
                            location_update["eta_to_dropoff_minutes"] = eta
                            location_update["distance_to_dropoff_km"] = round(distance, 2)
                        except (ValueError, TypeError):
                            pass
                
                await ws_manager.send_to_passenger(passenger_id, location_update)
                print(f"📡 Sent driver location to passenger {passenger_id}")
    
    except WebSocketDisconnect:
        print(f"🚗 Driver {driver_id} disconnected")
        redis_conn.srem("available_drivers", driver_id)
        ws_manager.disconnect_driver(driver_id)
    except Exception as e:
        print(f"❌ Error in driver WebSocket {driver_id}: {e}")
        import traceback
        traceback.print_exc()
        redis_conn.srem("available_drivers", driver_id)
        ws_manager.disconnect_driver(driver_id)


@router.websocket("/ws/passenger/{passenger_id}")
async def passenger_websocket(websocket: WebSocket, passenger_id: str):
    """
    WebSocket endpoint for passengers to receive ride updates.
    Requires JWT token in query params: ?token=<jwt_token>
    """
    # Authenticate WebSocket connection
    user_id, role, error = await authenticate_websocket(websocket)
    if error:
        return  # Connection already closed
    
    # Verify user is a passenger
    if not verify_role(role, ["Passenger", "User"]):
        await websocket.close(code=1008, reason="Unauthorized: Passenger role required")
        return
    
    # Verify passenger_id matches authenticated user_id
    print(f"👤 Passenger {passenger_id} (user_id: {user_id}) connected")
    
    await ws_manager.connect_passenger(passenger_id, websocket)
    
    # Check for ongoing ride (restore state on reconnect)
    ride_key = f"ride:passenger:{passenger_id}"
    ride_data = redis_conn.hgetall(ride_key)
    
    if ride_data:
        ride = decode_dict(ride_data)
        driver_id = ride.get("driver_id")
        pickup_lat = ride.get("pickup_lat")
        pickup_lon = ride.get("pickup_lon")
        status = ride.get("status", "assigned")
        dropoff_lat = ride.get("dropoff_lat")
        dropoff_lon = ride.get("dropoff_lon")
        request_id = ride.get("request_id")
        
        if driver_id and pickup_lat is not None and pickup_lon is not None:
            try:
                ride_info = {
                    "type": "ongoing_ride",
                    "driver_id": driver_id,
                    "pickup_lat": float(pickup_lat),
                    "pickup_lon": float(pickup_lon),
                    "status": status,
                    "request_id": request_id
                }
                if dropoff_lat:
                    ride_info["dropoff_lat"] = float(dropoff_lat)
                if dropoff_lon:
                    ride_info["dropoff_lon"] = float(dropoff_lon)
                
                await ws_manager.send_to_passenger(passenger_id, ride_info)
            except ValueError:
                print("⚠️ Invalid passenger ride lat/lon:", ride)
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            # Handle ride cancellation
            if msg_type == "cancel_ride":
                request_id = data.get("request_id")
                reason = data.get("reason")
                print(f"🚫 Passenger {passenger_id} CANCELLED ride {request_id}")
                success = await ride_manager.cancel_ride(request_id, "passenger", passenger_id, reason)
                if success:
                    await ws_manager.send_to_passenger(passenger_id, {
                        "type": "ride_cancelled_ack",
                        "request_id": request_id
                    })
                else:
                    await ws_manager.send_to_passenger(passenger_id, {
                        "type": "error",
                        "message": "Failed to cancel ride"
                    })
                continue
            
            # Handle ping/heartbeat
            if msg_type == "ping":
                ws_manager.update_passenger_ping(passenger_id)
                await ws_manager.send_to_passenger(passenger_id, {"type": "pong"})
                continue
            
            # Handle passenger location updates during ride
            if msg_type == "location_update":
                lat = data.get("lat")
                lon = data.get("lon")
                
                if lat is not None and lon is not None:
                    # Update passenger location
                    redis_conn.hset(f"passenger:{passenger_id}", mapping={
                        "lat": str(lat),
                        "lon": str(lon),
                        "timestamp": str(time.time())
                    })
                    
                    # Update ping time
                    ws_manager.update_passenger_ping(passenger_id)
                    
                    # If in a ride, notify driver
                    ride_data = redis_conn.hgetall(ride_key)
                    if ride_data:
                        ride = decode_dict(ride_data)
                        driver_id = ride.get("driver_id")
                        if driver_id:
                            await ws_manager.send_to_driver(driver_id, {
                                "type": "passenger_location_update",
                                "passenger_id": passenger_id,
                                "lat": lat,
                                "lon": lon,
                                "timestamp": time.time()
                            })
                continue
            
            print(f"👤 Passenger {passenger_id} sent: {data}")
    
    except WebSocketDisconnect:
        print(f"👤 Passenger {passenger_id} disconnected")
        ws_manager.disconnect_passenger(passenger_id)
    except Exception as e:
        print(f"❌ Error in passenger WebSocket {passenger_id}: {e}")
        import traceback
        traceback.print_exc()
        ws_manager.disconnect_passenger(passenger_id)


async def handle_driver_accept(driver_id: str, request_id: str):
    """Handle driver accepting a ride request."""
    ride = await ride_manager.assign_ride(request_id, driver_id)
    
    if not ride:
        await ws_manager.send_to_driver(driver_id, {
            "type": "ride_taken",
            "request_id": request_id,
            "message": "Ride was already taken or expired"
        })
        return
    
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
    
    dropoff_lat = ride.get("dropoff_lat")
    dropoff_lon = ride.get("dropoff_lon")
    
    # Notify passenger
    passenger_msg = {
        "type": "driver_assigned",
        "driver_id": driver_id,
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon,
        "request_id": request_id
    }
    if dropoff_lat:
        passenger_msg["dropoff_lat"] = float(dropoff_lat)
    if dropoff_lon:
        passenger_msg["dropoff_lon"] = float(dropoff_lon)
    
    await ws_manager.send_to_passenger(passenger_id, passenger_msg)
    
    # Send notification to passenger about driver assignment
    await notification_client.notify_driver_assigned(
        passenger_id=passenger_id,
        driver_id=driver_id,
        request_id=request_id,
        pickup_lat=pickup_lat,
        pickup_lon=pickup_lon,
        dropoff_lat=float(dropoff_lat) if dropoff_lat else None,
        dropoff_lon=float(dropoff_lon) if dropoff_lon else None
    )
    
    # Confirm to driver
    driver_msg = {
        "type": "ride_confirmed",
        "passenger_id": passenger_id,
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon,
        "request_id": request_id
    }
    if dropoff_lat:
        driver_msg["dropoff_lat"] = float(dropoff_lat)
    if dropoff_lon:
        driver_msg["dropoff_lon"] = float(dropoff_lon)
    
    await ws_manager.send_to_driver(driver_id, driver_msg)
    
    # Notify other drivers that ride is taken
    await ws_manager.broadcast_to_drivers(
        {"type": "ride_taken", "request_id": request_id},
        exclude_driver_id=driver_id
    )


async def handle_ride_completion(driver_id: str, request_id: str):
    """Handle ride completion."""
    from app.db.session import SessionLocal
    from app.core.ride_persistence import save_ride_to_db, calculate_ride_duration
    
    ride_key = f"ride_request:{request_id}"
    ride_data = redis_conn.hgetall(ride_key)
    
    if not ride_data:
        await ws_manager.send_to_driver(driver_id, {
            "type": "error",
            "message": "Ride not found"
        })
        return
    
    # Update status to completed
    success = await ride_manager.update_ride_status(request_id, RideStatus.COMPLETED)
    
    if not success:
        await ws_manager.send_to_driver(driver_id, {
            "type": "error",
            "message": "Cannot complete ride in current status"
        })
        return
    
    ride = decode_dict(ride_data)
    passenger_id = ride.get("passenger_id")
    
    # Calculate duration
    started_at = ride.get("started_at")
    completed_at = time.time()
    duration_minutes = calculate_ride_duration(started_at, completed_at)
    
    # Save to database
    try:
        db = SessionLocal()
        try:
            save_ride_to_db(
                db=db,
                request_id=request_id,
                passenger_id=passenger_id,
                driver_id=driver_id,
                pickup_lat=float(ride.get("pickup_lat")),
                pickup_lon=float(ride.get("pickup_lon")),
                dropoff_lat=float(ride.get("dropoff_lat")) if ride.get("dropoff_lat") else None,
                dropoff_lon=float(ride.get("dropoff_lon")) if ride.get("dropoff_lon") else None,
                pickup_address=ride.get("pickup_address"),
                dropoff_address=ride.get("dropoff_address"),
                status=RideStatus.COMPLETED,
                created_at=ride.get("created_at"),
                assigned_at=ride.get("assigned_at"),
                started_at=started_at,
                completed_at=completed_at,
                duration_minutes=duration_minutes,
            )
            print(f"💾 Saved ride {request_id} to database")
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️ Failed to save ride to database: {e}")
        # Continue even if DB save fails
    
    # Notify passenger
    if passenger_id:
        await ws_manager.send_to_passenger(passenger_id, {
            "type": "ride_completed",
            "request_id": request_id,
            "driver_id": driver_id
        })
        # Send notification to passenger
        await notification_client.notify_ride_completed(
            passenger_id, driver_id, request_id
        )
    
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
    
    print(f"✅ Ride {request_id} completed by driver {driver_id}")
