"""
Emergency contacts management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.session import get_db
from app.db.models import EmergencyContact
from app.schemas.sos import (
    EmergencyContactCreate,
    EmergencyContactResponse,
    EmergencyContactUpdate
)
from app.core.security import get_current_user_id

router = APIRouter(prefix="/contacts", tags=["Emergency Contacts"])

MAX_CONTACTS = 5  # Maximum 5 emergency contacts per user


@router.post("", response_model=EmergencyContactResponse, status_code=status.HTTP_201_CREATED)
async def create_emergency_contact(
    contact: EmergencyContactCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Add an emergency contact (max 5 per user).
    """
    # Check current contact count
    current_count = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id,
        EmergencyContact.is_active == True
    ).count()
    
    if current_count >= MAX_CONTACTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_CONTACTS} emergency contacts allowed. Please remove one before adding another."
        )
    
    # Validate: at least phone or email required
    if not contact.phone and not contact.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least phone or email is required"
        )
    
    # Create contact
    new_contact = EmergencyContact(
        user_id=user_id,
        name=contact.name,
        phone=contact.phone,
        email=contact.email,
        priority=contact.priority,
        is_active=True
    )
    
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    
    return new_contact


@router.get("", response_model=List[EmergencyContactResponse], status_code=status.HTTP_200_OK)
async def list_emergency_contacts(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get user's emergency contacts."""
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id
    ).order_by(EmergencyContact.priority.asc(), EmergencyContact.created_at.asc()).all()
    
    return contacts


@router.put("/{contact_id}", response_model=EmergencyContactResponse, status_code=status.HTTP_200_OK)
async def update_emergency_contact(
    contact_id: UUID,
    contact_update: EmergencyContactUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Update an emergency contact."""
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == user_id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency contact not found"
        )
    
    # Update fields
    if contact_update.name is not None:
        contact.name = contact_update.name
    if contact_update.phone is not None:
        contact.phone = contact_update.phone
    if contact_update.email is not None:
        contact.email = contact_update.email
    if contact_update.priority is not None:
        contact.priority = contact_update.priority
    if contact_update.is_active is not None:
        contact.is_active = contact_update.is_active
    
    # Validate: at least phone or email required
    if not contact.phone and not contact.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least phone or email is required"
        )
    
    db.commit()
    db.refresh(contact)
    
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_200_OK)
async def delete_emergency_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id)
):
    """Delete (deactivate) an emergency contact."""
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.user_id == user_id
    ).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency contact not found"
        )
    
    # Soft delete (deactivate)
    contact.is_active = False
    db.commit()
    
    return {"message": "Emergency contact deactivated successfully"}
