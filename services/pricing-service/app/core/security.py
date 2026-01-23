"""
Security utilities for JWT authentication.
"""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID
from typing import Optional

from app.core.config import settings

security = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[UUID]:
    """Extract user ID from JWT token (optional for pricing calculation)."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("user_id") or payload.get("sub")
        if user_id:
            return UUID(user_id)
        return None
    except (jwt.ExpiredSignatureError, jwt.JWTError, ValueError):
        return None


def get_current_user_role(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user role from JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        role: str = payload.get("role")
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return role
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


def verify_admin_role(role: str) -> bool:
    """Verify if user has admin role."""
    return role in ["Admin", "SuperAdmin", "VendorAdmin"]
