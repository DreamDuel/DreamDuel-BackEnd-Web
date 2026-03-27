"""Upload routes"""

import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Literal

from app.core.dependencies import get_current_user_id
from app.core.config import settings

# Base directory for storing uploads locally
UPLOAD_DIR = Path("app/uploads")

router = APIRouter()


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    folder: Literal["avatars", "images"] = Form("images")
):
    """Upload an image file locally to the server"""
    
    # Ensure the directory exists
    target_dir = UPLOAD_DIR / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a unique filename while preserving extension
    extension = os.path.splitext(file.filename)[1] if file.filename else ".png"
    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = target_dir / unique_filename
    
    # Check file size (FastAPI handles this with max size limits, but good practice)
    
    # Save file locally
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file globally: {str(e)}")
    finally:
        file.file.close()
        
    # Return the relative URL so the frontend and backend can find it
    relative_url = f"/app/uploads/{folder}/{unique_filename}"
    
    return {
        "url": relative_url,
        "filename": unique_filename,
        "format": extension.strip('.'),
        "provider": "local"
    }
