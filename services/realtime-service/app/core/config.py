from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # JWT settings for authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    # Ride settings
    RIDE_REQUEST_TIMEOUT_SECONDS: int = 30  # Timeout for ride requests
    DRIVER_SERVICE_URL: str = "http://driver-service:8002/api/v1"
    PASSENGER_SERVICE_URL: str = "http://passenger-service:8003/api/v1"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8011/api/v1"  # Port 8011 from docker-compose
    
    # Matching algorithm weights (configurable)
    MATCHING_DISTANCE_WEIGHT: float = 0.4  # Weight for distance in scoring
    MATCHING_RATING_WEIGHT: float = 0.3  # Weight for driver rating
    MATCHING_VEHICLE_TYPE_WEIGHT: float = 0.2  # Weight for vehicle type match
    MATCHING_VERIFICATION_WEIGHT: float = 0.1  # Weight for verification status
    MATCHING_MIN_RATING_THRESHOLD: float = 3.0  # Minimum rating to prioritize
    MATCHING_MAX_DISTANCE_KM: float = 10.0  # Maximum distance for matching
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@postgres:5432/realtimedb"
    
    class Config:
        env_file = ".env"


settings = Settings()
