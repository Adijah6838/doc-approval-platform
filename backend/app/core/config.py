from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./doc_approval.db"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Create a single global instance used across the app
settings = Settings()