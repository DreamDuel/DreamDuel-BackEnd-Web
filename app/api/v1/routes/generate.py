"""AI Generation routes (PLACEHOLDER)"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.core.dependencies import get_current_user_id
from app.api.v1.schemas.generate import (
    GenerateImageRequest, GenerateImageResponse,
    GenerateBatchRequest, GenerateBatchResponse,
    RegenerateRequest, GenerationStatusResponse,
    CancelGenerationResponse
)
from app.infrastructure.external_services.ai_image_service import ai_image_service
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User
from app.core.exceptions import NotFoundException, InsufficientCreditsException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("", response_model=GenerateImageResponse)
async def generate_image(
    data: GenerateImageRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Generate an AI image
    
    - First image is FREE
    - Each additional image requires payment (purchased credits)
    """
    
    # Get user
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # Check if user can generate image
    # First image is always free
    if user.total_images_generated == 0:
        # This is the first image - FREE!
        pass
    else:
        # User needs to have purchased images
        images_available = user.paid_images_count - (user.total_images_generated - 1)
        
        if images_available <= 0:
            raise InsufficientCreditsException(
                required=1, 
                available=images_available,
                message="You need to purchase image generations to continue"
            )
    
    # Generate image with AI service
    result = await ai_image_service.generate_image(
        prompt=data.prompt,
        style=data.style,
        aspect_ratio=data.aspectRatio,
        negative_prompt=data.negativePrompt,
        character_images=data.characterImages
    )
    
    # Increment total images generated
    user.total_images_generated += 1
    db.commit()
    
    return GenerateImageResponse(**result)


# Batch generation endpoint commented out - designed for story scenes
# @router.post("/batch", response_model=GenerateBatchResponse)
# async def generate_batch(
#     data: GenerateBatchRequest,
#     current_user_id: str = Depends(get_current_user_id),
#     db: Session = Depends(get_db)
# ):
#     """Generate multiple AI images in batch (PLACEHOLDER)"""
#     
#     # Check user credits
#     user = db.query(User).filter(User.id == current_user_id).first()
#     if not user:
#         raise NotFoundException("User", current_user_id)
#     
#     required_credits = len(data.scenes)
#     
#     if not user.is_premium and user.free_images_left < required_credits:
#         raise InsufficientCreditsException(required=required_credits, available=user.free_images_left)
#     
#     # Generate images
#     prompts = [{"text": scene.text, "prompt": scene.prompt} for scene in data.scenes]
#     result = await ai_image_service.generate_batch(
#         prompts=prompts,
#         style=data.style,
#         character_images=data.characterImages
#     )
#     
#     # Deduct credits
#     if not user.is_premium:
#         user.free_images_left -= required_credits
#         db.commit()
#     
#     return GenerateBatchResponse(**result)


@router.post("/{generation_id}/regenerate", response_model=GenerateImageResponse)
async def regenerate_image(
    generation_id: str,
    data: RegenerateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Regenerate an AI image (PLACEHOLDER)"""
    
    # Check user credits (pay-per-image model)
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # Check if user has images available
    if user.total_images_generated == 0:
        # First image - FREE!
        pass
    else:
        # Calculate available images
        images_available = user.paid_images_count - (user.total_images_generated - 1)
        if images_available <= 0:
            raise InsufficientCreditsException(
                required=1, 
                available=max(0, images_available)
            )
    
    # Regenerate image
    result = await ai_image_service.regenerate_image(
        generation_id=generation_id,
        new_prompt=data.prompt
    )
    
    # Increment total images generated
    user.total_images_generated += 1
    db.commit()
    
    return GenerateImageResponse(**result)


@router.get("/{generation_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(
    generation_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get generation status (PLACEHOLDER)"""
    
    result = await ai_image_service.get_generation_status(generation_id)
    return GenerationStatusResponse(**result)


@router.post("/{generation_id}/cancel", response_model=CancelGenerationResponse)
async def cancel_generation(
    generation_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Cancel an in-progress generation (PLACEHOLDER)"""
    
    success = await ai_image_service.cancel_generation(generation_id)
    return CancelGenerationResponse(success=success)


# Story generation endpoint commented out - not in use
# @router.post("/story", response_model=GenerateStoryResponse)
# async def generate_story(
#     data: GenerateStoryRequest,
#     current_user_id: str = Depends(get_current_user_id)
# ):
#     """Generate a story structure with AI (PLACEHOLDER)"""
#     
#     result = await ai_story_service.generate_story(
#         prompt=data.prompt,
#         tags=data.tags,
#         intensity=data.intensity,
#         characters=[c.dict() for c in data.characters]
#     )
#     
#     return GenerateStoryResponse(**result)
