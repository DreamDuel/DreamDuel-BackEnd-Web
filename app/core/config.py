"""Application configuration"""

from typing import List, Optional, Any
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # App
    APP_NAME: str = "DreamDuel"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"
    API_V1_PREFIX: str = "/api"
    FRONTEND_URL: str = "https://dreamduel.com"

    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # PayPal
    PAYPAL_MODE: str = "live"
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: Optional[str] = None

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Sentry
    SENTRY_DSN: Optional[str] = None

    # CORS
    CORS_ORIGINS: Any = "https://dreamduel.com"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # AI
    AI_IMAGE_PROVIDER: str = "replicate"
    REPLICATE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    STABILITY_API_KEY: Optional[str] = None
    CUSTOM_IMAGE_API_URL: Optional[str] = None
    CUSTOM_AI_API_KEY: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
