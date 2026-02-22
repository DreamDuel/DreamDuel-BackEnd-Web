"""User schemas"""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.utils.validators import validate_username


class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: EmailStr
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8)
    referral_code: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def validate_username_field(cls, v):
        if v:
            return validate_username(v)
        return v


class UserAvatarUpdate(BaseModel):
    """User avatar update schema"""
    avatarUrl: str = Field(..., min_length=1)


class UserProfileSchema(BaseModel):
    """User profile schema (authenticated user)"""
    id: UUID
    username: str
    email: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_premium: bool
    is_verified: bool
    referral_code: str
    free_images_left: int
    free_images_reset_at: Optional[datetime] = None
    created_at: datetime
    
    # Computed fields
    followers_count: int = 0
    following_count: int = 0
    stories_count: int = 0
    
    class Config:
        from_attributes = True


class PublicUserProfileSchema(BaseModel):
    """Public user profile schema (for other users)"""
    id: UUID
    username: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_premium: bool
    is_verified: bool
    created_at: datetime
    
    # Computed fields
    followers_count: int = 0
    following_count: int = 0
    stories_count: int = 0
    
    class Config:
        from_attributes = True


class FollowResponse(BaseModel):
    """Follow/unfollow response"""
    following: bool
    followersCount: int


class CreditsResponse(BaseModel):
    """User credits response"""
    freeImagesLeft: int
    resetAt: Optional[datetime]
    isPremium: bool


class UseCreditsResponse(BaseModel):
    """Use credits response"""
    success: bool
    creditsLeft: int


class ReferralResponse(BaseModel):
    """Referral application response"""
    success: bool
    bonusCredits: int
    message: str


class ApplyReferralRequest(BaseModel):
    """Apply referral code request"""
    code: str = Field(..., min_length=6, max_length=20)
