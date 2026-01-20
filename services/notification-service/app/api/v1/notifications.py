from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.schemas.notification import (
    NotificationRequest,
    NotificationResponse,
    BulkNotificationRequest,
    NotificationType,
    NotificationChannel
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(request: NotificationRequest):
    """
    Send a notification to a single user.
    Centralized notification endpoint for all services.
    """
    notification_id = uuid.uuid4()
    
    # Log the notification (in production, this would send via actual channels)
    print(f"📧 Notification sent: {request.notification_type} to user {request.user_id}")
    print(f"   Title: {request.title}")
    print(f"   Message: {request.message}")
    print(f"   Channels: {request.channels}")
    
    # In a real implementation, you would:
    # 1. Save notification to database
    # 2. Send push notification if channel includes "push"
    # 3. Send SMS if channel includes "sms"
    # 4. Send email if channel includes "email"
    # 5. Store in-app notification
    
    # For now, simulate successful sending
    channels_sent = []
    for channel in request.channels:
        # Simulate sending to each channel
        if channel == NotificationChannel.IN_APP:
            channels_sent.append("in_app")
            # Store in database/Redis for in-app notifications
        elif channel == NotificationChannel.PUSH:
            channels_sent.append("push")
            # Send push notification via FCM/APNS
        elif channel == NotificationChannel.SMS:
            channels_sent.append("sms")
            # Send SMS via Twilio/other provider
        elif channel == NotificationChannel.EMAIL:
            channels_sent.append("email")
            # Send email via SMTP/SendGrid
    
    return NotificationResponse(
        notification_id=notification_id,
        status="sent",
        channels_sent=channels_sent,
        message="Notification sent successfully"
    )


@router.post("/send/bulk", response_model=List[NotificationResponse], status_code=status.HTTP_201_CREATED)
async def send_bulk_notifications(request: BulkNotificationRequest):
    """
    Send notifications to multiple users at once.
    Useful for notifying multiple drivers about a ride request.
    """
    responses = []
    
    for user_id in request.user_ids:
        notification_id = uuid.uuid4()
        
        print(f"📧 Bulk notification sent: {request.notification_type} to user {user_id}")
        
        # Simulate sending (same logic as single notification)
        channels_sent = []
        for channel in request.channels:
            if channel == NotificationChannel.IN_APP:
                channels_sent.append("in_app")
            elif channel == NotificationChannel.PUSH:
                channels_sent.append("push")
            elif channel == NotificationChannel.SMS:
                channels_sent.append("sms")
            elif channel == NotificationChannel.EMAIL:
                channels_sent.append("email")
        
        responses.append(NotificationResponse(
            notification_id=notification_id,
            status="sent",
            channels_sent=channels_sent,
            message="Notification sent successfully"
        ))
    
    return responses


@router.post("/ride/request-sent", status_code=status.HTTP_201_CREATED)
async def notify_ride_request_sent(
    driver_ids: List[str],
    passenger_id: str,
    request_id: str,
    pickup_lat: float,
    pickup_lon: float,
    distance_km: float,
    pickup_address: Optional[str] = None
):
    """
    Specialized endpoint for ride request notifications.
    Notifies multiple drivers about a new ride request.
    """
    from uuid import UUID
    
    try:
        driver_uuids = [UUID(driver_id) for driver_id in driver_ids]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid driver ID format"
        )
    
    responses = []
    for driver_id in driver_uuids:
        notification = NotificationRequest(
            user_id=driver_id,
            notification_type=NotificationType.RIDE_REQUEST,
            title="New Ride Request",
            message=f"New ride request {distance_km:.1f}km away",
            channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH],
            data={
                "request_id": request_id,
                "passenger_id": passenger_id,
                "pickup_lat": pickup_lat,
                "pickup_lon": pickup_lon,
                "distance_km": distance_km,
                "pickup_address": pickup_address
            },
            priority="high"
        )
        
        response = await send_notification(notification)
        responses.append(response)
    
    return {"notifications_sent": len(responses), "responses": responses}


@router.post("/ride/driver-assigned", status_code=status.HTTP_201_CREATED)
async def notify_driver_assigned(
    passenger_id: str,
    driver_id: str,
    request_id: str,
    pickup_lat: float,
    pickup_lon: float
):
    """
    Notify passenger that a driver has been assigned.
    """
    from uuid import UUID
    
    try:
        passenger_uuid = UUID(passenger_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid passenger ID format"
        )
    
    notification = NotificationRequest(
        user_id=passenger_uuid,
        notification_type=NotificationType.DRIVER_ASSIGNED,
        title="Driver Assigned",
        message="A driver has been assigned to your ride",
        channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH],
        data={
            "request_id": request_id,
            "driver_id": driver_id,
            "pickup_lat": pickup_lat,
            "pickup_lon": pickup_lon
        },
        priority="high"
    )
    
    return await send_notification(notification)


@router.post("/ride/status-update", status_code=status.HTTP_201_CREATED)
async def notify_ride_status_update(
    user_id: str,
    notification_type: NotificationType,
    request_id: str,
    title: str,
    message: str,
    additional_data: Optional[Dict[str, Any]] = None
):
    """
    Generic endpoint for ride status updates (started, completed, cancelled, expired).
    """
    from uuid import UUID
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    data = {"request_id": request_id}
    if additional_data:
        data.update(additional_data)
    
    notification = NotificationRequest(
        user_id=user_uuid,
        notification_type=notification_type,
        title=title,
        message=message,
        channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH],
        data=data,
        priority="normal" if notification_type == NotificationType.RIDE_COMPLETED else "high"
    )
    
    return await send_notification(notification)
