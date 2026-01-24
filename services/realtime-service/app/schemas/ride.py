from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID
from enum import Enum


class VehicleType(str, Enum):
    """Vehicle types that passengers can request.
    This is the source of truth for ride requests.
    Must match what drivers register in driver-service.
    """
    bike = "bike"
    car = "car"
    auto = "auto"  # Auto-rickshaw
    premium_car = "premium_car"


class RideRequest(BaseModel):
    """Passenger ride request - passenger specifies vehicle type preference here."""
    passenger_id: str  # UUID as string
    lat: float = Field(..., description="Pickup latitude")
    lon: float = Field(..., description="Pickup longitude")
    pickup_address: Optional[str] = None
    dropoff_address: Optional[str] = None
    dropoff_lat: Optional[float] = Field(None, description="Dropoff latitude (required for fare estimate)")
    dropoff_lon: Optional[float] = Field(None, description="Dropoff longitude (required for fare estimate)")
    vehicle_type_preference: Optional[VehicleType] = Field(
        None, 
        description="Vehicle type preference: bike, car, auto, premium_car. None = any vehicle type"
    )
    min_driver_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Minimum driver rating (1.0-5.0)")
    city_code: Optional[str] = Field(None, description="City code (e.g. MUM, DEL) - for fare estimate, default: MUM")


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
