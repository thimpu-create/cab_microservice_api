from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class DriverRegistrationRequest(BaseModel):
    """Schema for driver registration request."""
    # Mode 1: Link existing user
    user_id: Optional[UUID] = None
    
    # Mode 2: Create new user
    fname: Optional[str] = None
    mname: Optional[str] = None
    lname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    
    # Driver fields (all optional)
    license_number: Optional[str] = None
    license_expiry_date: Optional[datetime] = None
    license_state_province: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_color: Optional[str] = None
    vehicle_plate_number: Optional[str] = None
    notes: Optional[str] = None
