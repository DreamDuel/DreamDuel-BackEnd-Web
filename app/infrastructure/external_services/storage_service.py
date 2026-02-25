"""AWS S3 storage service"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
from fastapi import UploadFile
import uuid
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import ExternalServiceException


class S3StorageService:
    """Service for AWS S3 file storage and management"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.AWS_S3_BUCKET
        self.region = settings.AWS_REGION
    
    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "general",
        transformation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload an image to S3
        
        Args:
            file: Uploaded file
            folder: S3 folder (avatars, generated_images, etc.)
            transformation: Not used in S3 (kept for compatibility)
            
        Returns:
            Upload result with URL, key, etc.
        """
        try:
            # Read file content
            contents = await file.read()
            
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            key = f"dreamduel/{folder}/{unique_filename}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=contents,
                ContentType=file.content_type or 'image/jpeg',
                CacheControl='max-age=31536000',  # 1 year cache
            )
            
            # Generate public URL
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
            
            return {
                "url": url,
                "publicId": key,
                "key": key,
                "bucket": self.bucket,
                "width": 0,  # S3 doesn't auto-detect dimensions
                "height": 0,
                "format": file_extension,
            }
            
        except ClientError as e:
            raise ExternalServiceException(f"S3 upload failed: {str(e)}")
        except Exception as e:
            raise ExternalServiceException(f"Upload failed: {str(e)}")
    
    def delete_image(self, key: str) -> Dict[str, Any]:
        """Delete an image from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return {"status": "deleted", "key": key}
        except ClientError as e:
            raise ExternalServiceException(f"S3 delete failed: {str(e)}")
    
    def get_image_url(
        self,
        key: str,
        transformation: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get S3 image URL
        
        Args:
            key: S3 object key
            transformation: Not used in S3 (use CloudFront for transformations)
            
        Returns:
            S3 image URL
        """
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
    
    def get_thumbnail_url(self, key: str, width: int = 300, height: int = 300) -> str:
        """
        Get thumbnail URL
        
        Note: S3 doesn't do dynamic transformations.
        Consider using CloudFront + Lambda@Edge for image resizing.
        """
        return self.get_image_url(key)
    
    def validate_upload_file(self, file: UploadFile) -> bool:
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
            raise ExternalServiceException(
                f"Invalid file type: {file.content_type}. Allowed: JPEG, PNG, GIF, WebP, HEIC"
            )
        
        return True


# Singleton instance
storage_service = S3StorageService()
