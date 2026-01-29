from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.core.security import get_current_user_id, get_current_user_role
from app.core.ride_service_client import (
    get_history,
    get_ride_by_id as ride_service_get_ride_by_id,
    get_history_stats,
)
from pydantic import BaseModel

router = APIRouter(prefix="/rides", tags=["Ride History"])


class RideHistoryResponse(BaseModel):
    id: UUID
    request_id: str
    passenger_id: UUID
    driver_id: Optional[UUID]
    pickup_lat: float
    pickup_lon: float
    pickup_address: Optional[str]
    dropoff_lat: Optional[float]
    dropoff_lon: Optional[float]
    dropoff_address: Optional[str]
    status: str
    distance_km: Optional[float]
    duration_minutes: Optional[int]
    fare_amount: Optional[float]
    created_at: datetime
    assigned_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancelled_by: Optional[str]


@router.get("/history", response_model=List[RideHistoryResponse])
async def get_ride_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
):
    """Get ride history for the current user. Proxied from ride-service."""
    if role not in ["Passenger", "User", "IndependentDriver", "CompanyDriver", "Driver"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role")
    items = await get_history(str(user_id), role, skip=skip, limit=limit, status_filter=status_filter)
    return [RideHistoryResponse.model_validate(x) for x in items]


@router.get("/history/stats", response_model=dict)
async def get_ride_stats(
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
):
    """Get ride statistics for the current user. Proxied from ride-service."""
    if role not in ["Passenger", "User", "IndependentDriver", "CompanyDriver", "Driver"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role")
    data = await get_history_stats(str(user_id), role)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ride service unavailable",
        )
    return data


@router.get("/history/{ride_id}", response_model=RideHistoryResponse)
async def get_ride_by_id(
    ride_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
):
    """Get a specific ride by ID. Proxied from ride-service."""
    if role not in ["Passenger", "User", "IndependentDriver", "CompanyDriver", "Driver"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role")
    ride = await ride_service_get_ride_by_id(str(ride_id), str(user_id), role)
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    return RideHistoryResponse.model_validate(ride)
