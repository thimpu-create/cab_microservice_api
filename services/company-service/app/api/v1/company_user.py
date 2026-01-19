from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.db.models import CompanyUser, CabCompany
from app.schemas.company_user import (
    CompanyUserCreate,
    CompanyUserResponse,
    CompanyUsersListResponse,
)
from app.core.security import get_current_user_id, get_current_user_role

router = APIRouter(
    prefix="/companies",
    tags=["Company Users"],
)


@router.post(
    "/{company_id}/users",
    response_model=CompanyUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_user_to_company(
    company_id: UUID,
    payload: CompanyUserCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
):
    """
    Add a user to a company (associate user with company).
    
    **Authorization:** 
    - Only VendorAdmin (company owner) can add users to their company
    - Current user must be the owner of the company
    
    **Allowed system roles to add:**
    - VendorDriver (company drivers)
    - VendorManager (company managers)
    - VendorSupport (company support staff)
    
    **Note:** The user being added must already have the correct system role
    (VendorDriver, VendorManager, or VendorSupport) from auth-service.
    The 'role' field in CompanyUser is kept for database compatibility
    but is NOT used for authorization. Authorization is based on the user's
    system role from auth-service.
    """
    # Verify company exists
    company = db.query(CabCompany).filter(CabCompany.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    # Authorization: Only VendorAdmin (company owner) can add users
    if current_user_role != "VendorAdmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only VendorAdmin can add users to a company",
        )
    
    # Verify current user is the company owner
    if company.owner_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add users to your own company",
        )
    
    # Use company_id from URL path
    if payload.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company ID in payload must match URL parameter",
        )
    
    # Check if association already exists
    existing = (
        db.query(CompanyUser)
        .filter(
            CompanyUser.user_id == payload.user_id,
            CompanyUser.company_id == company_id,
        )
        .first()
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already associated with this company",
        )
    
    # Create association
    # Note: role field is kept for DB compatibility but system role is used for authorization
    company_user = CompanyUser(
        user_id=payload.user_id,
        company_id=company_id,
        role=payload.role,  # Defaults to 'driver' if not provided, but not used for auth
        is_active=payload.is_active,
        is_verified=payload.is_verified,
        can_manage_drivers=payload.can_manage_drivers,
        can_manage_rides=payload.can_manage_rides,
        can_view_reports=payload.can_view_reports,
        can_manage_payments=payload.can_manage_payments,
        notes=payload.notes,
    )
    
    db.add(company_user)
    db.commit()
    db.refresh(company_user)
    
    return company_user


@router.get(
    "/{company_id}/users",
    response_model=CompanyUsersListResponse,
)
def get_company_users(
    company_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False, description="Filter only active users"),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    """
    Get all users associated with a company.
    
    Note: The 'role' field in the response is kept for database compatibility
    but is NOT used for authorization. Check the user's system role from
    auth-service for actual permissions.
    """
    # Verify company exists
    company = db.query(CabCompany).filter(CabCompany.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    # Build query
    query = db.query(CompanyUser).filter(CompanyUser.company_id == company_id)
    
    if active_only:
        query = query.filter(CompanyUser.is_active == True)
    
    # Get total counts
    total_users = query.count()
    active_users = (
        db.query(CompanyUser)
        .filter(CompanyUser.company_id == company_id, CompanyUser.is_active == True)
        .count()
    )
    
    # Get paginated results
    users = query.offset(skip).limit(limit).all()
    
    return CompanyUsersListResponse(
        company_id=company_id,
        total_users=total_users,
        active_users=active_users,
        users=users,
    )


@router.delete(
    "/{company_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user_from_company(
    company_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
):
    """
    Remove user from company (delete association).
    
    **Authorization:** Only VendorAdmin (company owner) can remove users from their company.
    """
    # Verify company exists
    company = db.query(CabCompany).filter(CabCompany.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    
    # Authorization: Only VendorAdmin (company owner) can remove users
    if current_user_role != "VendorAdmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only VendorAdmin can remove users from a company",
        )
    
    # Verify current user is the company owner
    if company.owner_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only remove users from your own company",
        )
    association = (
        db.query(CompanyUser)
        .filter(
            CompanyUser.company_id == company_id,
            CompanyUser.user_id == user_id,
        )
        .first()
    )
    
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with this company",
        )
    
    db.delete(association)
    db.commit()
    
    return None
