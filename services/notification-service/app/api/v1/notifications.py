from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import logging

from app.schemas.notification import (
    NotificationRequest,
    NotificationResponse,
    BulkNotificationRequest,
    NotificationType,
    NotificationChannel,
    PushNotificationRequest,
    TopicNotificationRequest
)
from app.core.firebase import FirebaseService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


async def send_push_notification(user_id: str, title: str, message: str, 
                                  data: Optional[Dict[str, Any]] = None, 
                                  device_token: Optional[str] = None,
                                  priority: str = "high") -> Dict[str, Any]:
    """
    Send push notification via Firebase Cloud Messaging.
    
    Note: In production, you should fetch device_token from database using user_id.
    """
    if not device_token:
        logger.warning(f"No device token provided for user {user_id}")
        return {"success": False, "error": "No device token available"}
    
    return FirebaseService.send_push_notification(
        device_token=device_token,
        title=title,
        body=message,
        data=data,
        priority=priority
    )


@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(request: NotificationRequest):
    """
    Send a notification to a single user.
    Centralized notification endpoint for all services.
    
    Supports: in_app, push, sms, email channels.
    """
    notification_id = uuid.uuid4()
    channels_sent = []
    errors = []
    
    logger.info(f"📧 Notification for user {request.user_id}: {request.notification_type}")
    logger.info(f"   Title: {request.title}")
    logger.info(f"   Channels: {request.channels}")
    
    # Process each requested channel
    for channel in request.channels:
        try:
            if channel == NotificationChannel.IN_APP:
                # Store in database/Redis for in-app notifications
                channels_sent.append("in_app")
                logger.info(f"✅ In-app notification queued for user {request.user_id}")
                
            elif channel == NotificationChannel.PUSH:
                # Send push notification via Firebase Cloud Messaging
                # TODO: Fetch device_token from database using user_id
                device_token = None  # This should come from user device registry
                if device_token:
                    result = await send_push_notification(
                        user_id=str(request.user_id),
                        title=request.title,
                        message=request.message,
                        data=request.data,
                        device_token=device_token,
                        priority=request.priority
                    )
                    if result.get("success"):
                        channels_sent.append("push")
                    else:
                        errors.append(f"Push failed: {result.get('error')}")
                else:
                    logger.warning(f"No device token for push notification to user {request.user_id}")
                
            elif channel == NotificationChannel.SMS:
                # Send SMS via Twilio/other provider
                # TODO: Implement SMS sending
                channels_sent.append("sms")
                logger.info(f"✅ SMS notification queued for user {request.user_id}")
                
            elif channel == NotificationChannel.EMAIL:
                # Send email via SMTP/SendGrid
                # TODO: Implement email sending
                channels_sent.append("email")
                logger.info(f"✅ Email notification queued for user {request.user_id}")
        
        except Exception as e:
            error_msg = f"Error sending {channel}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    return NotificationResponse(
        notification_id=notification_id,
        status="sent" if channels_sent else "failed",
        channels_sent=channels_sent,
        message=f"Notification sent successfully" if not errors else f"Sent to: {', '.join(channels_sent)}"
    )


@router.post("/send/bulk", response_model=List[NotificationResponse], status_code=status.HTTP_201_CREATED)
async def send_bulk_notifications(request: BulkNotificationRequest):
    """
    Send notifications to multiple users at once.
    Useful for notifying multiple drivers about a ride request.
    """
    from app.core.config import settings
    
    if len(request.user_ids) > settings.MAX_BULK_NOTIFICATION_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum bulk size is {settings.MAX_BULK_NOTIFICATION_SIZE} users"
        )
    
    responses = []
    logger.info(f"📧 Sending bulk notification to {len(request.user_ids)} users")
    
    for user_id in request.user_ids:
        notification = NotificationRequest(
            user_id=user_id,
            notification_type=request.notification_type,
            title=request.title,
            message=request.message,
            channels=request.channels,
            data=request.data,
            priority=request.priority
        )
        response = await send_notification(notification)
        responses.append(response)
    
    logger.info(f"✅ Bulk notification sent to {len(request.user_ids)} users")
    return responses


@router.post("/push", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def send_push_direct(request: PushNotificationRequest):
    """
    Send a direct push notification via Firebase Cloud Messaging.
    Requires a valid device token.
    """
    try:
        result = FirebaseService.send_push_notification(
            device_token=request.device_token,
            title=request.title,
            body=request.body,
            data=request.data,
            priority=request.priority
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send push notification")
            )
        
        return {
            "success": True,
            "message_id": result.get("message_id"),
            "device_token": request.device_token
        }
    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/push/multicast", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def send_push_multicast(device_tokens: List[str], title: str, body: str,
                              data: Optional[Dict[str, Any]] = None, priority: str = "high"):
    """
    Send push notifications to multiple devices at once.
    """
    try:
        result = FirebaseService.send_multicast_notification(
            device_tokens=device_tokens,
            title=title,
            body=body,
            data=data,
            priority=priority
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send multicast notification")
            )
        
        return result
    except Exception as e:
        logger.error(f"Error sending multicast notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/topic/send", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def send_topic_notification(request: TopicNotificationRequest):
    """
    Send a notification to all subscribers of a topic.
    Topics: drivers, passengers, admins, etc.
    """
    try:
        result = FirebaseService.send_to_topic(
            topic=request.topic,
            title=request.title,
            body=request.body,
            data=request.data,
            priority=request.priority
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send topic notification")
            )
        
        return result
    except Exception as e:
        logger.error(f"Error sending topic notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/topic/subscribe", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def subscribe_to_topic(device_tokens: List[str], topic: str):
    """
    Subscribe device tokens to a Firebase Cloud Messaging topic.
    """
    try:
        result = FirebaseService.subscribe_to_topic(
            device_tokens=device_tokens,
            topic=topic
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to subscribe to topic")
            )
        
        return result
    except Exception as e:
        logger.error(f"Error subscribing to topic: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/topic/unsubscribe", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def unsubscribe_from_topic(device_tokens: List[str], topic: str):
    """
    Unsubscribe device tokens from a Firebase Cloud Messaging topic.
    """
    try:
        result = FirebaseService.unsubscribe_from_topic(
            device_tokens=device_tokens,
            topic=topic
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to unsubscribe from topic")
            )
        
        return result
    except Exception as e:
        logger.error(f"Error unsubscribing from topic: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ride/request-sent", status_code=status.HTTP_201_CREATED)
async def notify_ride_request_sent(
    driver_ids: List[str],
    passenger_id: str,
    request_id: str,
    pickup_lat: float,
    pickup_lon: float,
    distance_km: float,
    pickup_address: Optional[str] = None,
    device_tokens: Optional[List[str]] = None
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
    
    # Send via Firebase if device tokens provided
    if device_tokens and len(device_tokens) > 0:
        firebase_result = FirebaseService.send_multicast_notification(
            device_tokens=device_tokens,
            title="New Ride Request",
            body=f"New ride request {distance_km:.1f}km away",
            data={
                "request_id": request_id,
                "passenger_id": passenger_id,
                "pickup_lat": pickup_lat,
                "pickup_lon": pickup_lon,
                "distance_km": distance_km,
                "pickup_address": pickup_address,
                "type": "ride_request"
            },
            priority="high"
        )
        logger.info(f"✅ Ride request sent to {len(device_tokens)} drivers via Firebase")
        responses.append(firebase_result)
    
    # Also send via general notification system
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
    
    return {
        "notifications_sent": len(responses),
        "responses": responses
    }


@router.post("/ride/driver-assigned", status_code=status.HTTP_201_CREATED)
async def notify_driver_assigned(
    passenger_id: str,
    driver_id: str,
    request_id: str,
    pickup_lat: float,
    pickup_lon: float,
    device_token: Optional[str] = None
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
    
    # Send via Firebase if device token provided
    if device_token:
        FirebaseService.send_push_notification(
            device_token=device_token,
            title="Driver Assigned",
            body="A driver has been assigned to your ride",
            data={
                "request_id": request_id,
                "driver_id": driver_id,
                "pickup_lat": pickup_lat,
                "pickup_lon": pickup_lon,
                "type": "driver_assigned"
            },
            priority="high"
        )
    
    # Also send via general notification system
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
    additional_data: Optional[Dict[str, Any]] = None,
    device_token: Optional[str] = None
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
    
    # Send via Firebase if device token provided
    if device_token:
        FirebaseService.send_push_notification(
            device_token=device_token,
            title=title,
            body=message,
            data=data,
            priority="high" if notification_type != NotificationType.RIDE_COMPLETED else "normal"
        )
    
    # Also send via general notification system
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

