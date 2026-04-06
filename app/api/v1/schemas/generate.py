"""AI Generation schemas (PLACEHOLDER)"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class GenerateImageRequest(BaseModel):
    """Generate image request (Guest checkout support)"""
    prompt: str = Field(..., min_length=1, max_length=4000)
    style: Optional[str] = None
    aspectRatio: Optional[str] = "1:1"
    negativePrompt: Optional[str] = None
    characterImages: List[str] = Field(default_factory=list)
    sessionId: str = Field(..., min_length=1)  # Required for guest checkout tracking
    licenseKey: str = Field(..., min_length=1, description="Gumroad License Key")


class GenerateImageResponse(BaseModel):
    """Generate image response"""
    imageUrl: str
    prompt: Optional[str] = None
    generationId: Optional[str] = None
    creditsUsed: int = 0


class BatchSceneInput(BaseModel):
    """Batch scene input"""
    text: str
    prompt: str


class GenerateBatchRequest(BaseModel):
    """Generate batch images request"""
    scenes: List[BatchSceneInput]
    style: str
    characterImages: List[str] = Field(default_factory=list)


class BatchImageResult(BaseModel):
    """Batch image result"""
    sceneIndex: int
    imageUrl: str
    generationId: str


class GenerateBatchResponse(BaseModel):
    """Generate batch images response"""
    images: List[BatchImageResult]
    totalCreditsUsed: int
    taskId: Optional[str] = None  # For async processing


class RegenerateRequest(BaseModel):
    """Regenerate image request"""
    prompt: Optional[str] = None


class GenerationStatusResponse(BaseModel):
    """Generation status response"""
    status: str  # pending, processing, completed, failed
    imageUrl: Optional[str] = None
    error: Optional[str] = None


class CancelGenerationResponse(BaseModel):
    """Cancel generation response"""
    success: bool = True


# Story generation schemas commented out - not in use
# class GenerateStoryRequest(BaseModel):
#     """Generate story request (AI story generation)"""
#     prompt: str = Field(..., min_length=10, max_length=1000)
#     tags: List[str] = Field(default_factory=list)
#     intensity: float = Field(default=0.5, ge=0.0, le=1.0)
#     characters: List["CharacterInput"] = Field(default_factory=list)


# class GeneratedScene(BaseModel):
#     """Generated scene"""
#     text: str
#     imagePrompt: str


# class GenerateStoryResponse(BaseModel):
#     """Generate story response"""
#     title: str
#     synopsis: str
#     scenes: List[GeneratedScene]


# Import after class definitions
# from app.api.v1.schemas.story import CharacterInput
# GenerateStoryRequest.model_rebuild()
