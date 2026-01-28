"""
Pydantic models for device management.
"""
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    """Supported platforms."""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class DeviceRegisterRequest(BaseModel):
    """Request to register a device."""
    user_id: UUID
    device_token: str  # FCM token from Firebase
    device_name: Optional[str] = None  # e.g., "iPhone 15", "Samsung S24"
    platform: Platform  # ios, android, web


class DeviceResponse(BaseModel):
    """Response with device information."""
    id: UUID
    user_id: UUID
    device_name: Optional[str]
    platform: str
    is_active: bool
    created_at: datetime
    last_heartbeat: datetime

    class Config:
        from_attributes = True


class UserDevicesResponse(BaseModel):
    """Response with user's devices."""
    user_id: UUID
    device_count: int
    devices: List[DeviceResponse]


class DeviceTokensResponse(BaseModel):
    """Response with device tokens for Firebase."""
    user_id: UUID
    token_count: int
    tokens: List[str]
    platform: Optional[str] = None
