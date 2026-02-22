"""Analytics routes"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from uuid import UUID
from datetime import datetime, timedelta

from app.core.dependencies import get_current_user_id, get_optional_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import AnalyticsEvent, Story
from app.api.v1.schemas.analytics import (
    AnalyticsEventRequest, AnalyticsEventResponse,
    UserMetricsResponse, StoryAnalyticsResponse
)
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.post("/event", response_model=AnalyticsEventResponse)
async def track_event(
    data: AnalyticsEventRequest,
    user_id: str = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """Track an analytics event"""
    
    event = AnalyticsEvent(
        user_id=user_id,
        event_type=data.eventType,
        metadata=data.metadata
    )
    
    db.add(event)
    db.commit()
    
    return AnalyticsEventResponse()


@router.get("/user/metrics", response_model=UserMetricsResponse)
async def get_user_metrics(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user analytics metrics"""
    
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Count events today
    generation_count = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.user_id == current_user_id,
        AnalyticsEvent.event_type == "generation",
        AnalyticsEvent.created_at >= today_start
    ).count()
    
    blur_clicks = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.user_id == current_user_id,
        AnalyticsEvent.event_type == "blur_click",
        AnalyticsEvent.created_at >= today_start
    ).count()
    
    download_attempts = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.user_id == current_user_id,
        AnalyticsEvent.event_type == "download_attempt",
        AnalyticsEvent.created_at >= today_start
    ).count()
    
    stories_viewed = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.user_id == current_user_id,
        AnalyticsEvent.event_type == "story_view",
        AnalyticsEvent.created_at >= today_start
    ).count()
    
    # Determine high intent (heuristic: multiple blur clicks or download attempts)
    is_high_intent = (blur_clicks + download_attempts) >= 3
    
    return UserMetricsResponse(
        generationsToday=generation_count,
        blurClicksToday=blur_clicks,
        downloadAttempts=download_attempts,
        storiesViewed=stories_viewed,
        isHighIntent=is_high_intent
    )


@router.get("/story/{story_id}", response_model=StoryAnalyticsResponse)
async def get_story_analytics(
    story_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific story"""
    
    story = db.query(Story).filter(Story.id == story_id, Story.deleted_at.is_(None)).first()
    if not story:
        raise NotFoundException("Story", story_id)
    
    # Only allow author to view analytics
    if str(story.author_id) != current_user_id:
        raise NotFoundException("Story", story_id)  # Return 404 instead of 403 for privacy
    
    # Get view events
    view_events = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.event_type == "story_view",
        AnalyticsEvent.metadata["story_id"].astext == str(story_id)
    ).all()
    
    # Calculate average read time (mock)
    avg_read_time = 0.0
    if view_events:
        # In production, you'd track actual read time
        avg_read_time = 2.5  # Mock: 2.5 minutes average
    
    # Calculate completion rate (mock)
    completion_rate = 0.75  # Mock: 75% completion rate
    
    return StoryAnalyticsResponse(
        storyId=story_id,
        views=story.views,
        likes=story.likes,
        saves=story.saves,
        comments=story.comments_count,
        shares=0,  # Not implemented yet
        averageReadTime=avg_read_time,
        completionRate=completion_rate
    )
