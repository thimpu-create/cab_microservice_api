from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@postgres:5432/ridedb"
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    INTERNAL_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
