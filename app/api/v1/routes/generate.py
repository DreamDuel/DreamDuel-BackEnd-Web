"""AI Generation routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime, timedelta

from app.core.dependencies import get_current_user_id
from app.api.v1.schemas.generate import (
    GenerateImageRequest, GenerateImageResponse,
    GenerationStatusResponse
)
from app.infrastructure.external_services.ai_image_service import ai_image_service
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User, Invoice
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
    Generate an AI image - $1 per image
    
    Logic:
    - ALL images require payment (no free generation)
    - Requires COMPLETED payment within last 5 minutes
    
    Returns temporary image URL (not saved to profile)
    """
    
    # Get user
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # ALWAYS require payment - no free images
    # Look for completed payment in last 5 minutes
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    
    recent_payment = db.query(Invoice).filter(
        Invoice.user_id == current_user_id,
        Invoice.status == "COMPLETED",
        Invoice.created_at >= five_minutes_ago
    ).order_by(Invoice.created_at.desc()).first()
    
    if not recent_payment:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment required. Please purchase an image generation for $1."
        )
    
    # Generate image with AI service (Cloudinary URL - temporary)
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
    
    # Return image URL (temporary - not saved to profile)
    return GenerateImageResponse(**result)
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
