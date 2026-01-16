from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.db.models import DriverStatus


class DriverBase(BaseModel):
    license_number: Optional[str] = None
    license_expiry_date: Optional[datetime] = None
    license_state_province: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_color: Optional[str] = None
    vehicle_plate_number: Optional[str] = None
    notes: Optional[str] = None


class DriverCreate(DriverBase):
    # User information (will create account in auth-service if user_id not provided)
    user_id: Optional[UUID] = None  # If provided, use existing user
    # If user_id not provided, create new user with these fields:
    fname: Optional[str] = None
    mname: Optional[str] = None
    lname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class DriverUpdate(BaseModel):
    license_number: Optional[str] = None
    license_expiry_date: Optional[datetime] = None
    license_state_province: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_color: Optional[str] = None
    vehicle_plate_number: Optional[str] = None
    status: Optional[DriverStatus] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class DriverResponse(DriverBase):
    id: UUID
    user_id: UUID
    company_id: Optional[UUID]
    status: DriverStatus
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class DriverCountResponse(BaseModel):
    company_id: UUID
    total_drivers: int
    active_drivers: int
    inactive_drivers: int
    pending_verification: int
