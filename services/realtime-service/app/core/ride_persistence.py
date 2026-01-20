"""
Ride persistence module - saves completed/cancelled rides to database.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.db.models import Ride, RideStatus as DBRideStatus
from app.core.ride_manager import RideStatus


def save_ride_to_db(
    db: Session,
    request_id: str,
    passenger_id: str,
    pickup_lat: float,
    pickup_lon: float,
    status: str,
    driver_id: Optional[str] = None,
    dropoff_lat: Optional[float] = None,
    dropoff_lon: Optional[float] = None,
    pickup_address: Optional[str] = None,
    dropoff_address: Optional[str] = None,
    created_at: Optional[float] = None,
    assigned_at: Optional[float] = None,
    started_at: Optional[float] = None,
    completed_at: Optional[float] = None,
    cancelled_at: Optional[float] = None,
    cancelled_by: Optional[str] = None,
    cancellation_reason: Optional[str] = None,
    distance_km: Optional[float] = None,
    duration_minutes: Optional[int] = None,
    fare_amount: Optional[float] = None,
) -> Ride:
    """
    Save or update a ride in the database.
    """
    # Check if ride already exists
    existing_ride = db.query(Ride).filter(Ride.request_id == request_id).first()
    
    # Map status from string to enum
    status_map = {
        RideStatus.PENDING: DBRideStatus.pending,
        RideStatus.ASSIGNED: DBRideStatus.assigned,
        RideStatus.IN_PROGRESS: DBRideStatus.in_progress,
        RideStatus.COMPLETED: DBRideStatus.completed,
        RideStatus.CANCELLED: DBRideStatus.cancelled,
        RideStatus.EXPIRED: DBRideStatus.expired,
        RideStatus.REJECTED: DBRideStatus.rejected,
    }
    db_status = status_map.get(status, DBRideStatus.pending)
    
    # Convert timestamps
    def timestamp_to_datetime(ts: Optional[float]) -> Optional[datetime]:
        if ts is None:
            return None
        return datetime.fromtimestamp(float(ts))
    
    if existing_ride:
        # Update existing ride
        existing_ride.status = db_status
        existing_ride.driver_id = UUID(driver_id) if driver_id else None
        existing_ride.dropoff_lat = dropoff_lat
        existing_ride.dropoff_lon = dropoff_lon
        existing_ride.dropoff_address = dropoff_address
        existing_ride.assigned_at = timestamp_to_datetime(assigned_at)
        existing_ride.started_at = timestamp_to_datetime(started_at)
        existing_ride.completed_at = timestamp_to_datetime(completed_at)
        existing_ride.cancelled_at = timestamp_to_datetime(cancelled_at)
        existing_ride.cancelled_by = cancelled_by
        existing_ride.cancellation_reason = cancellation_reason
        existing_ride.distance_km = distance_km
        existing_ride.duration_minutes = duration_minutes
        existing_ride.fare_amount = fare_amount
        
        db.commit()
        db.refresh(existing_ride)
        return existing_ride
    else:
        # Create new ride
        ride = Ride(
            request_id=request_id,
            passenger_id=UUID(passenger_id),
            driver_id=UUID(driver_id) if driver_id else None,
            pickup_lat=pickup_lat,
            pickup_lon=pickup_lon,
            pickup_address=pickup_address,
            dropoff_lat=dropoff_lat,
            dropoff_lon=dropoff_lon,
            dropoff_address=dropoff_address,
            status=db_status,
            created_at=timestamp_to_datetime(created_at) if created_at else datetime.utcnow(),
            assigned_at=timestamp_to_datetime(assigned_at),
            started_at=timestamp_to_datetime(started_at),
            completed_at=timestamp_to_datetime(completed_at),
            cancelled_at=timestamp_to_datetime(cancelled_at),
            cancelled_by=cancelled_by,
            cancellation_reason=cancellation_reason,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            fare_amount=fare_amount,
        )
        
        db.add(ride)
        db.commit()
        db.refresh(ride)
        return ride


def calculate_ride_duration(started_at: Optional[float], completed_at: Optional[float]) -> Optional[int]:
    """Calculate ride duration in minutes."""
    if not started_at or not completed_at:
        return None
    
    duration_seconds = float(completed_at) - float(started_at)
    return int(duration_seconds / 60)
