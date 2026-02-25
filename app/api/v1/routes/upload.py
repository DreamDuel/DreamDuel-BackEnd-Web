"""Upload routes"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Literal

from app.core.dependencies import get_current_user_id
from app.api.v1.schemas.upload import UploadResponse
from app.infrastructure.external_services.storage_service import storage_service
from app.core.config import settings

router = APIRouter()


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    folder: Literal["stories", "avatars", "characters"] = Form("stories"),
    current_user_id: str = Depends(get_current_user_id)
):
    """Upload an image file to S3"""
    
    # Validate file
    storage_service.validate_upload_file(file)
    
    # Check file size (FastAPI handles this with max size limits)
    max_size_mb = settings.MAX_UPLOAD_SIZE_MB
    
    # Upload to S3
    result = await storage_service.upload_image(file, folder=folder)
    
    return UploadResponse(**result)
