"""Story schemas"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.utils.validators import validate_tags


class CharacterInput(BaseModel):
    """Character input schema"""
    name: str = Field(..., min_length=1, max_length=100)
    photo_url: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)


class SceneInput(BaseModel):
    """Scene input schema"""
    text: str = Field(..., min_length=1)
    image_url: str
    order: int = Field(..., ge=0)


class CharacterSchema(BaseModel):
    """Character schema"""
    id: UUID
    name: str
    photo_url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SceneSchema(BaseModel):
    """Scene schema"""
    id: UUID
    image_url: str
    text: str
    order: int
    generation_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class StoryCreate(BaseModel):
    """Story creation schema"""
    prompt: str = Field(..., min_length=10, max_length=1000)
    tags: List[str] = Field(default_factory=list)
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    visualStyle: str = Field(..., min_length=1, max_length=50)
    isPublic: bool = True
    characters: List[CharacterInput] = Field(default_factory=list)
    
    @field_validator('tags')
    @classmethod
    def validate_tags_field(cls, v):
        return validate_tags(v)


class StoryUpdate(BaseModel):
    """Story update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    synopsis: Optional[str] = Field(None, max_length=1000)
    cover_url: Optional[str] = None
    visibility: Optional[str] = Field(None, pattern="^(public|private)$")
    tags: Optional[List[str]] = None
    visual_style: Optional[str] = Field(None, max_length=50)
    intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @field_validator('tags')
    @classmethod
    def validate_tags_field(cls, v):
        if v is not None:
            return validate_tags(v)
        return v


class StorySchema(BaseModel):
    """Story schema (list view)"""
    id: UUID
    title: str
    synopsis: str
    cover_url: str
    author_id: UUID
    visibility: str
    tags: List[str]
    visual_style: Optional[str] = None
    intensity: float
    views: int
    likes: int
    comments_count: int
    saves: int
    created_at: datetime
    updated_at: datetime
    
    # Author info
    author: Optional["PublicUserProfileSchema"] = None
    
    # User interaction status (optional)
    is_liked: bool = False
    is_saved: bool = False
    
    class Config:
        from_attributes = True


class StoryDetailSchema(StorySchema):
    """Story detail schema (includes scenes and characters)"""
    scenes: List[SceneSchema] = []
    characters: List[CharacterSchema] = []


class LikeStoryRequest(BaseModel):
    """Like story request"""
    userId: UUID


class LikeResponse(BaseModel):
    """Like response"""
    liked: bool
    likesCount: int


class SaveResponse(BaseModel):
    """Save response"""
    saved: bool


class ViewResponse(BaseModel):
    """View response"""
    success: bool = True


# Import after class definitions to avoid circular import
from app.api.v1.schemas.user import PublicUserProfileSchema
StorySchema.model_rebuild()
