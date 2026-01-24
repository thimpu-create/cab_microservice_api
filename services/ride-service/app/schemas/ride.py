"""
Ride domain schemas. VehicleType and RideRequest live here—ride-service owns them.
"""
from enum import Enum
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class VehicleType(str, Enum):
    """Vehicle types passengers can request. Must match driver-service."""
    bike = "bike"
    car = "car"
    auto = "auto"
    premium_car = "premium_car"


class RideRequestCreate(BaseModel):
    """Payload for creating a ride request (internal: realtime -> ride-service)."""
    passenger_id: str
    lat: float = Field(..., description="Pickup latitude")
    lon: float = Field(..., description="Pickup longitude")
    pickup_address: Optional[str] = None
    dropoff_address: Optional[str] = None
    dropoff_lat: Optional[float] = None
    dropoff_lon: Optional[float] = None
    vehicle_type_preference: Optional[VehicleType] = Field(
        None,
        description="bike, car, auto, premium_car. None = any",
    )
    min_driver_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    city_code: Optional[str] = None


class RideCreateResponse(BaseModel):
    request_id: str
    status: str = "pending"
    passenger_id: str
    pickup_lat: float
    pickup_lon: float
    dropoff_lat: Optional[float] = None
    dropoff_lon: Optional[float] = None
    pickup_address: Optional[str] = None
    dropoff_address: Optional[str] = None
    vehicle_type: Optional[str] = None
    city_code: Optional[str] = None
    created_at: Optional[datetime] = None


class RideStatusUpdate(BaseModel):
    status: str = Field(..., description="assigned | in_progress | completed")
    driver_id: Optional[str] = None
    distance_km: Optional[float] = None
    duration_minutes: Optional[int] = None
    fare_amount: Optional[float] = None


class RideCancel(BaseModel):
    cancelled_by: str = Field(..., description="passenger | driver")
    cancellation_reason: Optional[str] = None


class RideStatusResponse(BaseModel):
    request_id: str
    status: str
    passenger_id: Optional[str] = None
    driver_id: Optional[str] = None
    pickup_lat: Optional[float] = None
    pickup_lon: Optional[float] = None
    dropoff_lat: Optional[float] = None
    dropoff_lon: Optional[float] = None
    pickup_address: Optional[str] = None
    dropoff_address: Optional[str] = None
    vehicle_type: Optional[str] = None
    city_code: Optional[str] = None
    estimated_fare: Optional[float] = None
    fare_breakdown: Optional[dict] = None
    created_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None


class RideHistoryItem(BaseModel):
    """Single ride for history list."""
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


class RideHistoryStats(BaseModel):
    total_rides: int
    completed_rides: int
    cancelled_rides: int
    total_distance_km: float
    total_earnings: Optional[float] = None
