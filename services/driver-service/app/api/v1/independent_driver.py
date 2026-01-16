from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import httpx

from app.db.session import get_db
from app.db.models import Driver, DriverStatus
from app.schemas.driver import DriverCreate, DriverResponse

router = APIRouter(
    prefix="/drivers",
    tags=["Independent Drivers"],
)


@router.post(
    "/register/independent",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_independent_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db),
):
    """
    Register as an independent driver (not linked to any company).
    This is a PUBLIC endpoint - no authentication required.
    
    Creates both:
    1. User account in auth-service (with IndependentDriver role)
    2. Driver profile in driver-service (with company_id = null)
    
    Required fields: fname, lname, email, phone, password
    Optional fields: All driver-specific fields (license, vehicle info, etc.)
    """
    # Validate required fields for new user
    if not all([payload.fname, payload.lname, payload.email, payload.phone, payload.password]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Required fields: fname, lname, email, phone, password"
        )
    
    # If user_id is provided, use it (for existing users registering as driver)
    driver_user_id: UUID
    
    if payload.user_id:
        driver_user_id = payload.user_id
    else:
        # Create user in auth-service as IndependentDriver
        AUTH_SERVICE_URL = "http://auth-service:8000/api/v1/auth"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{AUTH_SERVICE_URL}/register/independent-driver",
                    json={
                        "fname": payload.fname,
                        "mname": payload.mname,
                        "lname": payload.lname,
                        "email": payload.email,
                        "phone": payload.phone,
                        "password": payload.password,
                        "license_number": payload.license_number
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    # Try to get error detail, but handle non-JSON responses
                    try:
                        error_detail = response.json().get('detail', 'Unknown error')
                    except Exception:
                        error_detail = response.text or f"Auth service returned status {response.status_code}"
                    
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to create user account: {error_detail}"
                    )
                
                # Parse response JSON
                try:
                    user_response = response.json()
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Invalid response from auth service: {str(e)}"
                    )
                
                # Get uuid from user response
                if "uuid" in user_response and user_response["uuid"]:
                    driver_user_id = UUID(user_response["uuid"])
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"User created but UUID not available in response. Response: {user_response}"
                    )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Auth service unavailable: {str(e)}"
            )
    
    # Check if driver already exists for this user
    existing_driver = (
        db.query(Driver)
        .filter(Driver.user_id == driver_user_id)
        .first()
    )
    
    if existing_driver:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver already registered for this user",
        )
    
    # Create independent driver record (company_id = None)
    driver = Driver(
        user_id=driver_user_id,
        company_id=None,  # Independent drivers have no company
        license_number=payload.license_number,
        license_expiry_date=payload.license_expiry_date,
        license_state_province=payload.license_state_province,
        vehicle_make=payload.vehicle_make,
        vehicle_model=payload.vehicle_model,
        vehicle_year=payload.vehicle_year,
        vehicle_color=payload.vehicle_color,
        vehicle_plate_number=payload.vehicle_plate_number,
        notes=payload.notes,
        status=DriverStatus.pending_verification,  # New drivers start as pending
        is_verified=False,
        is_active=True,
    )
    
    db.add(driver)
    db.commit()
    db.refresh(driver)
    
    return driver
