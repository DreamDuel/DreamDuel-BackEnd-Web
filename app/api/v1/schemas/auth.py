"""Authentication schemas"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.utils.validators import validate_username, validate_password


class RegisterRequest(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    referral_code: Optional[str] = Field(None, min_length=6, max_length=20)
    
    @field_validator('username')
    @classmethod
    def validate_username_field(cls, v):
        return validate_username(v)
    
    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v):
        return validate_password(v)


class LoginRequest(BaseModel):
    """User login request"""
    emailOrUsername: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class OAuthRequest(BaseModel):
    """OAuth login request"""
    token: str = Field(..., min_length=1)


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation"""
    token: str = Field(..., min_length=1)
    newPassword: str = Field(..., min_length=8)
    
    @field_validator('newPassword')
    @classmethod
    def validate_new_password(cls, v):
        return validate_password(v)


class EmailVerificationRequest(BaseModel):
    """Email verification request"""
    token: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Authentication response"""
    token: str
    refresh_token: str
    user: "UserProfileSchema"
    
    class Config:
        from_attributes = True


class LogoutResponse(BaseModel):
    """Logout response"""
    success: bool = True
    message: str = "Successfully logged out"


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


# Import after class definitions to avoid circular import
from app.api.v1.schemas.user import UserProfileSchema
AuthResponse.model_rebuild()
