from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.models import VehicleType


class FareCalculationRequest(BaseModel):
    """Request to calculate fare."""
    pickup_lat: float = Field(..., description="Pickup latitude")
    pickup_lon: float = Field(..., description="Pickup longitude")
    dropoff_lat: float = Field(..., description="Dropoff latitude")
    dropoff_lon: float = Field(..., description="Dropoff longitude")
    vehicle_type: VehicleType = Field(..., description="Vehicle type")
    city_code: str = Field(..., min_length=2, max_length=10, description="City code (e.g., MUM, DEL)")
    driver_id: Optional[UUID] = Field(None, description="Driver ID (will fetch company_id to determine pricing type)")
    company_id: Optional[UUID] = Field(None, description="Company ID (optional, will be fetched from driver if not provided)")
    estimated_distance_km: Optional[float] = Field(None, description="Estimated distance (will be calculated if not provided)")
    estimated_duration_minutes: Optional[float] = Field(None, description="Estimated duration (will be calculated if not provided)")


class FareCalculationResponse(BaseModel):
    """Response with detailed fare breakdown."""
    base_fare: float
    distance_cost: float
    time_cost: float
    subtotal: float
    peak_multiplier: float
    peak_adjusted_subtotal: float
    surge_multiplier: float
    surge_adjusted_subtotal: float
    minimum_fare: float
    regulatory_cap: Optional[float]
    final_fare: float
    currency: str
    breakdown: dict
    metadata: dict


class PricingProfileCreate(BaseModel):
    """Create pricing profile.
    company_id should be NULL for platform pricing (admin), or specific company_id for company pricing (VendorAdmin).
    """
    city_code: str
    state_code: Optional[str] = None
    vehicle_type: VehicleType
    base_fare: float = Field(..., gt=0)
    per_km_rate: float = Field(..., gt=0)
    per_minute_rate: float = Field(..., gt=0)
    minimum_fare: float = Field(..., gt=0)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    # Note: company_id will be set automatically based on user role (admin = NULL, VendorAdmin = their company_id)


class PricingProfileResponse(BaseModel):
    """Pricing profile response."""
    id: UUID
    company_id: Optional[UUID]  # NULL = platform pricing, NOT NULL = company pricing
    city_code: str
    state_code: Optional[str]
    vehicle_type: str
    base_fare: float
    per_km_rate: float
    per_minute_rate: float
    minimum_fare: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SurgeConfigUpdate(BaseModel):
    """Update surge configuration."""
    base_demand_threshold: Optional[float] = Field(None, gt=0)
    max_surge_multiplier: Optional[float] = Field(None, gt=1.0)
    surge_increment: Optional[float] = Field(None, gt=0)


class SurgeConfigResponse(BaseModel):
    """Surge configuration response."""
    company_id: Optional[UUID]  # NULL = platform, NOT NULL = company
    vehicle_type: str
    base_demand_threshold: float
    max_surge_multiplier: float
    surge_increment: float
    is_active: bool
    
    class Config:
        from_attributes = True
