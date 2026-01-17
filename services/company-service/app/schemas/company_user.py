from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.db.models import UserCompanyRole


class CompanyUserBase(BaseModel):
    role: UserCompanyRole = UserCompanyRole.driver
    is_active: bool = True
    is_verified: bool = False
    can_manage_drivers: bool = False
    can_manage_rides: bool = False
    can_view_reports: bool = False
    can_manage_payments: bool = False
    notes: Optional[str] = None


class CompanyUserCreate(CompanyUserBase):
    user_id: UUID
    company_id: UUID


class CompanyUserUpdate(BaseModel):
    role: Optional[UserCompanyRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    can_manage_drivers: Optional[bool] = None
    can_manage_rides: Optional[bool] = None
    can_view_reports: Optional[bool] = None
    can_manage_payments: Optional[bool] = None
    notes: Optional[str] = None
    left_at: Optional[datetime] = None


class CompanyUserResponse(CompanyUserBase):
    id: UUID
    user_id: UUID
    company_id: UUID
    joined_at: datetime
    left_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyUsersListResponse(BaseModel):
    company_id: UUID
    total_users: int
    active_users: int
    users: list[CompanyUserResponse]
