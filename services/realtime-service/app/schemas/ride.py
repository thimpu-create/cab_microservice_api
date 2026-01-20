from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class VehicleType(str):
    """Vehicle type preference - extensible for future additions."""
    BIKE = "bike"
    CAR = "car"
    AUTO = "auto"
    PREMIUM_CAR = "premium_car"


class RideRequest(BaseModel):
    passenger_id: str  # UUID as string
    lat: float
    lon: float
    pickup_address: Optional[str] = None
    dropoff_address: Optional[str] = None
    dropoff_lat: Optional[float] = None
    dropoff_lon: Optional[float] = None
    vehicle_type_preference: Optional[str] = None  # bike, car, auto, premium_car - None means no preference
    min_driver_rating: Optional[float] = None  # Minimum driver rating (1.0-5.0)


class LocationUpdate(BaseModel):
    lat: float
    lon: float
    status: Optional[str] = "available"  # available, busy, offline


class AcceptRideRequest(BaseModel):
    type: str = "accept_ride"
    request_id: str


class RejectRideRequest(BaseModel):
    type: str = "reject_ride"
    request_id: str
    reason: Optional[str] = None


class CancelRideRequest(BaseModel):
    type: str = "cancel_ride"
    request_id: str
    reason: Optional[str] = None


class CompleteRideRequest(BaseModel):
    type: str = "completed_ride"
    request_id: str


class UpdateRideStatusRequest(BaseModel):
    type: str = "update_ride_status"
    request_id: str
    status: str  # "in_progress" or "completed"
