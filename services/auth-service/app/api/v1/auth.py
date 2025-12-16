from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Role
from app.schemas.user import UserCreate, UserRead, LoginSchema

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------- REGISTER ----------
@router.post("/register", response_model=UserRead)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if email or phone already exists
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.phone == user.phone)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email or phone already registered")

    # Check if role exists
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Hash password
    hashed_password = hash_password(user.password)

    # Create user
    new_user = User(
        fname=user.fname,
        mname=user.mname,
        lname=user.lname,
        email=user.email,
        phone=user.phone,
        password=hashed_password,
        role_id=user.role_id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ---------- LOGIN ----------
@router.post("/login")
def login(payload: LoginSchema, db: Session = Depends(get_db)):

    # Search by email or phone
    user = db.query(User).filter(
        (User.email == payload.email) | (User.phone == payload.email)
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Verify password
    if not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token_data = {
        "user_id": user.id,
        "role": user.role.name,
    }

    # Tokens (expiry handled internally)
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
