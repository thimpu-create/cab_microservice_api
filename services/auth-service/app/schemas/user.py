from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ---------- Role Schemas ----------
class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int

    class Config:
        orm_mode = True


# ---------- User Schemas ----------
class UserBase(BaseModel):
    fname: str
    mname: Optional[str] = None
    lname: str
    email: EmailStr
    phone: str
    status: Optional[str] = "active"

class UserCreate(UserBase):
    password: str
    role_id: int  # assign role when creating

class UserRead(UserBase):
    id: int
    role: RoleRead
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class LoginSchema(BaseModel):
    email: str  # email or phone
    password: str
