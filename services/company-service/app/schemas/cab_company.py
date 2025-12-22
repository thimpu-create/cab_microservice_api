from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.db.models import CompanyType, OperatingRegion, CompanyStatus
from uuid import UUID


class CabCompanyBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    legal_name: Optional[str]

    company_type: CompanyType
    operating_region: OperatingRegion

    country: str = Field(..., examples=["USA", "Canada"])
    state_province: str
    city: str
    timezone: str = Field(..., examples=["America/New_York"])
    currency: str = Field(default="USD", examples=["USD", "CAD"])

    address_line1: str
    address_line2: Optional[str]
    postal_code: str

    business_email: EmailStr
    business_phone: str
    support_email: Optional[EmailStr]
    support_phone: Optional[str]

    website_url: Optional[str]

    # Compliance
    us_dot_number: Optional[str]
    mc_number: Optional[str]
    cvor_number: Optional[str]

    business_license_number: Optional[str]
    license_expiry_date: Optional[datetime]

    insurance_policy_number: Optional[str]
    insurance_provider: Optional[str]
    insurance_expiry_date: Optional[datetime]

    tax_id: Optional[str]
    tax_percentage: Optional[str]

    fleet_size: Optional[int]

    service_areas: Optional[List[str]]
    operating_hours: Optional[Dict[str, str]]

    notes: Optional[str]


class CabCompanyCreate(CabCompanyBase):
    pass


class CabCompanyUpdate(BaseModel):
    company_name: Optional[str]
    legal_name: Optional[str]
    company_type: Optional[CompanyType]
    status: Optional[CompanyStatus]

    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state_province: Optional[str]
    postal_code: Optional[str]

    business_email: Optional[EmailStr]
    business_phone: Optional[str]

    service_areas: Optional[List[str]]
    operating_hours: Optional[Dict[str, str]]

    is_active: Optional[bool]



class CabCompanyResponse(CabCompanyBase):
    id: UUID
    owner_user_id: UUID
    status: CompanyStatus
    is_verified: bool
    is_active: bool

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True  # Pydantic v2
