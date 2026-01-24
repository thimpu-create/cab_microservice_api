"""
Client to fetch fare estimates from pricing-service.
Used when creating ride requests to show price to passenger and drivers.
"""
import httpx
from typing import Optional, Dict, Any

from app.core.config import settings


async def get_fare_estimate(
    pickup_lat: float,
    pickup_lon: float,
    dropoff_lat: float,
    dropoff_lon: float,
    vehicle_type: str,
    city_code: str,
    estimated_distance_km: Optional[float] = None,
    estimated_duration_minutes: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get fare estimate from pricing-service (platform pricing, no driver_id).
    Returns None if pricing service unavailable or returns error.
    """
    if not vehicle_type:
        vehicle_type = "car"
    url = f"{settings.PRICING_SERVICE_URL}/internal/estimate"
    payload = {
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon,
        "dropoff_lat": dropoff_lat,
        "dropoff_lon": dropoff_lon,
        "vehicle_type": vehicle_type,
        "city_code": city_code,
    }
    if estimated_distance_km is not None:
        payload["estimated_distance_km"] = estimated_distance_km
    if estimated_duration_minutes is not None:
        payload["estimated_duration_minutes"] = estimated_duration_minutes

    headers = {}
    if settings.INTERNAL_API_KEY:
        headers["X-Internal-Key"] = settings.INTERNAL_API_KEY
    # When key not set, pricing-service allows anyway (dev)

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=10.0)
            if r.status_code == 200:
                return r.json()
            return None
    except Exception as e:
        print(f"⚠️ Pricing client error: {e}")
        return None
