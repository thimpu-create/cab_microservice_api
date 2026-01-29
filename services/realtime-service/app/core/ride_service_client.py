"""
Client for ride-service. Realtime calls ride-service for ride CRUD and persistence.
"""
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

_BASE = f"{settings.RIDE_SERVICE_URL}/api/v1/internal/rides"


def _headers() -> dict:
    h = {}
    if settings.INTERNAL_API_KEY:
        h["X-Internal-Key"] = settings.INTERNAL_API_KEY
    return h


async def create_ride_request(
    passenger_id: str,
    lat: float,
    lon: float,
    pickup_address: Optional[str] = None,
    dropoff_address: Optional[str] = None,
    dropoff_lat: Optional[float] = None,
    dropoff_lon: Optional[float] = None,
    vehicle_type_preference: Optional[str] = None,
    min_driver_rating: Optional[float] = None,
    city_code: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Create ride request. Returns { request_id, ... } or None on error. Raises on 409."""
    payload = {
        "passenger_id": passenger_id,
        "lat": lat,
        "lon": lon,
        "pickup_address": pickup_address,
        "dropoff_address": dropoff_address,
        "dropoff_lat": dropoff_lat,
        "dropoff_lon": dropoff_lon,
        "vehicle_type_preference": vehicle_type_preference,
        "min_driver_rating": min_driver_rating,
        "city_code": city_code,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{_BASE}/request",
                json=payload,
                headers=_headers(),
                timeout=10.0,
            )
            if r.status_code == 201:
                return r.json()
            if r.status_code == 409:
                data = r.json() if r.text else {}
                detail = data.get("detail", {})
                if isinstance(detail, dict) and detail.get("request_id"):
                    raise _AlreadyRequested(detail["request_id"], detail.get("message", "Already requested"))
                raise _AlreadyRequested(None, str(detail))
            return None
    except _AlreadyRequested:
        raise
    except Exception as e:
        print(f"⚠️ ride_service_client create_ride_request: {e}")
        return None


async def update_ride_status(
    request_id: str,
    status: str,
    driver_id: Optional[str] = None,
    distance_km: Optional[float] = None,
    duration_minutes: Optional[int] = None,
    fare_amount: Optional[float] = None,
) -> bool:
    """Update ride status (assigned | in_progress | completed)."""
    payload = {"status": status}
    if driver_id is not None:
        payload["driver_id"] = driver_id
    if distance_km is not None:
        payload["distance_km"] = distance_km
    if duration_minutes is not None:
        payload["duration_minutes"] = duration_minutes
    if fare_amount is not None:
        payload["fare_amount"] = fare_amount

    try:
        async with httpx.AsyncClient() as client:
            r = await client.patch(
                f"{_BASE}/{request_id}/status",
                json=payload,
                headers=_headers(),
                timeout=10.0,
            )
            return r.status_code == 200
    except Exception as e:
        print(f"⚠️ ride_service_client update_ride_status: {e}")
        return False


async def cancel_ride(request_id: str, cancelled_by: str, cancellation_reason: Optional[str] = None) -> bool:
    """Cancel ride."""
    payload = {"cancelled_by": cancelled_by}
    if cancellation_reason:
        payload["cancellation_reason"] = cancellation_reason

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{_BASE}/{request_id}/cancel",
                json=payload,
                headers=_headers(),
                timeout=10.0,
            )
            return r.status_code == 200
    except Exception as e:
        print(f"⚠️ ride_service_client cancel_ride: {e}")
        return False


async def get_history(
    user_id: str,
    role: str,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List ride history. Returns [] on error."""
    params = {"user_id": user_id, "role": role, "skip": skip, "limit": limit}
    if status_filter:
        params["status"] = status_filter
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{_BASE}/history", params=params, headers=_headers(), timeout=10.0)
            if r.status_code == 200:
                return r.json()
            return []
    except Exception as e:
        print(f"⚠️ ride_service_client get_history: {e}")
        return []


async def get_ride_by_id(ride_id: str, user_id: str, role: str) -> Optional[Dict[str, Any]]:
    """Get single ride by id. Returns None on 404/403/error."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{_BASE}/history/{ride_id}",
                params={"user_id": user_id, "role": role},
                headers=_headers(),
                timeout=10.0,
            )
            if r.status_code == 200:
                return r.json()
            return None
    except Exception as e:
        print(f"⚠️ ride_service_client get_ride_by_id: {e}")
        return None


async def get_history_stats(user_id: str, role: str) -> Optional[Dict[str, Any]]:
    """Get ride history stats. Returns None on error."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{_BASE}/history/stats",
                params={"user_id": user_id, "role": role},
                headers=_headers(),
                timeout=10.0,
            )
            if r.status_code == 200:
                return r.json()
            return None
    except Exception as e:
        print(f"⚠️ ride_service_client get_history_stats: {e}")
        return None


class _AlreadyRequested(Exception):
    def __init__(self, request_id: Optional[str], message: str):
        self.request_id = request_id
        self.message = message
        super().__init__(message)
