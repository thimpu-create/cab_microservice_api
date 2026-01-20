from fastapi import APIRouter, Depends, HTTPException, status, Request
from uuid import UUID
import httpx

from app.core.security import get_current_user_id, get_current_user_role

router = APIRouter(
    prefix="/rides",
    tags=["Ride Management"],
)

REALTIME_SERVICE_URL = "http://realtime-service:8007/api/v1"


@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_ride(
    request: Request,
    lat: float,
    lon: float,
    dropoff_lat: float = None,
    dropoff_lon: float = None,
    pickup_address: str = None,
    dropoff_address: str = None,
    vehicle_type_preference: str = None,  # bike, car, auto, premium_car
    min_driver_rating: float = None,  # Minimum driver rating (1.0-5.0)
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role)
):
    """
    Request a ride. Forwards request to realtime service.
    """
    # Verify user is a passenger
    if role not in ["Passenger", "User"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only passengers can request rides"
        )
    
    # Get authorization header
    auth_header = request.headers.get("Authorization", "")
    
    # Forward to realtime service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{REALTIME_SERVICE_URL}/rides/request",
                json={
                    "passenger_id": str(user_id),
                    "lat": lat,
                    "lon": lon,
                    "dropoff_lat": dropoff_lat,
                    "dropoff_lon": dropoff_lon,
                    "pickup_address": pickup_address,
                    "dropoff_address": dropoff_address,
                    "vehicle_type_preference": vehicle_type_preference,
                    "min_driver_rating": min_driver_rating,
                },
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Realtime service unavailable: {str(e)}"
        )


@router.post("/{request_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_ride(
    request: Request,
    request_id: str,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Cancel a ride request.
    """
    auth_header = request.headers.get("Authorization", "")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{REALTIME_SERVICE_URL}/rides/{request_id}/cancel",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Realtime service unavailable: {str(e)}"
        )


@router.get("/{request_id}/status", status_code=status.HTTP_200_OK)
async def get_ride_status(
    request: Request,
    request_id: str,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get the status of a ride request.
    """
    auth_header = request.headers.get("Authorization", "")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{REALTIME_SERVICE_URL}/rides/{request_id}/status",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Realtime service unavailable: {str(e)}"
        )


@router.get("/active", status_code=status.HTTP_200_OK)
async def get_active_ride(
    request: Request,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get the active ride for the current passenger.
    """
    auth_header = request.headers.get("Authorization", "")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{REALTIME_SERVICE_URL}/rides/active",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json().get("detail", response.text) if response.headers.get("content-type") == "application/json" else response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Realtime service unavailable: {str(e)}"
        )
