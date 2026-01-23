"""
Redis client to fetch driver availability and demand data for surge calculation.
Data is stored by realtime-service.
"""
import redis
from typing import Tuple, Optional
from app.core.config import settings


# Redis connection
redis_conn = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=False  # Keep bytes for compatibility
)


def decode_val(v):
    """Decode Redis bytes to string."""
    return v.decode() if isinstance(v, bytes) else v


def get_available_drivers_count(vehicle_type: Optional[str] = None) -> int:
    """
    Get count of available drivers.
    
    Args:
        vehicle_type: Optional vehicle type filter (would need driver-service integration)
    
    Returns:
        Count of available drivers
    """
    try:
        # Get all available drivers from Redis set
        available_drivers = redis_conn.smembers("available_drivers")
        return len(available_drivers)
    except Exception as e:
        print(f"⚠️ Error getting available drivers: {e}")
        return 0


def get_pending_requests_count(area_lat: float, area_lon: float, radius_km: float = 10.0) -> int:
    """
    Get count of pending ride requests in an area.
    
    Args:
        area_lat: Center latitude
        area_lon: Center longitude
        radius_km: Radius in kilometers
    
    Returns:
        Count of pending requests
    """
    try:
        count = 0
        # Scan for pending ride requests
        for key in redis_conn.scan_iter("ride_request:*"):
            ride_data = redis_conn.hgetall(key)
            if ride_data:
                status = decode_val(ride_data.get(b"status", b""))
                if status == "pending":
                    # Get pickup location
                    pickup_lat_str = decode_val(ride_data.get(b"pickup_lat", b""))
                    pickup_lon_str = decode_val(ride_data.get(b"pickup_lon", b""))
                    
                    if pickup_lat_str and pickup_lon_str:
                        try:
                            pickup_lat = float(pickup_lat_str)
                            pickup_lon = float(pickup_lon_str)
                            
                            # Calculate distance (simple check - could use Redis GEO)
                            from app.core.utils import calculate_distance
                            distance = calculate_distance(area_lat, area_lon, pickup_lat, pickup_lon)
                            
                            if distance <= radius_km:
                                count += 1
                        except (ValueError, TypeError):
                            continue
        
        return count
    except Exception as e:
        print(f"⚠️ Error getting pending requests: {e}")
        return 0


def calculate_demand_supply_ratio(
    area_lat: float,
    area_lon: float,
    radius_km: float = 10.0,
    vehicle_type: Optional[str] = None
) -> float:
    """
    Calculate demand/supply ratio for surge calculation.
    
    Args:
        area_lat: Center latitude
        area_lon: Center longitude
        radius_km: Radius in kilometers
        vehicle_type: Optional vehicle type filter
    
    Returns:
        Demand/supply ratio (demand / supply)
    """
    demand = get_pending_requests_count(area_lat, area_lon, radius_km)
    supply = get_available_drivers_count(vehicle_type)
    
    # Avoid division by zero
    if supply == 0:
        return float('inf') if demand > 0 else 1.0
    
    return demand / supply
