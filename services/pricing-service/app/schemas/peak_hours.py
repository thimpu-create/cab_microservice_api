from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class PeakHoursCreate(BaseModel):
    """Create peak hours definition."""
    city_code: str
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="0=Monday, 6=Sunday, None=all days")
    start_time: str = Field(..., regex=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="HH:MM format (24-hour)")
    end_time: str = Field(..., regex=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="HH:MM format (24-hour)")
    multiplier: float = Field(..., gt=1.0, description="Multiplier during peak hours (e.g., 1.2 = 20% surcharge)")


class PeakHoursResponse(BaseModel):
    """Peak hours response."""
    id: UUID
    company_id: Optional[UUID]
    city_code: str
    day_of_week: Optional[int]
    start_time: str
    end_time: str
    multiplier: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
