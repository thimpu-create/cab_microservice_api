from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class DriverRatingCreate(BaseModel):
    """Schema for creating a driver rating."""
    driver_id: UUID
    passenger_id: UUID
    ride_id: Optional[UUID] = None
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating from 1.0 to 5.0")
    comment: Optional[str] = None
    
    # Optional detailed ratings
    punctuality_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    driving_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    vehicle_condition_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    communication_rating: Optional[float] = Field(None, ge=1.0, le=5.0)


class DriverRatingResponse(BaseModel):
    """Schema for driver rating response."""
    id: UUID
    driver_id: UUID
    passenger_id: UUID
    ride_id: Optional[UUID]
    rating: float
    comment: Optional[str]
    punctuality_rating: Optional[float] = None
    driving_rating: Optional[float] = None
    vehicle_condition_rating: Optional[float] = None
    communication_rating: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DriverRatingStats(BaseModel):
    """Schema for driver rating statistics."""
    driver_id: UUID
    average_rating: float
    total_ratings: int
    rating_distribution: dict  # {1: count, 2: count, 3: count, 4: count, 5: count}
    average_punctuality: Optional[float] = None
    average_driving: Optional[float] = None
    average_vehicle_condition: Optional[float] = None
    average_communication: Optional[float] = None
