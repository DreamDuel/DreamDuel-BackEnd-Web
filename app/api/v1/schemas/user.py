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
    is_verified: bool
    referral_code: str
    
    # Pay-per-image model fields
    total_images_generated: int = 0
    paid_images_count: int = 0
    
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
    is_verified: bool
    created_at: datetime
    
    # Computed fields
    followers_count: int = 0
    following_count: int = 0
    stories_count: int = 0
    
    class Config:
        from_attributes = True


class UserMeSchema(BaseModel):
    """Simplified user schema for /me endpoint (Frontend compatibility)"""
    id: UUID
    username: str
    email: str
    avatarUrl: Optional[str] = Field(None, alias="avatar_url")
    hasUsedFreeGeneration: bool = Field(default=False)
    totalImagesGenerated: int = Field(default=0, alias="total_images_generated")
    createdAt: datetime = Field(alias="created_at")
    
    @classmethod
    def from_user(cls, user):
        """Create schema from User model"""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            hasUsedFreeGeneration=True,  # No free images - always True
            total_images_generated=user.total_images_generated,
            created_at=user.created_at
        )
    
    class Config:
        from_attributes = True
        populate_by_name = True


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
