"""Analytics schemas"""

from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class AnalyticsEventRequest(BaseModel):
    """Analytics event request"""
    eventType: str = Field(..., min_length=1, max_length=50)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsEventResponse(BaseModel):
    """Analytics event response"""
    success: bool = True


class UserMetricsResponse(BaseModel):
    """User metrics response"""
    generationsToday: int
    blurClicksToday: int
    downloadAttempts: int
    storiesViewed: int
    isHighIntent: bool


class StoryAnalyticsResponse(BaseModel):
    """Story analytics response"""
    storyId: UUID
    views: int
    likes: int
    saves: int
    comments: int
    shares: int = 0
    averageReadTime: float = 0.0
    completionRate: float = 0.0
