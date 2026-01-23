"""
Emergency number configuration endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import EmergencyNumber
from app.schemas.sos import EmergencyNumberResponse, EmergencyNumberUpdate
from app.core.security import get_current_user_role, verify_admin_role
from app.core.config import settings

router = APIRouter(prefix="/emergency-number", tags=["Emergency Number"])


@router.get("", response_model=EmergencyNumberResponse, status_code=status.HTTP_200_OK)
async def get_emergency_number(db: Session = Depends(get_db)):
    """
    Get current emergency number.
    Returns default from database or config.
    """
    # Try to get from database first
    default_number = db.query(EmergencyNumber).filter(
        EmergencyNumber.is_default == True,
        EmergencyNumber.is_active == True
    ).first()
    
    if default_number:
        return EmergencyNumberResponse(
            number=default_number.number,
            description=default_number.description,
            country_code=default_number.country_code
        )
    
    # Fallback to config
    return EmergencyNumberResponse(
        number=settings.EMERGENCY_NUMBER,
        description="Default emergency number",
        country_code=None
    )


@router.put("", response_model=EmergencyNumberResponse, status_code=status.HTTP_200_OK)
async def update_emergency_number(
    update: EmergencyNumberUpdate,
    db: Session = Depends(get_db),
    role: str = Depends(get_current_user_role)
):
    """
    Update emergency number (admin only).
    This allows changing the emergency number in the future.
    """
    # Verify admin role
    if not verify_admin_role(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update emergency number"
        )
    
    # Get or create default emergency number
    default_number = db.query(EmergencyNumber).filter(
        EmergencyNumber.is_default == True
    ).first()
    
    if default_number:
        # Update existing
        default_number.number = update.number
        default_number.description = update.description
        default_number.country_code = update.country_code
        default_number.is_active = True
    else:
        # Create new default
        # First, deactivate any existing default numbers
        db.query(EmergencyNumber).filter(
            EmergencyNumber.is_default == True
        ).update({"is_default": False})
        
        # Create new default
        default_number = EmergencyNumber(
            number=update.number,
            description=update.description or "Default emergency number",
            country_code=update.country_code,
            is_active=True,
            is_default=True
        )
        db.add(default_number)
    
    db.commit()
    db.refresh(default_number)
    
    return EmergencyNumberResponse(
        number=default_number.number,
        description=default_number.description,
        country_code=default_number.country_code
    )
