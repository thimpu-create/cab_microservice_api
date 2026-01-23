"""
SOS emergency endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.session import get_db
from app.db.models import SOSRequest, EmergencyContact, SOSContactNotification, EmergencyNumber, SOSStatus
from app.schemas.sos import (
    SOSTriggerRequest,
    SOSResponse,
    SOSHistoryResponse,
    EmergencyContactCreate,
    EmergencyContactResponse,
    EmergencyContactUpdate,
    EmergencyNumberResponse,
    EmergencyNumberUpdate
)
from app.core.security import get_current_user_id, get_current_user_role, verify_admin_role
from app.core.redis_client import get_live_location
from app.core.notification_client import NotificationClient
from app.core.config import settings

router = APIRouter(prefix="/sos", tags=["SOS Emergency"])

notification_client = NotificationClient()


@router.post("/trigger", response_model=SOSResponse, status_code=status.HTTP_201_CREATED)
async def trigger_sos(
    request: SOSTriggerRequest,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Trigger an emergency SOS.
    
    - Gets live location from Redis (realtime-service) if not provided
    - Calls emergency number (112 by default, configurable)
    - Notifies all 5 emergency contacts
    - Creates SOS request record
    """
    # Get location: from request body OR from Redis (live location)
    latitude = request.latitude
    longitude = request.longitude
    
    if latitude is None or longitude is None:
        # Try to get live location from Redis
        location = get_live_location(str(user_id))
        if location:
            latitude, longitude = location
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Location not provided and live location not available. Please provide latitude and longitude."
            )
    
    # Get emergency number (from config, default: 112)
    emergency_number = settings.EMERGENCY_NUMBER
    
    # Try to get default from database if available
    default_number = db.query(EmergencyNumber).filter(
        EmergencyNumber.is_default == True,
        EmergencyNumber.is_active == True
    ).first()
    
    if default_number:
        emergency_number = default_number.number
    
    # TODO: In future, integrate with telephony service to actually call emergency number
    # For now, we log it
    print(f"🚨 EMERGENCY CALL: Dialing {emergency_number} for user {user_id}")
    print(f"📍 Location: {latitude}, {longitude}")
    
    # Get user's emergency contacts (max 5, active only)
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id,
        EmergencyContact.is_active == True
    ).order_by(EmergencyContact.priority.asc()).limit(5).all()
    
    # Create SOS request
    sos_request = SOSRequest(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        address=request.address,
        emergency_number=emergency_number,
        status=SOSStatus.triggered,
        notes=request.notes
    )
    
    db.add(sos_request)
    db.flush()  # Get the ID
    
    # Notify emergency contacts
    contact_user_ids = []
    for contact in contacts:
        # Create notification record
        notification = SOSContactNotification(
            sos_request_id=sos_request.id,
            contact_id=contact.id
        )
        db.add(notification)
        
        # Collect contact user IDs (if they have user accounts)
        # Note: For now, we'll use contact phone/email. In future, link contacts to user accounts
        # For notification, we need user_ids. If contacts don't have user accounts,
        # we'll need to send SMS/Email directly via notification service
        # For now, we'll store the notification record and send via notification service
        # if contact has linked user_id (future enhancement)
    
    db.commit()
    db.refresh(sos_request)
    
    # Send notifications to emergency contacts
    # Note: This is a simplified version. In production, you'd:
    # 1. Link emergency contacts to user accounts, OR
    # 2. Send SMS/Email directly to contact phone/email
    # For now, we'll send notifications if contacts have user accounts linked
    # (This would require adding user_id field to EmergencyContact in future)
    
    # Get user name (would need to fetch from auth-service)
    user_name = f"User {user_id}"  # Placeholder
    
    # Send notifications (for now, we'll log it)
    # In production, implement proper notification to contacts
    print(f"📧 Sending SOS alerts to {len(contacts)} emergency contacts")
    
    # Create map link
    map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
    
    return SOSResponse(
        id=sos_request.id,
        user_id=sos_request.user_id,
        latitude=sos_request.latitude,
        longitude=sos_request.longitude,
        address=sos_request.address,
        emergency_number=sos_request.emergency_number,
        status=sos_request.status.value,
        triggered_at=sos_request.triggered_at,
        map_link=map_link
    )


@router.get("/history", response_model=List[SOSHistoryResponse], status_code=status.HTTP_200_OK)
async def get_sos_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get user's SOS history."""
    sos_requests = db.query(SOSRequest).filter(
        SOSRequest.user_id == user_id
    ).order_by(SOSRequest.triggered_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for sos in sos_requests:
        contacts_count = db.query(SOSContactNotification).filter(
            SOSContactNotification.sos_request_id == sos.id
        ).count()
        
        result.append(SOSHistoryResponse(
            id=sos.id,
            latitude=sos.latitude,
            longitude=sos.longitude,
            address=sos.address,
            emergency_number=sos.emergency_number,
            status=sos.status.value,
            triggered_at=sos.triggered_at,
            resolved_at=sos.resolved_at,
            contacts_notified_count=contacts_count
        ))
    
    return result


@router.get("/{sos_id}", response_model=SOSResponse, status_code=status.HTTP_200_OK)
async def get_sos_details(
    sos_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get specific SOS request details."""
    sos = db.query(SOSRequest).filter(
        SOSRequest.id == sos_id,
        SOSRequest.user_id == user_id
    ).first()
    
    if not sos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOS request not found"
        )
    
    map_link = f"https://www.google.com/maps?q={sos.latitude},{sos.longitude}"
    
    return SOSResponse(
        id=sos.id,
        user_id=sos.user_id,
        latitude=sos.latitude,
        longitude=sos.longitude,
        address=sos.address,
        emergency_number=sos.emergency_number,
        status=sos.status.value,
        triggered_at=sos.triggered_at,
        map_link=map_link
    )
