from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_PASSWORD_LENGTH: int = 128

    class Config:
        env_file = ".env"


settings = Settings()
