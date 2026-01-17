from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
import httpx

from app.db.session import get_db
from app.db.models import Driver, DriverStatus
from app.schemas.driver import DriverCountResponse, DriverCreate, DriverResponse
from app.core.security import get_current_user_id, security

router = APIRouter(
    prefix="/drivers/company",
    tags=["Company Drivers"],
)


@router.get(
    "/{company_id}/count",
    response_model=DriverCountResponse,
    status_code=status.HTTP_200_OK,
)
def get_driver_count_for_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Get driver count statistics for a specific company.
    Only accessible by authenticated users.
    """
    # Count total drivers for the company
    total_drivers = db.query(Driver).filter(Driver.company_id == company_id).count()
    
    # Count active drivers
    active_drivers = db.query(Driver).filter(
        Driver.company_id == company_id,
        Driver.status == DriverStatus.active,
        Driver.is_active == True
    ).count()
    
    # Count inactive drivers
    inactive_drivers = db.query(Driver).filter(
        Driver.company_id == company_id,
        Driver.status == DriverStatus.inactive
    ).count()
    
    # Count pending verification
    pending_verification = db.query(Driver).filter(
        Driver.company_id == company_id,
        Driver.status == DriverStatus.pending_verification
    ).count()
    
    return DriverCountResponse(
        company_id=company_id,
        total_drivers=total_drivers,
        active_drivers=active_drivers,
        inactive_drivers=inactive_drivers,
        pending_verification=pending_verification,
    )


@router.get(
    "/{company_id}",
    status_code=status.HTTP_200_OK,
)
def get_drivers_for_company(
    company_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Get list of drivers for a specific company.
    Only accessible by authenticated users.
    """
    drivers = (
        db.query(Driver)
        .filter(Driver.company_id == company_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return {
        "company_id": str(company_id),
        "count": len(drivers),
        "drivers": [
            {
                "id": str(driver.id),
                "user_id": str(driver.user_id),
                "status": driver.status.value if driver.status else None,
                "is_verified": driver.is_verified,
                "is_active": driver.is_active,
                "license_number": driver.license_number,
                "vehicle_make": driver.vehicle_make,
                "vehicle_model": driver.vehicle_model,
                "vehicle_year": driver.vehicle_year,
                "vehicle_color": driver.vehicle_color,
                "vehicle_plate_number": driver.vehicle_plate_number,
                "created_at": driver.created_at.isoformat() if driver.created_at else None,
            }
            for driver in drivers
        ],
    }


@router.post(
    "/{company_id}/register",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_driver_for_company(
    company_id: UUID,
    payload: DriverCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Register a new driver for a company.
    Requires authentication.
    
    **IMPORTANT:** 
    - `company_id` comes from URL path (NOT in request body)
    - Do NOT include `company_id` in the JSON body
    
    **Two modes:**
    1. **Link existing user**: Provide `user_id` in body
    2. **Create new user**: Provide `fname`, `lname`, `email`, `phone`, `password` in body
       (user account will be auto-created in auth-service)
    
    **Example for Mode 2 (create new user):**
    ```json
    {
      "fname": "John",
      "lname": "Driver",
      "email": "john@example.com",
      "phone": "+1234567890",
      "password": "SecurePass123!",
      "license_number": "DL123456",
      "vehicle_make": "Toyota",
      "vehicle_model": "Camry"
    }
    ```
    """
    # Note: company_id is automatically set from URL parameter, not from payload
    driver_user_id: UUID
    
    # Mode 1: Use existing user
    if payload.user_id:
        driver_user_id = payload.user_id
        # Verify user exists in auth-service (optional check)
        # For now, we'll trust the user_id is valid
    
    # Mode 2: Create new user account
    else:
        # Validate required fields for new user
        if not all([payload.fname, payload.lname, payload.email, payload.phone, payload.password]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="If user_id is not provided, you must provide: fname, lname, email, phone, password"
            )
        
        # Create user in auth-service
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
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Failed to create user account: {response.json().get('detail', 'Unknown error')}"
                    )
                
                user_response = response.json()
                # Get uuid from user response (now included in UserRead schema)
                if "uuid" in user_response and user_response["uuid"]:
                    driver_user_id = UUID(user_response["uuid"])
                else:
                    # Fallback: if uuid not in response, raise error
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="User created but UUID not available in response. Please contact support."
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
    
    # Create driver record - automatically set company_id from URL parameter
    driver = Driver(
        user_id=driver_user_id,
        company_id=company_id,  # Set from URL parameter
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
