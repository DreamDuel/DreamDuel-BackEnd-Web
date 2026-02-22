"""Story routes"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.core.dependencies import get_current_user_id, get_optional_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Story, Scene, Character, User, Like, Save
from app.api.v1.schemas.story import (
    StoryCreate, StoryUpdate, StorySchema, StoryDetailSchema,
    LikeStoryRequest, LikeResponse, SaveResponse, ViewResponse
)
from app.api.v1.schemas.user import PublicUserProfileSchema
from app.core.exceptions import NotFoundException, ForbiddenException
from app.utils.pagination import paginate, PaginationParams, PaginatedResponse
from app.utils.helpers import get_trending_score
from app.infrastructure.external_services.ai_story_service import ai_story_service
from app.infrastructure.external_services.ai_image_service import ai_image_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[StorySchema])
async def get_stories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """Get all public stories"""
    
    query = db.query(Story).filter(
        Story.visibility == "public",
        Story.deleted_at.is_(None)
    ).order_by(desc(Story.created_at))
    
    pagination = PaginationParams(page=page, limit=limit)
    result = paginate(query, pagination, StorySchema)
    
    # Enrich with author info
    for story in result.items:
        author = db.query(User).filter(User.id == story.author_id).first()
        if author:
            story.author =PublicUserProfileSchema(**author.__dict__, followers_count=0, following_count=0, stories_count=0)
        
        # Check if current user liked/saved
        if user_id:
            story.is_liked = db.query(Like).filter(
                Like.user_id == user_id,
                Like.story_id == story.id
            ).first() is not None
            story.is_saved = db.query(Save).filter(
                Save.user_id == user_id,
                Save.story_id == story.id
            ).first() is not None
    
    return result


@router.get("/trending", response_model=PaginatedResponse[StorySchema])
async def get_trending_stories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """Get trending stories (based on recent engagement)"""
    
    # Stories from the last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    stories = db.query(Story).filter(
        Story.visibility == "public",
        Story.deleted_at.is_(None),
        Story.created_at >= week_ago
    ).all()
    
    # Calculate trending score for each
    story_scores = [
        (story, get_trending_score(story.views, story.likes, story.created_at))
        for story in stories
    ]
    
    # Sort by score
    story_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Paginate manually
    start = (page - 1) * limit
    end = start + limit
    paginated_stories = [s[0] for s in story_scores[start:end]]
    
    # Convert to schema
    items = []
    for story in paginated_stories:
        author = db.query(User).filter(User.id == story.author_id).first()
        story_schema = StorySchema(**story.__dict__)
        if author:
            story_schema.author = PublicUserProfileSchema(**author.__dict__, followers_count=0, following_count=0, stories_count=0)
        
        if user_id:
            story_schema.is_liked = db.query(Like).filter(Like.user_id == user_id, Like.story_id == story.id).first() is not None
            story_schema.is_saved = db.query(Save).filter(Save.user_id == user_id, Save.story_id == story.id).first() is not None
        
        items.append(story_schema)
    
    return PaginatedResponse(
        items=items,
        total=len(story_scores),
        page=page,
        pages=(len(story_scores) + limit - 1) // limit,
        limit=limit,
        has_next=end < len(story_scores),
        has_prev=page > 1
    )


@router.get("/new", response_model=PaginatedResponse[StorySchema])
async def get_new_stories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """Get newest stories"""
    
    query = db.query(Story).filter(
        Story.visibility == "public",
        Story.deleted_at.is_(None)
    ).order_by(desc(Story.created_at))
    
    pagination = PaginationParams(page=page, limit=limit)
    result = paginate(query, pagination, StorySchema)
    
    for story in result.items:
        author = db.query(User).filter(User.id == story.author_id).first()
        if author:
            story.author = PublicUserProfileSchema(**author.__dict__, followers_count=0, following_count=0, stories_count=0)
        
        if user_id:
            story.is_liked = db.query(Like).filter(Like.user_id == user_id, Like.story_id == story.id).first() is not None
            story.is_saved = db.query(Save).filter(Save.user_id == user_id, Save.story_id == story.id).first() is not None
    
    return result


@router.get("/{story_id}", response_model=StoryDetailSchema)
async def get_story(
    story_id: UUID,
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """Get story details"""
    
    story = db.query(Story).filter(Story.id == story_id, Story.deleted_at.is_(None)).first()
    if not story:
        raise NotFoundException("Story", story_id)
    
    # Check visibility
    if story.visibility == "private" and (not user_id or str(story.author_id) != user_id):
        raise ForbiddenException("This story is private")
    
    # Get scenes and characters
    scenes = db.query(Scene).filter(Scene.story_id == story_id).order_by(Scene.order).all()
    characters = db.query(Character).filter(Character.story_id == story_id).all()
    
    # Get author
    author = db.query(User).filter(User.id == story.author_id).first()
    
    story_detail = StoryDetailSchema(**story.__dict__)
    story_detail.scenes = scenes
    story_detail.characters = characters
    
    if author:
        story_detail.author = PublicUserProfileSchema(**author.__dict__, followers_count=0, following_count=0, stories_count=0)
    
    if user_id:
        story_detail.is_liked = db.query(Like).filter(Like.user_id == user_id, Like.story_id == story.id).first() is not None
        story_detail.is_saved = db.query(Save).filter(Save.user_id == user_id, Save.story_id == story.id).first() is not None
    
    return story_detail


@router.get("/author/{author_id}", response_model=PaginatedResponse[StorySchema])
async def get_author_stories(
    author_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """Get stories by author"""
    
    # Show only public stories unless it's the author viewing
    if user_id and str(author_id) == user_id:
        query = db.query(Story).filter(Story.author_id == author_id, Story.deleted_at.is_(None))
    else:
        query = db.query(Story).filter(Story.author_id == author_id, Story.visibility == "public", Story.deleted_at.is_(None))
    
    query = query.order_by(desc(Story.created_at))
    
    pagination = PaginationParams(page=page, limit=limit)
    result = paginate(query, pagination, StorySchema)
    
    author = db.query(User).filter(User.id == author_id).first()
    
    for story in result.items:
        if author:
            story.author = PublicUserProfileSchema(**author.__dict__, followers_count=0, following_count=0, stories_count=0)
        
        if user_id:
            story.is_liked = db.query(Like).filter(Like.user_id == user_id, Like.story_id == story.id).first() is not None
            story.is_saved = db.query(Save).filter(Save.user_id == user_id, Like.story_id == story.id).first() is not None
    
    return result


@router.get("/search", response_model=PaginatedResponse[StorySchema])
async def search_stories(
    q: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    style: Optional[str] = Query(None),
    sort: str = Query("new", regex="^(new|trending|popular)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """Search stories"""
    
    query = db.query(Story).filter(Story.visibility == "public", Story.deleted_at.is_(None))
    
    # Text search
    if q:
        query = query.filter(
            or_(
                Story.title.ilike(f"%{q}%"),
                Story.synopsis.ilike(f"%{q}%")
            )
        )
    
    # Filter by tags
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",")]
        # PostgreSQL JSON contains
        for tag in tag_list:
            query = query.filter(Story.tags.contains([tag]))
    
    # Filter by style
    if style:
        query = query.filter(Story.visual_style == style)
    
    # Sorting
    if sort == "new":
        query = query.order_by(desc(Story.created_at))
    elif sort == "popular":
        query = query.order_by(desc(Story.views))
    elif sort == "trending":
        query = query.order_by(desc(Story.likes))
    
    pagination = PaginationParams(page=page, limit=limit)
    result = paginate(query, pagination, StorySchema)
    
    for story in result.items:
        author = db.query(User).filter(User.id == story.author_id).first()
        if author:
            story.author = PublicUserProfileSchema(**author.__dict__, followers_count=0, following_count=0, stories_count=0)
        
        if user_id:
            story.is_liked = db.query(Like).filter(Like.user_id == user_id, Like.story_id == story.id).first() is not None
            story.is_saved = db.query(Save).filter(Save.user_id == user_id, Save.story_id == story.id).first() is not None
    
    return result


@router.post("", response_model=StorySchema, status_code=status.HTTP_201_CREATED)
async def create_story(
    data: StoryCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new story (with AI generation)"""
    
    # TODO: This would coordinate with AI story and image generation
    # For now, create a placeholder story
    
    # Generate story structure with AI
    story_structure = await ai_story_service.generate_story(
        prompt=data.prompt,
        tags=data.tags,
        intensity=data.intensity,
        characters=[c.dict() for c in data.characters]
    )
    
    # Create story
    new_story = Story(
        title=story_structure["title"],
        synopsis=story_structure["synopsis"],
        cover_url="https://via.placeholder.com/800x600.png?text=Story+Cover",  # Placeholder
        author_id=current_user_id,
        visibility="public" if data.isPublic else "private",
        tags=data.tags,
        visual_style=data.visualStyle,
        intensity=data.intensity
    )
    
    db.add(new_story)
    db.flush()
    
    # Create characters
    for char_data in data.characters:
        character = Character(
            story_id=new_story.id,
            name=char_data.name,
            photo_url=char_data.photo_url,
            description=char_data.description
        )
        db.add(character)
    
    # Create scenes (would generate images here)
    for idx, scene_data in enumerate(story_structure["scenes"]):
        # In production: generate image with AI
        image_result = await ai_image_service.generate_image(
            prompt=scene_data["image_prompt"],
            style=data.visualStyle
        )
        
        scene = Scene(
            story_id=new_story.id,
            image_url=image_result["image_url"],
            text=scene_data["text"],
            order=idx,
            generation_id=image_result.get("generation_id")
        )
        db.add(scene)
    
    db.commit()
    db.refresh(new_story)
    
    return StorySchema(**new_story.__dict__)


@router.put("/{story_id}", response_model=StorySchema)
async def update_story(
    story_id: UUID,
    data: StoryUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update story"""
    
    story = db.query(Story).filter(Story.id == story_id, Story.deleted_at.is_(None)).first()
    if not story:
        raise NotFoundException("Story", story_id)
    
    if str(story.author_id) != current_user_id:
        raise ForbiddenException("You can only edit your own stories")
    
    # Update fields
    if data.title:
        story.title = data.title
    if data.synopsis:
        story.synopsis = data.synopsis
    if data.cover_url:
        story.cover_url = data.cover_url
    if data.visibility:
        story.visibility = data.visibility
    if data.tags is not None:
        story.tags = data.tags
    if data.visual_style:
        story.visual_style = data.visual_style
    if data.intensity is not None:
        story.intensity = data.intensity
    
    db.commit()
    db.refresh(story)
    
    return StorySchema(**story.__dict__)


@router.delete("/{story_id}")
async def delete_story(
    story_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete story (soft delete)"""
    
    story = db.query(Story).filter(Story.id == story_id, Story.deleted_at.is_(None)).first()
    if not story:
        raise NotFoundException("Story", story_id)
    
    if str(story.author_id) != current_user_id:
        raise ForbiddenException("You can only delete your own stories")
    
    # Soft delete
    story.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}


@router.post("/{story_id}/view", response_model=ViewResponse)
async def record_view(story_id: UUID, db: Session = Depends(get_db)):
    """Record a story view"""
    
    story = db.query(Story).filter(Story.id == story_id, Story.deleted_at.is_(None)).first()
    if not story:
        raise NotFoundException("Story", story_id)
    
    story.views += 1
    db.commit()
    
    return ViewResponse()


@router.post("/{story_id}/like", response_model=LikeResponse)
async def like_story(
    story_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Like/unlike a story"""
    
    story = db.query(Story).filter(Story.id == story_id, Story.deleted_at.is_(None)).first()
    if not story:
        raise NotFoundException("Story", story_id)
    
    existing_like = db.query(Like).filter(
        Like.user_id == current_user_id,
        Like.story_id == story_id
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        story.likes -= 1
        liked = False
    else:
        # Like
        new_like = Like(user_id=current_user_id, story_id=story_id)
        db.add(new_like)
        story.likes += 1
        liked = True
    
    db.commit()
    db.refresh(story)
    
    return LikeResponse(liked=liked, likesCount=story.likes)


@router.post("/{story_id}/save", response_model=SaveResponse)
async def save_story(
    story_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Save/unsave a story"""
    
    story = db.query(Story).filter(Story.id == story_id, Story.deleted_at.is_(None)).first()
    if not story:
        raise NotFoundException("Story", story_id)
    
    existing_save = db.query(Save).filter(
        Save.user_id == current_user_id,
        Save.story_id == story_id
    ).first()
    
    if existing_save:
        # Unsave
        db.delete(existing_save)
        story.saves -= 1
        saved = False
    else:
        # Save
        new_save = Save(user_id=current_user_id, story_id=story_id)
        db.add(new_save)
        story.saves += 1
        saved = True
    
    db.commit()
    
    return SaveResponse(saved=saved)
