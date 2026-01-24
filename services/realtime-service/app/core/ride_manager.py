"""
Centralized ride state management with timeout handling and status tracking.
"""
import asyncio
import json
import time
from typing import Optional, Dict, Any
from uuid import UUID

from app.core.redis_client import redis_conn, decode_dict, decode_val
from app.core.config import settings
from app.core.websocket_manager import ws_manager
from app.core.notification_client import notification_client


class RideStatus:
    """Ride status constants."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"


class RideManager:
    """Manages ride lifecycle, timeouts, and state transitions."""
    
    def __init__(self):
        self.active_timeouts: Dict[str, asyncio.Task] = {}
    
    async def create_ride_request(
        self,
        request_id: str,
        passenger_id: str,
        pickup_lat: float,
        pickup_lon: float,
        dropoff_lat: Optional[float] = None,
        dropoff_lon: Optional[float] = None,
        pickup_address: Optional[str] = None,
        dropoff_address: Optional[str] = None,
        estimated_fare: Optional[float] = None,
        fare_breakdown: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new ride request and set up timeout."""
        # Save ride request in Redis
        ride_data = {
            "passenger_id": passenger_id,
            "pickup_lat": str(pickup_lat),
            "pickup_lon": str(pickup_lon),
            "status": RideStatus.PENDING,
            "created_at": str(time.time()),
        }
        
        if dropoff_lat is not None:
            ride_data["dropoff_lat"] = str(dropoff_lat)
        if dropoff_lon is not None:
            ride_data["dropoff_lon"] = str(dropoff_lon)
        if pickup_address:
            ride_data["pickup_address"] = pickup_address
        if dropoff_address:
            ride_data["dropoff_address"] = dropoff_address
        if estimated_fare is not None:
            ride_data["estimated_fare"] = str(estimated_fare)
        if fare_breakdown is not None:
            ride_data["fare_breakdown"] = json.dumps(fare_breakdown)
        
        redis_conn.hset(f"ride_request:{request_id}", mapping=ride_data)
        redis_conn.expire(f"ride_request:{request_id}", 3600)  # 1 hour expiry
        
        # Set up timeout task
        timeout_task = asyncio.create_task(
            self._handle_ride_timeout(request_id)
        )
        self.active_timeouts[request_id] = timeout_task
        
        return {
            "request_id": request_id,
            "status": RideStatus.PENDING,
            **ride_data
        }
    
    async def _handle_ride_timeout(self, request_id: str):
        """Handle ride request timeout after configured seconds."""
        await asyncio.sleep(settings.RIDE_REQUEST_TIMEOUT_SECONDS)
        
        # Check if ride is still pending
        ride_key = f"ride_request:{request_id}"
        ride_data = redis_conn.hgetall(ride_key)
        
        if not ride_data:
            # Ride was already processed
            self.active_timeouts.pop(request_id, None)
            return
        
        ride = decode_dict(ride_data)
        status = ride.get("status")
        
        if status == RideStatus.PENDING:
            # Timeout - mark as expired
            redis_conn.hset(ride_key, "status", RideStatus.EXPIRED)
            
            passenger_id = ride.get("passenger_id")
            if passenger_id:
                await ws_manager.send_to_passenger(passenger_id, {
                    "type": "ride_request_expired",
                    "request_id": request_id,
                    "message": "No driver accepted your ride request in time"
                })
                
                # Send notification to passenger
                await notification_client.notify_ride_expired(passenger_id, request_id)
            
            # Notify all drivers that this request expired
            await ws_manager.broadcast_to_drivers({
                "type": "ride_request_expired",
                "request_id": request_id
            })
            
            print(f"⏰ Ride request {request_id} expired")
        
        self.active_timeouts.pop(request_id, None)
    
    async def assign_ride(
        self,
        request_id: str,
        driver_id: str
    ) -> Optional[Dict[str, Any]]:
        """Assign a ride to a driver (atomic operation)."""
        ride_key = f"ride_request:{request_id}"
        
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
        redis.call('HSET', k, 'assigned_at', ARGV[3])
        return 1
        """
        
        res = redis_conn.eval(
            lua_script,
            1,
            ride_key,
            RideStatus.PENDING,
            driver_id,
            str(time.time())
        )
        
        if res != 1:
            return None  # Ride was already assigned or doesn't exist
        
        # Cancel timeout task
        timeout_task = self.active_timeouts.pop(request_id, None)
        if timeout_task:
            timeout_task.cancel()
        
        # Get ride data
        ride_data = redis_conn.hgetall(ride_key)
        ride = decode_dict(ride_data)
        
        passenger_id = ride.get("passenger_id")
        pickup_lat = float(ride.get("pickup_lat"))
        pickup_lon = float(ride.get("pickup_lon"))
        
        # Save driver's ongoing ride
        redis_conn.hset(f"ride:driver:{driver_id}", mapping={
            "request_id": request_id,
            "passenger_id": passenger_id,
            "pickup_lat": str(pickup_lat),
            "pickup_lon": str(pickup_lon),
            "status": RideStatus.ASSIGNED,
        })
        
        if ride.get("dropoff_lat"):
            redis_conn.hset(f"ride:driver:{driver_id}", "dropoff_lat", ride.get("dropoff_lat"))
        if ride.get("dropoff_lon"):
            redis_conn.hset(f"ride:driver:{driver_id}", "dropoff_lon", ride.get("dropoff_lon"))
        
        redis_conn.expire(f"ride:driver:{driver_id}", 3600)
        
        # Save passenger's ride
        redis_conn.hset(f"ride:passenger:{passenger_id}", mapping={
            "request_id": request_id,
            "driver_id": driver_id,
            "pickup_lat": str(pickup_lat),
            "pickup_lon": str(pickup_lon),
            "status": RideStatus.ASSIGNED,
        })
        
        if ride.get("dropoff_lat"):
            redis_conn.hset(f"ride:passenger:{passenger_id}", "dropoff_lat", ride.get("dropoff_lat"))
        if ride.get("dropoff_lon"):
            redis_conn.hset(f"ride:passenger:{passenger_id}", "dropoff_lon", ride.get("dropoff_lon"))
        
        redis_conn.expire(f"ride:passenger:{passenger_id}", 3600)
        
        # Remove driver from available set
        redis_conn.srem("available_drivers", driver_id)
        
        return ride
    
    async def cancel_ride(
        self,
        request_id: str,
        cancelled_by: str,  # "passenger" or "driver"
        user_id: str,
        cancellation_reason: Optional[str] = None
    ) -> bool:
        """Cancel a ride request or assigned ride."""
        ride_key = f"ride_request:{request_id}"
        ride_data = redis_conn.hgetall(ride_key)
        
        if not ride_data:
            return False
        
        ride = decode_dict(ride_data)
        status = ride.get("status")
        
        # Only allow cancellation if pending or assigned
        if status not in [RideStatus.PENDING, RideStatus.ASSIGNED]:
            return False
        
        # Verify cancellation permissions
        if cancelled_by == "passenger" and ride.get("passenger_id") != user_id:
            return False
        elif cancelled_by == "driver" and ride.get("driver_id") != user_id:
            return False
        
        # Cancel timeout task
        timeout_task = self.active_timeouts.pop(request_id, None)
        if timeout_task:
            timeout_task.cancel()
        
        # Update status
        redis_conn.hset(ride_key, "status", RideStatus.CANCELLED)
        redis_conn.hset(ride_key, "cancelled_by", cancelled_by)
        redis_conn.hset(ride_key, "cancelled_at", str(time.time()))
        if cancellation_reason:
            redis_conn.hset(ride_key, "cancellation_reason", cancellation_reason)
        
        passenger_id = ride.get("passenger_id")
        driver_id = ride.get("driver_id")
        
        # Notify both parties
        if cancelled_by == "passenger":
            if driver_id:
                await ws_manager.send_to_driver(driver_id, {
                    "type": "ride_cancelled",
                    "request_id": request_id,
                    "cancelled_by": "passenger",
                    "message": "Passenger cancelled the ride"
                })
                # Send notification to driver
                await notification_client.notify_ride_cancelled(
                    driver_id, "passenger", request_id, passenger_id
                )
                # Make driver available again
                redis_conn.sadd("available_drivers", driver_id)
                redis_conn.delete(f"ride:driver:{driver_id}")
        else:  # driver cancelled
            if passenger_id:
                await ws_manager.send_to_passenger(passenger_id, {
                    "type": "ride_cancelled",
                    "request_id": request_id,
                    "cancelled_by": "driver",
                    "message": "Driver cancelled the ride"
                })
                # Send notification to passenger
                await notification_client.notify_ride_cancelled(
                    passenger_id, "driver", request_id, driver_id
                )
        
        # Cleanup
        if passenger_id:
            redis_conn.delete(f"ride:passenger:{passenger_id}")
        if driver_id:
            redis_conn.delete(f"ride:driver:{driver_id}")
            redis_conn.sadd("available_drivers", driver_id)
        
        return True
    
    async def reject_ride(
        self,
        request_id: str,
        driver_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Driver rejects a ride request."""
        ride_key = f"ride_request:{request_id}"
        ride_data = redis_conn.hgetall(ride_key)
        
        if not ride_data:
            return False
        
        ride = decode_dict(ride_data)
        
        # Only allow rejection if pending
        if ride.get("status") != RideStatus.PENDING:
            return False
        
        # Track rejection (don't change status, just log)
        redis_conn.sadd(f"ride_request:{request_id}:rejected_by", driver_id)
        
        passenger_id = ride.get("passenger_id")
        
        # Notify passenger (optional - might not want to notify on every rejection)
        # await ws_manager.send_to_passenger(passenger_id, {
        #     "type": "ride_rejected",
        #     "request_id": request_id,
        #     "driver_id": driver_id
        # })
        
        return True
    
    async def update_ride_status(
        self,
        request_id: str,
        new_status: str
    ) -> bool:
        """Update ride status (e.g., assigned -> in_progress -> completed)."""
        ride_key = f"ride_request:{request_id}"
        ride_data = redis_conn.hgetall(ride_key)
        
        if not ride_data:
            return False
        
        ride = decode_dict(ride_data)
        current_status = ride.get("status")
        
        # Validate status transition
        valid_transitions = {
            RideStatus.ASSIGNED: [RideStatus.IN_PROGRESS, RideStatus.CANCELLED],
            RideStatus.IN_PROGRESS: [RideStatus.COMPLETED, RideStatus.CANCELLED],
        }
        
        if current_status not in valid_transitions:
            return False
        
        if new_status not in valid_transitions[current_status]:
            return False
        
        redis_conn.hset(ride_key, "status", new_status)
        
        if new_status == RideStatus.IN_PROGRESS:
            redis_conn.hset(ride_key, "started_at", str(time.time()))
        elif new_status == RideStatus.COMPLETED:
            redis_conn.hset(ride_key, "completed_at", str(time.time()))
        
        return True
    
    def get_ride_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get current ride status."""
        ride_key = f"ride_request:{request_id}"
        ride_data = redis_conn.hgetall(ride_key)
        
        if not ride_data:
            return None
        
        return decode_dict(ride_data)


# Global ride manager instance
ride_manager = RideManager()
