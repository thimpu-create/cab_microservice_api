from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta
import jwt

from app.core.settings import settings


def create_jwt_token(data: dict, expires_delta: timedelta):
    """Create a JWT token with custom expiry."""
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + expires_delta

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def create_access_token(data: dict):
    """Create access token."""
    expires_delta = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    return create_jwt_token(data, expires_delta)


def create_refresh_token(data: dict):
    """Create refresh token."""
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_jwt_token(data, expires_delta)


def hash_password(password: str) -> str:
    """Hash password safely using PBKDF2-SHA256."""
    if not password:
        raise ValueError("Password cannot be empty")

    safe_password = password[:settings.MAX_PASSWORD_LENGTH]
    hashed = pbkdf2_sha256.hash(safe_password)

    # DEBUG (remove in production)
    print("=== HASH PASSWORD DEBUG ===")
    print("Original password:", password)
    print("Length:", len(password))
    print("Truncated password:", safe_password)
    print("Truncated length:", len(safe_password))
    print("Generated hash:", hashed)

    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using PBKDF2-SHA256."""
    if not plain_password:
        return False

    safe_password = plain_password[:settings.MAX_PASSWORD_LENGTH]
    result = pbkdf2_sha256.verify(safe_password, hashed_password)

    # DEBUG (remove in production)
    print("=== VERIFY PASSWORD DEBUG ===")
    print("Plain password:", plain_password)
    print("Truncated password:", safe_password)
    print("Verification result:", result)

    return result
