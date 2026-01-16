from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class RideRequest(BaseModel):
    passenger_id: str  # UUID as string
    lat: float
    lon: float
    pickup_address: Optional[str] = None
    dropoff_address: Optional[str] = None
    dropoff_lat: Optional[float] = None
    dropoff_lon: Optional[float] = None


class LocationUpdate(BaseModel):
    lat: float
    lon: float
    status: Optional[str] = "available"  # available, busy, offline


class AcceptRideRequest(BaseModel):
    type: str = "accept_ride"
    request_id: str


class CompleteRideRequest(BaseModel):
    type: str = "completed_ride"
    request_id: str
