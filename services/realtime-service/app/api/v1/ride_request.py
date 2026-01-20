from fastapi import APIRouter, HTTPException, status, Depends
import uuid
import time
from typing import List, Tuple
from uuid import UUID

import time
from app.core.redis_client import redis_conn, decode_val, decode_dict
from app.core.websocket_manager import ws_manager
from app.core.ride_manager import ride_manager, RideStatus
from app.core.notification_client import notification_client
from app.core.matching_algorithm import matching_algorithm
from app.schemas.ride import RideRequest
from app.core.security import get_current_user_id, get_current_user_role

router = APIRouter(prefix="/rides", tags=["Ride Requests"])


@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_ride(
    data: RideRequest,
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role)
):
    """
    Request a ride. Finds nearby drivers and sends ride request via WebSocket.
    Requires authentication.
    """
    # Verify user is a passenger
    if role not in ["Passenger", "User"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only passengers can request rides"
        )
    
    # Use authenticated user_id instead of payload
    passenger_id = str(user_id)
    lat, lon = data.lat, data.lon
    
    # Check if passenger already has an active ride
    existing_ride = redis_conn.hgetall(f"ride:passenger:{passenger_id}")
    if existing_ride:
        ride = decode_dict(existing_ride)
        return {
            "status": "already_in_ride",
            "request_id": ride.get("request_id"),
            "driver_id": ride.get("driver_id"),
            "ride_status": ride.get("status")
        }
    
    # Check if passenger already has a pending request
    for key in redis_conn.scan_iter("ride_request:*"):
        ride_info = redis_conn.hgetall(key)
        if ride_info:
            pid = decode_val(ride_info.get("passenger_id", b""))
            ride_status = decode_val(ride_info.get("status", b""))
            
            if pid == passenger_id and ride_status == RideStatus.PENDING:
                request_id = decode_val(key).split(":", 1)[1] if isinstance(key, bytes) else key.split(":", 1)[1]
                return {
                    "status": "already_requested",
                    "request_id": request_id,
                    "message": "You already have a pending ride request"
                }
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Save passenger location
    redis_conn.hset(
        f"passenger:{passenger_id}",
        mapping={
            "lat": str(lat),
            "lon": str(lon),
            "timestamp": str(time.time())
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
    
    # Decode driver IDs and filter available drivers
    available_drivers_raw: List[Tuple[str, float]] = []
    for raw_id, dist in nearby:
        d_id = decode_val(raw_id)
        # Check if driver is available
        if redis_conn.sismember("available_drivers", d_id):
            available_drivers_raw.append((d_id, dist))
    
    if not available_drivers_raw:
        return {
            "status": "no_drivers_available",
            "message": "No drivers available in your area"
        }
    
    # Use advanced matching algorithm to score and rank drivers
    driver_matches = await matching_algorithm.score_drivers(
        drivers_with_distance=available_drivers_raw,
        requested_vehicle_type=data.vehicle_type_preference,
        min_rating=data.min_driver_rating
    )
    
    if not driver_matches:
        return {
            "status": "no_drivers_available",
            "message": "No drivers match your preferences"
        }
    
    # Use top-scored drivers (sorted by algorithm)
    available_drivers = [(match.driver_id, match.distance_km) for match in driver_matches]
    
    # Create ride request using ride manager
    await ride_manager.create_ride_request(
        request_id=request_id,
        passenger_id=passenger_id,
        pickup_lat=lat,
        pickup_lon=lon,
        dropoff_lat=data.dropoff_lat,
        dropoff_lon=data.dropoff_lon,
        pickup_address=data.pickup_address,
        dropoff_address=data.dropoff_address,
    )
    
    # Send ride request to nearby available drivers (sorted by match score)
    notified_count = 0
    driver_ids_for_notification = []
    
    # Get match details for top drivers to include in notifications
    top_matches = driver_matches[:10]  # Top 10 matches
    
    for match in top_matches:
        driver_id = match.driver_id
        if driver_id in ws_manager.driver_connections:
            await ws_manager.send_to_driver(driver_id, {
                "type": "ride_request",
                "request_id": request_id,
                "passenger_id": passenger_id,
                "pickup_lat": lat,
                "pickup_lon": lon,
                "dropoff_lat": data.dropoff_lat,
                "dropoff_lon": data.dropoff_lon,
                "pickup_address": data.pickup_address,
                "dropoff_address": data.dropoff_address,
                "distance_km": round(match.distance_km, 2),
                "match_score": round(match.score, 3),  # Include match score for transparency
                "vehicle_type": match.vehicle_type,
                "driver_rating": match.average_rating
            })
            driver_ids_for_notification.append(driver_id)
            notified_count += 1
    
    # Send notifications to all drivers via notification service
    if driver_ids_for_notification:
        await notification_client.notify_ride_request_sent(
            driver_ids=driver_ids_for_notification,
            passenger_id=passenger_id,
            request_id=request_id,
            pickup_lat=lat,
            pickup_lon=lon,
            distance_km=round(available_drivers[0][1], 2) if available_drivers else 0.0,
            pickup_address=data.pickup_address
        )
    
    return {
        "status": "request_sent",
        "request_id": request_id,
        "drivers_notified": notified_count,
        "message": f"Ride request sent to {notified_count} nearby drivers"
    }


@router.post("/{request_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_ride(
    request_id: str,
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role)
):
    """
    Cancel a ride request or assigned ride.
    Can be called by passenger or driver.
    """
    user_id_str = str(user_id)
    
    # Get ride info to determine who can cancel
    ride_data = ride_manager.get_ride_status(request_id)
    if not ride_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    # Determine who is cancelling
    cancelled_by = None
    if ride_data.get("passenger_id") == user_id_str:
        cancelled_by = "passenger"
    elif ride_data.get("driver_id") == user_id_str:
        cancelled_by = "driver"
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to cancel this ride"
        )
    
    # Get cancellation reason from request body if provided
    cancellation_reason = None  # Could be extracted from request body if needed
    
    # Cancel the ride
    success = await ride_manager.cancel_ride(request_id, cancelled_by, user_id_str, cancellation_reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel ride in current status"
        )
    
    # Save cancelled ride to database
    try:
        from app.db.session import SessionLocal
        from app.core.ride_persistence import save_ride_to_db
        
        db = SessionLocal()
        try:
            save_ride_to_db(
                db=db,
                request_id=request_id,
                passenger_id=ride_data.get("passenger_id"),
                driver_id=ride_data.get("driver_id"),
                pickup_lat=float(ride_data.get("pickup_lat")),
                pickup_lon=float(ride_data.get("pickup_lon")),
                dropoff_lat=float(ride_data.get("dropoff_lat")) if ride_data.get("dropoff_lat") else None,
                dropoff_lon=float(ride_data.get("dropoff_lon")) if ride_data.get("dropoff_lon") else None,
                pickup_address=ride_data.get("pickup_address"),
                dropoff_address=ride_data.get("dropoff_address"),
                status="cancelled",
                created_at=ride_data.get("created_at"),
                assigned_at=ride_data.get("assigned_at"),
                cancelled_at=time.time(),
                cancelled_by=cancelled_by,
                cancellation_reason=cancellation_reason,
            )
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️ Failed to save cancelled ride to database: {e}")
        # Continue even if DB save fails
    
    return {
        "status": "cancelled",
        "request_id": request_id,
        "cancelled_by": cancelled_by,
        "message": "Ride cancelled successfully"
    }


@router.get("/{request_id}/status", status_code=status.HTTP_200_OK)
async def get_ride_status(
    request_id: str,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get the current status of a ride request.
    """
    ride_data = ride_manager.get_ride_status(request_id)
    
    if not ride_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    # Verify user has access to this ride
    user_id_str = str(user_id)
    if ride_data.get("passenger_id") != user_id_str and ride_data.get("driver_id") != user_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this ride"
        )
    
    return {
        "request_id": request_id,
        "status": ride_data.get("status"),
        "passenger_id": ride_data.get("passenger_id"),
        "driver_id": ride_data.get("driver_id"),
        "pickup_lat": ride_data.get("pickup_lat"),
        "pickup_lon": ride_data.get("pickup_lon"),
        "dropoff_lat": ride_data.get("dropoff_lat"),
        "dropoff_lon": ride_data.get("dropoff_lon"),
        "created_at": ride_data.get("created_at"),
        "assigned_at": ride_data.get("assigned_at"),
    }


@router.get("/active", status_code=status.HTTP_200_OK)
async def get_active_ride(
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role)
):
    """
    Get the active ride for the current user (passenger or driver).
    """
    user_id_str = str(user_id)
    
    if role in ["Passenger", "User"]:
        # Check passenger's active ride
        ride_data = redis_conn.hgetall(f"ride:passenger:{user_id_str}")
        if not ride_data:
            return {"status": "no_active_ride"}
        
        ride = decode_dict(ride_data)
        request_id = ride.get("request_id")
        
        # Get full ride details
        full_ride = ride_manager.get_ride_status(request_id)
        if not full_ride:
            return {"status": "no_active_ride"}
        
        return {
            "status": "active",
            "request_id": request_id,
            "driver_id": ride.get("driver_id"),
            "ride_status": ride.get("status"),
            "pickup_lat": ride.get("pickup_lat"),
            "pickup_lon": ride.get("pickup_lon"),
            "dropoff_lat": ride.get("dropoff_lat"),
            "dropoff_lon": ride.get("dropoff_lon"),
            **full_ride
        }
    
    elif role in ["IndependentDriver", "CompanyDriver", "Driver"]:
        # Check driver's active ride
        # First, find driver_id from user_id (would need to query driver service)
        # For now, we'll search all driver rides
        for key in redis_conn.scan_iter("ride:driver:*"):
            ride_data = redis_conn.hgetall(key)
            if ride_data:
                ride = decode_dict(ride_data)
                driver_user_id = redis_conn.hget(f"driver:{key.split(':')[-1]}", "user_id")
                if driver_user_id and decode_val(driver_user_id) == user_id_str:
                    request_id = ride.get("request_id")
                    full_ride = ride_manager.get_ride_status(request_id)
                    if full_ride:
                        return {
                            "status": "active",
                            "request_id": request_id,
                            "passenger_id": ride.get("passenger_id"),
                            "ride_status": ride.get("status"),
                            "pickup_lat": ride.get("pickup_lat"),
                            "pickup_lon": ride.get("pickup_lon"),
                            "dropoff_lat": ride.get("dropoff_lat"),
                            "dropoff_lon": ride.get("dropoff_lon"),
                            **full_ride
                        }
        
        return {"status": "no_active_ride"}
    
    return {"status": "no_active_ride"}
