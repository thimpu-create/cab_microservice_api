from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Redis settings (for surge calculation - get driver availability from realtime-service)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # JWT settings for authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@postgres:5432/pricingdb"
    
    # Default surge parameters (can be overridden in database)
    DEFAULT_BASE_DEMAND_THRESHOLD: float = 1.5  # Demand/supply ratio to start surge
    DEFAULT_MAX_SURGE: float = 3.0  # Maximum surge multiplier
    DEFAULT_SURGE_INCREMENT: float = 0.2  # Surge increment per demand unit
    
    class Config:
        env_file = ".env"


settings = Settings()
