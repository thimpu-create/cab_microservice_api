from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Role
from app.schemas.user import (
    PassengerRegister,
    VendorAdminRegister,
    IndependentDriverRegister,
    UserRead,
    LoginSchema,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ======================================================
# INTERNAL HELPERS
# ======================================================

def get_role(db: Session, role_name: str) -> Role:
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(
            status_code=500,
            detail=f"Role '{role_name}' not configured"
        )
    return role


def check_existing_user(db: Session, email: str, phone: str):
    user = db.query(User).filter(
        (User.email == email) | (User.phone == phone)
    ).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email or phone already registered"
        )


# ======================================================
# REGISTER: PASSENGER (PUBLIC)
# ======================================================

@router.post("/register/passenger", response_model=UserRead)
def register_passenger(
    payload: PassengerRegister,
    db: Session = Depends(get_db),
):
    check_existing_user(db, payload.email, payload.phone)

    role = get_role(db, "User")

    user = User(
        fname=payload.fname,
        mname=payload.mname,
        lname=payload.lname,
        email=payload.email.lower(),
        phone=payload.phone,
        password=hash_password(payload.password),
        role_id=role.id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ======================================================
# REGISTER: VENDOR ADMIN (PUBLIC)
# ======================================================

@router.post("/register/vendor-admin", response_model=UserRead)
def register_vendor_admin(
    payload: VendorAdminRegister,
    db: Session = Depends(get_db),
):
    check_existing_user(db, payload.email, payload.phone)

    role = get_role(db, "VendorAdmin")

    user = User(
        fname=payload.fname,
        mname=payload.mname,
        lname=payload.lname,
        email=payload.email.lower(),
        phone=payload.phone,
        password=hash_password(payload.password),
        role_id=role.id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Vendor creation can be added here (or via service layer)

    return user


# ======================================================
# REGISTER: INDEPENDENT DRIVER (PUBLIC)
# ======================================================

@router.post("/register/independent-driver", response_model=UserRead)
def register_independent_driver(
    payload: IndependentDriverRegister,
    db: Session = Depends(get_db),
):
    check_existing_user(db, payload.email, payload.phone)

    role = get_role(db, "IndependentDriver")

    user = User(
        fname=payload.fname,
        mname=payload.mname,
        lname=payload.lname,
        email=payload.email.lower(),
        phone=payload.phone,
        password=hash_password(payload.password),
        role_id=role.id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Driver profile creation can be added here

    return user


# ======================================================
# LOGIN (UNCHANGED – ALL ROLES)
# ======================================================

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
