from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Redis settings (to get live location from realtime-service)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # JWT settings for authentication
    SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    
    # Emergency number (configurable, default: 112)
    EMERGENCY_NUMBER: str = "112"
    
    # Service URLs
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8011/api/v1"
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@postgres:5432/sosdb"
    
    class Config:
        env_file = ".env"


settings = Settings()
