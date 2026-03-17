"""Application configuration using Pydantic Settings"""

from typing import List, Optional, Union, Any
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    APP_NAME: str = "DreamDuel"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production-use-generate-secrets-py"
    API_V1_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET: str = "change-me-in-production-use-generate-secrets-py"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = "dummy-cloud-name"
    CLOUDINARY_API_KEY: str = "dummy-api-key"
    CLOUDINARY_API_SECRET: str = "dummy-api-secret"
    
    # Resend
    RESEND_API_KEY: str = "re_dummy_api_key"
    FROM_EMAIL: str = "noreply@dreamduel.com"
    
    # OAuth (optional)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_TEAM_ID: Optional[str] = None
    APPLE_KEY_ID: Optional[str] = None
    APPLE_PRIVATE_KEY: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # Sentry (optional)
    SENTRY_DSN: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: Any = "http://localhost:3000"
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # AI Services Configuration
    AI_IMAGE_PROVIDER: str = "replicate"  # replicate, openai, stability, custom
    AI_STORY_PROVIDER: str = "openai"  # openai, anthropic, custom
    
    # AI API Keys
    REPLICATE_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Custom AI Services
    CUSTOM_IMAGE_API_URL: Optional[str] = None
    CUSTOM_STORY_API_URL: Optional[str] = None
    CUSTOM_AI_API_KEY: Optional[str] = None
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string to list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
