"""Comment routes"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from app.core.dependencies import get_current_user_id, get_optional_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Comment, Like, Story, User, Report
from app.api.v1.schemas.comment import (
    CommentCreate, CommentUpdate, CommentSchema,
    CommentLikeResponse, ReportCommentRequest, ReportResponse
)
from app.api.v1.schemas.user import PublicUserProfileSchema
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


@router.get("/story/{story_id}", response_model=List[CommentSchema])
async def get_story_comments(
    story_id: UUID,
    user_id: str = Depends(get_optional_user_id),
    db: Session = Depends(get_db)
):
    """Get all comments for a story (with nested replies)"""
    
    # Get top-level comments
    comments = db.query(Comment).filter(
        Comment.story_id == story_id,
        Comment.parent_id.is_(None),
        Comment.deleted_at.is_(None)
    ).order_by(Comment.created_at.desc()).all()
    
    def build_comment_tree(comment):
        """Recursively build comment with replies"""
        author = db.query(User).filter(User.id == comment.user_id).first()
        
        comment_schema = CommentSchema(**comment.__dict__)
        if author:
            comment_schema.user = PublicUserProfileSchema(**author.__dict__, followers_count=0, following_count=0, stories_count=0)
        
        # Check if user liked
        if user_id:
            comment_schema.is_liked = db.query(Like).filter(
                Like.user_id == user_id,
                Like.comment_id == comment.id
            ).first() is not None
        
        # Get replies
        replies = db.query(Comment).filter(
            Comment.parent_id == comment.id,
            Comment.deleted_at.is_(None)
        ).order_by(Comment.created_at).all()
        
        comment_schema.replies = [build_comment_tree(reply) for reply in replies]
        
        return comment_schema
    
    return [build_comment_tree(comment) for comment in comments]


@router.post("", response_model=CommentSchema, status_code=status.HTTP_201_CREATED)
async def create_comment(
    data: CommentCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new comment"""
    
    # Verify story exists
    story = db.query(Story).filter(Story.id == data.storyId, Story.deleted_at.is_(None)).first()
    if not story:
        raise NotFoundException("Story", data.storyId)
    
    # Verify parent comment exists if replying
    if data.parentId:
        parent = db.query(Comment).filter(Comment.id == data.parentId, Comment.deleted_at.is_(None)).first()
        if not parent:
            raise NotFoundException("Comment", data.parentId)
    
    new_comment = Comment(
        story_id=data.storyId,
        user_id=current_user_id,
        parent_id=data.parentId,
        content=data.content
    )
    
    db.add(new_comment)
    
    # Update comment count
    story.comments_count += 1
    
    db.commit()
    db.refresh(new_comment)
    
    # Get author
    author = db.query(User).filter(User.id == current_user_id).first()
    
    comment_schema = CommentSchema(**new_comment.__dict__)
    if author:
        comment_schema.user = PublicUserProfileSchema(**author.__dict__, followers_count=0, following_count=0, stories_count=0)
    
    return comment_schema


@router.put("/{comment_id}", response_model=CommentSchema)
async def update_comment(
    comment_id: UUID,
    data: CommentUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update a comment"""
    
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at.is_(None)).first()
    if not comment:
        raise NotFoundException("Comment", comment_id)
    
    if str(comment.user_id) != current_user_id:
        raise ForbiddenException("You can only edit your own comments")
    
    comment.content = data.content
    comment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(comment)
    
    # Get author
    author = db.query(User).filter(User.id == current_user_id).first()
    
    comment_schema = CommentSchema(**comment.__dict__)
    if author:
        comment_schema.user = PublicUserProfileSchema(**author.__dict__, followers_count=0, following_count=0, stories_count=0)
    
    return comment_schema


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a comment (soft delete)"""
    
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at.is_(None)).first()
    if not comment:
        raise NotFoundException("Comment", comment_id)
    
    if str(comment.user_id) != current_user_id:
        raise ForbiddenException("You can only delete your own comments")
    
    # Soft delete
    comment.deleted_at = datetime.utcnow()
    
    # Update comment count
    story = db.query(Story).filter(Story.id == comment.story_id).first()
    if story:
        story.comments_count -= 1
    
    db.commit()
    
    return {"success": True}


@router.post("/{comment_id}/like", response_model=CommentLikeResponse)
async def like_comment(
    comment_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Like/unlike a comment"""
    
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at.is_(None)).first()
    if not comment:
        raise NotFoundException("Comment", comment_id)
    
    existing_like = db.query(Like).filter(
        Like.user_id == current_user_id,
        Like.comment_id == comment_id
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        comment.likes -= 1
        liked = False
    else:
        # Like
        new_like = Like(user_id=current_user_id, comment_id=comment_id)
        db.add(new_like)
        comment.likes += 1
        liked = True
    
    db.commit()
    db.refresh(comment)
    
    return CommentLikeResponse(liked=liked, likesCount=comment.likes)


@router.post("/{comment_id}/report", response_model=ReportResponse)
async def report_comment(
    comment_id: UUID,
    data: ReportCommentRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Report a comment"""
    
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at.is_(None)).first()
    if not comment:
        raise NotFoundException("Comment", comment_id)
    
    new_report = Report(
        reporter_id=current_user_id,
        comment_id=comment_id,
        reason=data.reason
    )
    
    db.add(new_report)
    db.commit()
    
    return ReportResponse()
