from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ======================================================
# ROLE SCHEMAS
# ======================================================

class RoleBase(BaseModel):
    name: str


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    id: int

    class Config:
        orm_mode = True


# ======================================================
# BASE USER SCHEMA (shared fields)
# ======================================================

class UserBase(BaseModel):
    fname: str
    mname: Optional[str] = None
    lname: str
    email: EmailStr
    phone: str
    status: Optional[str] = "active"


# ======================================================
# PUBLIC REGISTRATION SCHEMAS (NO ROLE FIELD)
# ======================================================

class PassengerRegister(BaseModel):
    fname: str
    mname: Optional[str] = None
    lname: str
    email: EmailStr
    phone: str
    password: str


class VendorAdminRegister(BaseModel):
    fname: str
    mname: Optional[str] = None
    lname: str
    email: EmailStr
    phone: str
    password: str

    # optional: if vendor/company is created at signup
    company_name: Optional[str] = None


class IndependentDriverRegister(BaseModel):
    fname: str
    mname: Optional[str] = None
    lname: str
    email: EmailStr
    phone: str
    password: str

    # optional driver-specific info
    license_number: Optional[str] = None


# ======================================================
# VENDOR-MANAGED USER CREATION (AUTH REQUIRED)
# ======================================================

class VendorUserCreate(BaseModel):
    fname: str
    mname: Optional[str] = None
    lname: str
    email: Optional[EmailStr] = None
    phone: str
    password: str

    # MUST be validated server-side
    role: str  # VendorDriver / VendorSupport / VendorManager


# ======================================================
# USER READ (SAFE RESPONSE)
# ======================================================

class UserRead(BaseModel):
    id: int
    fname: str
    mname: Optional[str]
    lname: str
    email: EmailStr
    phone: str
    status: str
    role: RoleRead
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# ======================================================
# AUTH / LOGIN
# ======================================================

class LoginSchema(BaseModel):
    email: str  # email OR phone
    password: str
