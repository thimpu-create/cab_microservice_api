from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications."""
    RIDE_REQUEST = "ride_request"
    DRIVER_ASSIGNED = "driver_assigned"
    RIDE_STARTED = "ride_started"
    RIDE_COMPLETED = "ride_completed"
    RIDE_CANCELLED = "ride_cancelled"
    RIDE_EXPIRED = "ride_expired"
    DRIVER_LOCATION_UPDATE = "driver_location_update"
    RIDE_STATUS_UPDATE = "ride_status_update"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"


class NotificationRequest(BaseModel):
    """Request to send a notification."""
    user_id: UUID  # Recipient user ID
    notification_type: NotificationType
    title: str
    message: str
    channels: list[NotificationChannel] = [NotificationChannel.IN_APP]  # Default to in-app
    data: Optional[Dict[str, Any]] = None  # Additional data (ride_id, driver_id, etc.)
    priority: str = "normal"  # normal, high, urgent


class NotificationResponse(BaseModel):
    """Response from notification service."""
    notification_id: UUID
    status: str  # sent, failed, pending
    channels_sent: list[str]
    message: Optional[str] = None


class BulkNotificationRequest(BaseModel):
    """Request to send notifications to multiple users."""
    user_ids: list[UUID]
    notification_type: NotificationType
    title: str
    message: str
    channels: list[NotificationChannel] = [NotificationChannel.IN_APP]
    data: Optional[Dict[str, Any]] = None
    priority: str = "normal"
