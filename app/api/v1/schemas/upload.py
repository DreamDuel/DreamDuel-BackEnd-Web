"""Upload schemas"""

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Upload response schema"""
    url: str
    publicId: str
    width: int
    height: int
    format: str
