from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.db.models import CabCompany, CompanyUser, UserCompanyRole
from app.schemas.cab_company import (
    CabCompanyCreate,
    CabCompanyResponse,
)
from app.core.security import get_current_user_id

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)



@router.post(
    "/register",
    response_model=CabCompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_company(
    payload: CabCompanyCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    # Optional: prevent duplicate company for same user
    existing_company = (
        db.query(CabCompany)
        .filter(CabCompany.owner_user_id == user_id)
        .first()
    )

    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has a registered company",
        )

    company = CabCompany(
        **payload.model_dump(),
        owner_user_id=user_id,
    )

    db.add(company)
    db.flush()  # Flush to get company.id without committing
    
    # Automatically create CompanyUser entry for owner
    # Note: Role field kept for DB compatibility but system role (VendorAdmin) is used for authorization
    company_user = CompanyUser(
        user_id=user_id,
        company_id=company.id,
        role=UserCompanyRole.owner,  # Default, but system role is used for auth
        is_active=True,
        is_verified=True,  # Owner is automatically verified
        can_manage_drivers=True,
        can_manage_rides=True,
        can_view_reports=True,
        can_manage_payments=True,
    )
    
    db.add(company_user)
    db.commit()
    db.refresh(company)

    return company
