"""
Device management endpoints for registering and managing user devices.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
import logging

from app.db.database import get_db
from app.db.crud import DeviceCRUD, NotificationLogCRUD
from app.schemas.device import (
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceListResponse,
    UserDevicesResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices", tags=["Device Management"])


@router.post("/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    request: DeviceRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register or update a device for a user.
    Called when user logs in or app sends device token.
    
    This endpoint should be called by mobile apps on login:
    - Get FCM token from Firebase
    - Send to this endpoint
    - Device is registered and ready to receive notifications
    """
    try:
        device = DeviceCRUD.register_device(
            db=db,
            user_id=request.user_id,
            device_token=request.device_token,
            device_name=request.device_name,
            platform=request.platform
        )
        
        logger.info(f"✅ Device registered for user {request.user_id} on {request.platform}")
        
        return DeviceResponse(
            id=device.id,
            user_id=device.user_id,
            device_name=device.device_name,
            platform=device.platform,
            is_active=device.is_active,
            created_at=device.created_at,
            last_heartbeat=device.last_heartbeat
        )
    
    except Exception as e:
        logger.error(f"❌ Error registering device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}", response_model=UserDevicesResponse)
async def get_user_devices(
    user_id: UUID,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all devices for a user.
    Used internally to fetch tokens for sending notifications.
    """
    try:
        devices = DeviceCRUD.get_user_devices(db, user_id, active_only)
        
        device_responses = [
            DeviceResponse(
                id=d.id,
                user_id=d.user_id,
                device_name=d.device_name,
                platform=d.platform,
                is_active=d.is_active,
                created_at=d.created_at,
                last_heartbeat=d.last_heartbeat
            )
            for d in devices
        ]
        
        return UserDevicesResponse(
            user_id=user_id,
            device_count=len(devices),
            devices=device_responses
        )
    
    except Exception as e:
        logger.error(f"❌ Error retrieving devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}/tokens", response_model=Dict[str, Any])
async def get_user_device_tokens(
    user_id: UUID,
    platform: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all device tokens for a user (for Firebase).
    
    Internal endpoint used by notification sending logic.
    Returns only active device tokens.
    """
    try:
        if platform:
            devices = DeviceCRUD.get_devices_by_platform(
                db, user_id, platform, active_only=True
            )
            tokens = [d.device_token for d in devices]
        else:
            tokens = DeviceCRUD.get_user_device_tokens(db, user_id, active_only=True)
        
        logger.info(f"📱 Retrieved {len(tokens)} tokens for user {user_id}")
        
        return {
            "user_id": str(user_id),
            "token_count": len(tokens),
            "tokens": tokens,
            "platform": platform or "all"
        }
    
    except Exception as e:
        logger.error(f"❌ Error retrieving tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/device/{device_id}", status_code=status.HTTP_200_OK)
async def deactivate_device(
    device_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Deactivate a device (soft delete).
    Called when user logs out or uninstalls app.
    """
    try:
        success = DeviceCRUD.deactivate_device(db, device_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        logger.info(f"✅ Device {device_id} deactivated")
        
        return {
            "success": True,
            "message": f"Device {device_id} deactivated",
            "device_id": str(device_id)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deactivating device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/device/{device_id}/heartbeat", status_code=status.HTTP_200_OK)
async def send_heartbeat(
    device_id: UUID,
    device_token: str,
    db: Session = Depends(get_db)
):
    """
    Send heartbeat to keep device active.
    Mobile app can periodically call this to prevent deactivation.
    """
    try:
        success = DeviceCRUD.heartbeat(db, device_token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device token not found"
            )
        
        return {
            "success": True,
            "message": "Heartbeat recorded",
            "device_id": str(device_id)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending heartbeat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_inactive_devices(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Cleanup inactive devices (deactivate if no heartbeat for N days).
    Admin endpoint - can be called periodically via cron job.
    """
    try:
        count = DeviceCRUD.cleanup_inactive_devices(db, days)
        
        return {
            "success": True,
            "message": f"Deactivated {count} inactive devices",
            "devices_cleaned": count,
            "inactivity_threshold_days": days
        }
    
    except Exception as e:
        logger.error(f"❌ Error cleaning up devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_device_stats(db: Session = Depends(get_db)):
    """
    Get device statistics (admin endpoint).
    """
    try:
        active_devices = db.query(DeviceCRUD).filter(
            lambda d: d.is_active == True
        ).count() if hasattr(db, 'query') else 0
        
        # Get from models directly
        from app.db.models import UserDevice
        
        total = db.query(UserDevice).count()
        active = db.query(UserDevice).filter(UserDevice.is_active == True).count()
        
        platforms = {}
        from sqlalchemy import func
        platform_counts = db.query(
            UserDevice.platform,
            func.count(UserDevice.id)
        ).filter(UserDevice.is_active == True).group_by(UserDevice.platform).all()
        
        for platform, count in platform_counts:
            platforms[platform] = count
        
        return {
            "total_devices": total,
            "active_devices": active,
            "inactive_devices": total - active,
            "platforms": platforms
        }
    
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
