"""Cloudinary storage service"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Dict, Any, Optional
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import CloudinaryException


# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


class CloudinaryService:
    """Service for Cloudinary file storage and management"""
    
    @staticmethod
    async def upload_image(
        file: UploadFile,
        folder: str = "general",
        transformation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload an image to Cloudinary
        
        Args:
            file: Uploaded file
            folder: Cloudinary folder (stories, avatars, characters, etc.)
            transformation: Optional transformation parameters
            
        Returns:
            Upload result with URL, public_id, etc.
        """
        try:
            # Read file content
            contents = await file.read()
            
            # Upload parameters
            upload_params = {
                "folder": f"dreamduel/{folder}",
                "resource_type": "auto",
                "format": "auto",  # Auto-detect format
                "quality": "auto:best",  # Auto quality optimization
                "fetch_format": "auto",  # Auto format (WebP, AVIF, etc.)
            }
            
            if transformation:
                upload_params["transformation"] = transformation
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(contents, **upload_params)
            
            return {
                "url": result["secure_url"],
                "publicId": result["public_id"],
                "width": result.get("width", 0),
                "height": result.get("height", 0),
                "format": result.get("format", ""),
            }
            
        except Exception as e:
            raise CloudinaryException(f"Upload failed: {str(e)}")
    
    @staticmethod
    def delete_image(public_id: str) -> Dict[str, Any]:
        """Delete an image from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result
        except Exception as e:
            raise CloudinaryException(f"Delete failed: {str(e)}")
    
    @staticmethod
    def get_image_url(
        public_id: str,
        transformation: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get optimized image URL with transformations
        
        Args:
            public_id: Cloudinary public ID
            transformation: Transformation parameters
            
        Returns:
            Optimized image URL
        """
        try:
            url = cloudinary.CloudinaryImage(public_id).build_url(
                transformation=transformation,
                secure=True,
                fetch_format="auto",
                quality="auto:best"
            )
            return url
        except Exception as e:
            raise CloudinaryException(f"Failed to generate URL: {str(e)}")
    
    @staticmethod
    def get_thumbnail_url(public_id: str, width: int = 300, height: int = 300) -> str:
        """Get thumbnail URL"""
        transformation = {
            "width": width,
            "height": height,
            "crop": "fill",
            "gravity": "auto",
            "quality": "auto:best",
            "fetch_format": "auto"
        }
        return CloudinaryService.get_image_url(public_id, transformation)
    
    @staticmethod
    def validate_upload_file(file: UploadFile) -> bool:
        """Validate upload file type and size"""
        # Check file type
        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/heic",
            "image/heif"
        }
        
        if file.content_type not in allowed_types:
            raise CloudinaryException(
                f"Invalid file type: {file.content_type}. Allowed: JPEG, PNG, GIF, WebP, HEIC"
            )
        
        # Note: File size validation should be done before reading the file
        # FastAPI has built-in file size limits via UploadFile
        
        return True


# Singleton instance
cloudinary_service = CloudinaryService()
