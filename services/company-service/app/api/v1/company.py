from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.db.models import CabCompany
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
    db.commit()
    db.refresh(company)

    return company
