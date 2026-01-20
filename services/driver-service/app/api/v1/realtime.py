from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID
import httpx
from fastapi.security import HTTPAuthorizationCredentials

from app.db.session import get_db
from app.db.models import Driver
from app.core.security import get_current_user_id, get_current_user_role, security
from app.schemas.driver import DriverResponse

router = APIRouter(
    prefix="/realtime",
    tags=["Realtime Integration"],
)

REALTIME_SERVICE_URL = "http://realtime-service:8007/api/v1"


@router.get("/active-ride", response_model=dict)
async def get_active_ride(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the active ride for the current driver.
    """
    # Get driver record
    driver = db.query(Driver).filter(Driver.user_id == user_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    driver_id = str(driver.id)
    
    # Get authorization header from request
    auth_header = request.headers.get("Authorization", "")
    
    # Call realtime service to get active ride
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{REALTIME_SERVICE_URL}/rides/active",
                headers={"Authorization": auth_header},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"status": "no_active_ride"}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Realtime service unavailable: {str(e)}"
        )


@router.get("/status", response_model=dict)
async def get_driver_status(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get driver's realtime status (available, busy, offline).
    """
    # Get driver record
    driver = db.query(Driver).filter(Driver.user_id == user_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    driver_id = str(driver.id)
    
    # Get status from Redis (would need redis client in driver service)
    # For now, return basic info
    return {
        "driver_id": driver_id,
        "is_active": driver.is_active,
        "status": driver.status.value if driver.status else "inactive"
    }


@router.post("/toggle-availability", response_model=dict)
async def toggle_availability(
    available: bool,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Toggle driver availability status.
    Note: This should be done via WebSocket connection to realtime service.
    This endpoint is for reference/status checking.
    """
    # Get driver record
    driver = db.query(Driver).filter(Driver.user_id == user_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Update driver active status
    driver.is_active = available
    db.commit()
    db.refresh(driver)
    
    return {
        "driver_id": str(driver.id),
        "is_active": driver.is_active,
        "message": "Availability updated. Connect via WebSocket to realtime service to go online."
    }
