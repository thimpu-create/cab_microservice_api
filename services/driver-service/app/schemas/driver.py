from pydantic import BaseModel, field_validator, model_validator
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
    """
    Schema for creating a driver.
    
    Two modes:
    1. Link existing user: Provide `user_id` only
    2. Create new user: Provide `fname`, `lname`, `email`, `phone`, `password` (user_id will be auto-created)
    
    Note: `company_id` comes from URL path, not body.
    """
    # Mode 1: Link existing user (provide user_id)
    user_id: Optional[UUID] = None
    
    # Mode 2: Create new user (provide these fields, user_id will be auto-created)
    fname: Optional[str] = None
    mname: Optional[str] = None
    lname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_user_info(self):
        """Ensure either user_id OR user creation fields are provided"""
        has_user_id = self.user_id is not None
        has_user_details = all([
            self.fname,
            self.lname,
            self.email,
            self.phone,
            self.password
        ])
        
        if not has_user_id and not has_user_details:
            raise ValueError(
                "Either provide 'user_id' (to link existing user) OR provide "
                "'fname', 'lname', 'email', 'phone', 'password' (to create new user)"
            )
        
        if has_user_id and has_user_details:
            raise ValueError(
                "Provide either 'user_id' OR user creation fields, not both"
            )
        
        return self


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
