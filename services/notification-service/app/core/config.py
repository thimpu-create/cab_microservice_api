import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # App Configuration
    APP_NAME: str = "Notification Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Firebase Configuration
    FIREBASE_KEY_PATH: str = os.getenv("FIREBASE_KEY_PATH", "firebase-key.json")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "rideconnectnotifications")
    
    # Database Configuration (if needed for notification history)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", None)
    
    # Redis Configuration (for caching device tokens, subscription states)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    
    # Notification Configuration
    NOTIFICATION_RETENTION_DAYS: int = 30
    MAX_BULK_NOTIFICATION_SIZE: int = 1000
    
    # CORS Configuration
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
