"""AI Generation routes - Guest checkout support"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime, timedelta

from app.api.v1.schemas.generate import (
    GenerateImageRequest, GenerateImageResponse,
    GenerationStatusResponse
)
from app.infrastructure.external_services.ai_image_service import ai_image_service
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User, Invoice, GeneratedImage
from app.core.exceptions import NotFoundException, InsufficientCreditsException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("", response_model=GenerateImageResponse)
async def generate_image_guest(
    data: GenerateImageRequest,
    db: Session = Depends(get_db)
):
    """
    Generate an AI image - $1 per image (GUEST CHECKOUT)
    
    Logic:
    - No login required - uses session_id from frontend
    - Requires COMPLETED payment for this session_id within last 24 hours
    - Checks that image hasn't been generated yet for this payment
    
    Returns image URL and saves to database
    """
    
    # Look for completed payment with this session_id in last 24 hours
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    
    recent_payment = db.query(Invoice).filter(
        Invoice.session_id == data.sessionId,
        Invoice.status == "COMPLETED",
        Invoice.created_at >= twenty_four_hours_ago
    ).order_by(Invoice.created_at.desc()).first()
    
    if not recent_payment:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment required. Please purchase an image generation for $1."
        )
    
    # Check if image was already generated for this session
    existing_image = db.query(GeneratedImage).filter(
        GeneratedImage.session_id == data.sessionId
    ).first()
    
    if existing_image:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Image already generated for this payment. Each payment is valid for one image."
        )
    
    print(f"✅ Generating image for guest session: {data.sessionId}")
    
    # Generate image with AI service
    result = await ai_image_service.generate_image(
        prompt=data.prompt,
        style=data.style,
        aspect_ratio=data.aspectRatio,
        negative_prompt=data.negativePrompt,
        character_images=data.characterImages
    )
    
    # Save generated image to database with session_id
    generated_image = GeneratedImage(
        session_id=data.sessionId,  # Guest session tracking
        user_id=None,  # No user for guest
        prompt=data.prompt,
        negative_prompt=data.negativePrompt,
        image_url=result["imageUrl"],
        style=data.style,
        aspect_ratio=data.aspectRatio,
        generation_id=result.get("generationId"),
        is_public=False  # Guest images are private by default
    )
    db.add(generated_image)
    db.commit()
    
    print(f"✅ Image saved for session: {data.sessionId}, url={result['imageUrl']}")
    
    # Return image URL
    return GenerateImageResponse(**result)
