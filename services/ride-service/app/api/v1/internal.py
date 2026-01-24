"""
Internal API for ride operations. Called by realtime-service.
Uses X-Internal-Key when INTERNAL_API_KEY is set.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.db.session import get_db
from app.db.models import Ride, RideStatusEnum
from app.schemas.ride import (
    RideRequestCreate,
    RideCreateResponse,
    RideStatusUpdate,
    RideCancel,
    RideStatusResponse,
    RideHistoryItem,
    RideHistoryStats,
)

router = APIRouter(prefix="/internal/rides", tags=["Internal Rides"])


def _verify_internal_key(x_internal_key: Optional[str] = Header(None, alias="X-Internal-Key")):
    if not settings.INTERNAL_API_KEY:
        return True
    if x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal key")
    return True


@router.post("/request", response_model=RideCreateResponse, status_code=status.HTTP_201_CREATED)
def create_ride_request(
    body: RideRequestCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(_verify_internal_key),
):
    """
    Create a ride request (pending). Realtime-service calls this, then does matching/Redis/WS.
    Returns request_id for realtime to use.
    """
    # Reject if passenger already has a pending ride
    existing = (
        db.query(Ride)
        .filter(
            Ride.passenger_id == uuid.UUID(body.passenger_id),
            Ride.status == RideStatusEnum.pending,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Passenger already has a pending ride request",
                "request_id": existing.request_id,
            },
        )

    request_id = str(uuid.uuid4())
    vt = body.vehicle_type_preference.value if body.vehicle_type_preference else None
    ride = Ride(
        request_id=request_id,
        passenger_id=uuid.UUID(body.passenger_id),
        pickup_lat=body.lat,
        pickup_lon=body.lon,
        pickup_address=body.pickup_address,
        dropoff_lat=body.dropoff_lat,
        dropoff_lon=body.dropoff_lon,
        dropoff_address=body.dropoff_address,
        vehicle_type=vt,
        city_code=body.city_code or None,
        status=RideStatusEnum.pending,
    )
    db.add(ride)
    db.commit()
    db.refresh(ride)

    return RideCreateResponse(
        request_id=request_id,
        status="pending",
        passenger_id=body.passenger_id,
        pickup_lat=body.lat,
        pickup_lon=body.lon,
        dropoff_lat=body.dropoff_lat,
        dropoff_lon=body.dropoff_lon,
        pickup_address=body.pickup_address,
        dropoff_address=body.dropoff_address,
        vehicle_type=vt,
        city_code=body.city_code,
        created_at=ride.created_at,
    )


def _user_filter(query, user_id: uuid.UUID, role: str):
    if role in ("Passenger", "User"):
        return query.filter(Ride.passenger_id == user_id)
    if role in ("IndependentDriver", "CompanyDriver", "Driver"):
        return query.filter(Ride.driver_id == user_id)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role for history")


@router.get("/history", response_model=List[RideHistoryItem])
def get_ride_history(
    user_id: str = Query(..., description="User UUID"),
    role: str = Query(..., description="Passenger|User|IndependentDriver|CompanyDriver|Driver"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: bool = Depends(_verify_internal_key),
):
    """List ride history for user. Realtime-service proxies this for GET /rides/history."""
    uid = uuid.UUID(user_id)
    query = db.query(Ride)
    query = _user_filter(query, uid, role)
    if status_filter:
        try:
            st = RideStatusEnum(status_filter.lower())
            query = query.filter(Ride.status == st)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    query = query.order_by(Ride.created_at.desc())
    rides = query.offset(skip).limit(limit).all()
    return [RideHistoryItem.model_validate(r) for r in rides]


@router.get("/history/stats", response_model=RideHistoryStats)
def get_ride_history_stats(
    user_id: str = Query(...),
    role: str = Query(...),
    db: Session = Depends(get_db),
    _: bool = Depends(_verify_internal_key),
):
    """Ride stats for user. Realtime-service proxies this for GET /rides/history/stats."""
    uid = uuid.UUID(user_id)
    query = db.query(Ride)
    query = _user_filter(query, uid, role)
    total_rides = query.count()
    completed_rides = query.filter(Ride.status == RideStatusEnum.completed).count()
    cancelled_rides = query.filter(Ride.status == RideStatusEnum.cancelled).count()
    q_dist = db.query(func.coalesce(func.sum(Ride.distance_km), 0)).filter(Ride.status == RideStatusEnum.completed)
    if role in ("Passenger", "User"):
        q_dist = q_dist.filter(Ride.passenger_id == uid)
    else:
        q_dist = q_dist.filter(Ride.driver_id == uid)
    total_distance_km = float(q_dist.scalar() or 0)
    total_earnings = None
    if role in ("IndependentDriver", "CompanyDriver", "Driver"):
        q_earn = db.query(func.coalesce(func.sum(Ride.fare_amount), 0)).filter(
            Ride.driver_id == uid, Ride.status == RideStatusEnum.completed
        )
        total_earnings = float(q_earn.scalar() or 0)
    return RideHistoryStats(
        total_rides=total_rides,
        completed_rides=completed_rides,
        cancelled_rides=cancelled_rides,
        total_distance_km=total_distance_km,
        total_earnings=total_earnings,
    )


@router.get("/history/{ride_id}", response_model=RideHistoryItem)
def get_ride_by_id(
    ride_id: str,
    user_id: str = Query(...),
    role: str = Query(...),
    db: Session = Depends(get_db),
    _: bool = Depends(_verify_internal_key),
):
    """Get single ride by id. Realtime-service proxies for GET /rides/history/{ride_id}."""
    uid = uuid.UUID(user_id)
    try:
        rid = uuid.UUID(ride_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ride_id")
    ride = db.query(Ride).filter(Ride.id == rid).first()
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")
    if role in ("Passenger", "User") and ride.passenger_id != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this ride")
    if role in ("IndependentDriver", "CompanyDriver", "Driver") and ride.driver_id != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this ride")
    return RideHistoryItem.model_validate(ride)


@router.get("/{request_id}/status", response_model=RideStatusResponse)
def get_ride_status(
    request_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(_verify_internal_key),
):
    """Get ride status by request_id. Used by realtime-service."""
    ride = db.query(Ride).filter(Ride.request_id == request_id).first()
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")

    return RideStatusResponse(
        request_id=ride.request_id,
        status=ride.status.value,
        passenger_id=str(ride.passenger_id),
        driver_id=str(ride.driver_id) if ride.driver_id else None,
        pickup_lat=ride.pickup_lat,
        pickup_lon=ride.pickup_lon,
        dropoff_lat=ride.dropoff_lat,
        dropoff_lon=ride.dropoff_lon,
        pickup_address=ride.pickup_address,
        dropoff_address=ride.dropoff_address,
        vehicle_type=ride.vehicle_type,
        city_code=ride.city_code,
        estimated_fare=ride.fare_amount,  # optionally set from realtime
        created_at=ride.created_at,
        assigned_at=ride.assigned_at,
        cancelled_by=ride.cancelled_by,
        cancellation_reason=ride.cancellation_reason,
    )


@router.patch("/{request_id}/status", response_model=RideStatusResponse)
def update_ride_status(
    request_id: str,
    body: RideStatusUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(_verify_internal_key),
):
    """Update ride status (assigned, in_progress, completed). Realtime calls after assign/start/complete."""
    ride = db.query(Ride).filter(Ride.request_id == request_id).first()
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")

    try:
        ride.status = RideStatusEnum(body.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    if body.driver_id:
        ride.driver_id = uuid.UUID(body.driver_id)
    if body.status == "assigned":
        ride.assigned_at = datetime.utcnow()
    elif body.status == "in_progress":
        ride.started_at = datetime.utcnow()
    elif body.status == "completed":
        ride.completed_at = datetime.utcnow()
    if body.distance_km is not None:
        ride.distance_km = body.distance_km
    if body.duration_minutes is not None:
        ride.duration_minutes = body.duration_minutes
    if body.fare_amount is not None:
        ride.fare_amount = body.fare_amount

    db.commit()
    db.refresh(ride)

    return RideStatusResponse(
        request_id=ride.request_id,
        status=ride.status.value,
        passenger_id=str(ride.passenger_id),
        driver_id=str(ride.driver_id) if ride.driver_id else None,
        pickup_lat=ride.pickup_lat,
        pickup_lon=ride.pickup_lon,
        dropoff_lat=ride.dropoff_lat,
        dropoff_lon=ride.dropoff_lon,
        pickup_address=ride.pickup_address,
        dropoff_address=ride.dropoff_address,
        vehicle_type=ride.vehicle_type,
        city_code=ride.city_code,
        created_at=ride.created_at,
        assigned_at=ride.assigned_at,
        cancelled_by=ride.cancelled_by,
        cancellation_reason=ride.cancellation_reason,
    )


@router.post("/{request_id}/cancel", response_model=RideStatusResponse)
def cancel_ride(
    request_id: str,
    body: RideCancel,
    db: Session = Depends(get_db),
    _: bool = Depends(_verify_internal_key),
):
    """Cancel a ride. Realtime calls this then cleans up Redis/WS."""
    ride = db.query(Ride).filter(Ride.request_id == request_id).first()
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found")

    if ride.status not in (RideStatusEnum.pending, RideStatusEnum.assigned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ride cannot be cancelled in current status",
        )

    ride.status = RideStatusEnum.cancelled
    ride.cancelled_at = datetime.utcnow()
    ride.cancelled_by = body.cancelled_by
    ride.cancellation_reason = body.cancellation_reason

    db.commit()
    db.refresh(ride)

    return RideStatusResponse(
        request_id=ride.request_id,
        status=ride.status.value,
        passenger_id=str(ride.passenger_id),
        driver_id=str(ride.driver_id) if ride.driver_id else None,
        pickup_lat=ride.pickup_lat,
        pickup_lon=ride.pickup_lon,
        dropoff_lat=ride.dropoff_lat,
        dropoff_lon=ride.dropoff_lon,
        pickup_address=ride.pickup_address,
        dropoff_address=ride.dropoff_address,
        vehicle_type=ride.vehicle_type,
        city_code=ride.city_code,
        created_at=ride.created_at,
        assigned_at=ride.assigned_at,
        cancelled_by=ride.cancelled_by,
        cancellation_reason=ride.cancellation_reason,
    )
