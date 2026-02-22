"""Comment schemas"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    """Comment creation schema"""
    storyId: UUID
    content: str = Field(..., min_length=1, max_length=2000)
    parentId: Optional[UUID] = None


class CommentUpdate(BaseModel):
    """Comment update schema"""
    content: str = Field(..., min_length=1, max_length=2000)


class CommentSchema(BaseModel):
    """Comment schema"""
    id: UUID
    story_id: UUID
    user_id: UUID
    parent_id: Optional[UUID] = None
    content: str
    likes: int
    created_at: datetime
    updated_at: datetime
    
    # User info
    user: Optional["PublicUserProfileSchema"] = None
    
    # Nested replies
    replies: List["CommentSchema"] = []
    
    # User interaction
    is_liked: bool = False
    
    class Config:
        from_attributes = True


class CommentLikeResponse(BaseModel):
    """Comment like response"""
    liked: bool
    likesCount: int


class ReportCommentRequest(BaseModel):
    """Report comment request"""
    reason: str = Field(..., min_length=10, max_length=500)


class ReportResponse(BaseModel):
    """Report response"""
    success: bool = True
    message: str = "Report submitted successfully"


# Import after class definitions
from app.api.v1.schemas.user import PublicUserProfileSchema
CommentSchema.model_rebuild()
