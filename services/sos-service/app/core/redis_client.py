"""
Redis client to fetch live location from realtime-service.
Passenger locations are stored in Redis with key: passenger:{passenger_id}
"""
import redis
from typing import Optional, Tuple
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


def decode_dict(d):
    """Decode all values in a Redis hash dict."""
    return {decode_val(k): decode_val(v) for k, v in d.items()}


def get_live_location(user_id: str) -> Optional[Tuple[float, float]]:
    """
    Get user's live location from Redis (stored by realtime-service).
    
    Args:
        user_id: User ID (passenger_id)
    
    Returns:
        Tuple of (latitude, longitude) if found, None otherwise
    """
    try:
        # Get location from Redis (key: passenger:{user_id})
        location_data = redis_conn.hgetall(f"passenger:{user_id}")
        
        if not location_data:
            return None
        
        # Decode the hash
        location = decode_dict(location_data)
        
        # Extract lat/lon
        lat_str = location.get("lat")
        lon_str = location.get("lon")
        
        if not lat_str or not lon_str:
            return None
        
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            return (lat, lon)
        except (ValueError, TypeError):
            return None
            
    except Exception as e:
        print(f"⚠️ Error getting live location from Redis: {e}")
        return None
