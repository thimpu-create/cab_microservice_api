from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.db.models import Ride, RideStatus
from app.core.security import get_current_user_id, get_current_user_role
from pydantic import BaseModel
from sqlalchemy import func

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
    
    class Config:
        from_attributes = True


@router.get("/history", response_model=List[RideHistoryResponse])
async def get_ride_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    db: Session = Depends(get_db)
):
    """
    Get ride history for the current user (passenger or driver).
    """
    query = db.query(Ride)
    
    # Filter by user role
    if role in ["Passenger", "User"]:
        query = query.filter(Ride.passenger_id == user_id)
    elif role in ["IndependentDriver", "CompanyDriver", "Driver"]:
        query = query.filter(Ride.driver_id == user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized role"
        )
    
    # Filter by status if provided
    if status_filter:
        try:
            status_enum = RideStatus[status_filter.lower()]
            query = query.filter(Ride.status == status_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    # Order by most recent first
    query = query.order_by(Ride.created_at.desc())
    
    # Apply pagination
    rides = query.offset(skip).limit(limit).all()
    
    return rides


@router.get("/history/{ride_id}", response_model=RideHistoryResponse)
async def get_ride_by_id(
    ride_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    db: Session = Depends(get_db)
):
    """
    Get a specific ride by ID. User must be the passenger or driver of the ride.
    """
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    # Verify user has access to this ride
    if role in ["Passenger", "User"]:
        if ride.passenger_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this ride"
            )
    elif role in ["IndependentDriver", "CompanyDriver", "Driver"]:
        if ride.driver_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this ride"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized role"
        )
    
    return ride


@router.get("/history/stats", response_model=dict)
async def get_ride_stats(
    user_id: UUID = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    db: Session = Depends(get_db)
):
    """
    Get ride statistics for the current user.
    """
    query = db.query(Ride)
    
    # Filter by user role
    if role in ["Passenger", "User"]:
        query = query.filter(Ride.passenger_id == user_id)
    elif role in ["IndependentDriver", "CompanyDriver", "Driver"]:
        query = query.filter(Ride.driver_id == user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized role"
        )
    
    total_rides = query.count()
    completed_rides = query.filter(Ride.status == RideStatus.completed).count()
    cancelled_rides = query.filter(Ride.status == RideStatus.cancelled).count()
    
    # Calculate total distance and earnings (for drivers)
    if role in ["Passenger", "User"]:
        total_distance = db.query(func.sum(Ride.distance_km)).filter(
            Ride.passenger_id == user_id,
            Ride.status == RideStatus.completed
        ).scalar() or 0.0
    else:
        total_distance = db.query(func.sum(Ride.distance_km)).filter(
            Ride.driver_id == user_id,
            Ride.status == RideStatus.completed
        ).scalar() or 0.0
    
    total_earnings = 0.0
    if role in ["IndependentDriver", "CompanyDriver", "Driver"]:
        total_earnings = db.query(func.sum(Ride.fare_amount)).filter(
            Ride.driver_id == user_id,
            Ride.status == RideStatus.completed
        ).scalar() or 0.0
    
    return {
        "total_rides": total_rides,
        "completed_rides": completed_rides,
        "cancelled_rides": cancelled_rides,
        "total_distance_km": float(total_distance),
        "total_earnings": float(total_earnings) if role in ["IndependentDriver", "CompanyDriver", "Driver"] else None,
    }
