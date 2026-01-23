from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.models import SOSStatus


class SOSTriggerRequest(BaseModel):
    """Request to trigger SOS."""
    # Optional: if not provided, will fetch from Redis (live location)
    latitude: Optional[float] = Field(None, description="Current latitude (optional, will use live location if not provided)")
    longitude: Optional[float] = Field(None, description="Current longitude (optional, will use live location if not provided)")
    address: Optional[str] = Field(None, description="Optional address string")
    notes: Optional[str] = Field(None, description="Optional notes about the emergency")


class SOSResponse(BaseModel):
    """SOS request response."""
    id: UUID
    user_id: UUID
    latitude: float
    longitude: float
    address: Optional[str]
    emergency_number: str
    status: str
    triggered_at: datetime
    map_link: str
    
    class Config:
        from_attributes = True


class SOSHistoryResponse(BaseModel):
    """SOS history response."""
    id: UUID
    latitude: float
    longitude: float
    address: Optional[str]
    emergency_number: str
    status: str
    triggered_at: datetime
    resolved_at: Optional[datetime]
    contacts_notified_count: int
    
    class Config:
        from_attributes = True


class EmergencyContactCreate(BaseModel):
    """Create emergency contact."""
    name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    priority: int = Field(5, ge=1, le=5, description="Priority 1-5 (1 is highest)")
    
    # Note: user_id will be set from authenticated user


class EmergencyContactResponse(BaseModel):
    """Emergency contact response."""
    id: UUID
    user_id: UUID
    name: str
    phone: Optional[str]
    email: Optional[str]
    priority: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmergencyContactUpdate(BaseModel):
    """Update emergency contact."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    priority: Optional[int] = Field(None, ge=1, le=5)
    is_active: Optional[bool] = None


class EmergencyNumberResponse(BaseModel):
    """Emergency number response."""
    number: str
    description: Optional[str]
    country_code: Optional[str]


class EmergencyNumberUpdate(BaseModel):
    """Update emergency number (admin only)."""
    number: str = Field(..., min_length=3, max_length=20)
    description: Optional[str] = None
    country_code: Optional[str] = None
