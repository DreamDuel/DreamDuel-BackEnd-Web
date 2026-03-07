"""User routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.dependencies import get_current_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User, Follow
from app.api.v1.schemas.user import (
    UserProfileSchema, PublicUserProfileSchema, UserUpdate,
    UserAvatarUpdate, FollowResponse, CreditsResponse,
    UseCreditsResponse, ReferralResponse, ApplyReferralRequest,
    UserMeSchema
)
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.utils.helpers import calculate_reset_date
from datetime import datetime

router = APIRouter()


@router.get("/me", response_model=UserProfileSchema)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current authenticated user profile"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)
    
    # Get stats
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    
    return UserProfileSchema(
        **user.__dict__,
        followers_count=followers_count,
        following_count=following_count,
        stories_count=0
    )


@router.get("/me/simple", response_model=UserMeSchema)
async def get_current_user_simple(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user - simplified format for frontend compatibility"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)
    
    return UserMeSchema.from_user(user)


@router.get("/{user_id}", response_model=PublicUserProfileSchema)
async def get_user_profile(user_id: UUID, db: Session = Depends(get_db)):
    """Get public user profile"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)
    
    # Get stats
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    
    return PublicUserProfileSchema(
        **user.__dict__,
        followers_count=followers_count,
        following_count=following_count,
        stories_count=0
    )


@router.put("/{user_id}", response_model=UserProfileSchema)
async def update_user_profile(
    user_id: UUID,
    data: UserUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    if str(user_id) != current_user_id:
        raise ForbiddenException("You can only update your own profile")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)
    
    # Update fields
    if data.username:
        # Check if username is already taken
        existing = db.query(User).filter(
            User.username == data.username.lower(),
            User.id != user_id
        ).first()
        if existing:
            raise ConflictException("User", "username", data.username)
        user.username = data.username.lower()
    
    if data.bio is not None:
        user.bio = data.bio
    
    if data.avatar_url is not None:
        user.avatar_url = data.avatar_url
    
    db.commit()
    db.refresh(user)
    
    # Get stats
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    
    return UserProfileSchema(
        **user.__dict__,
        followers_count=followers_count,
        following_count=following_count,
        stories_count=0
    )


@router.put("/{user_id}/avatar", response_model=UserProfileSchema)
async def update_avatar(
    user_id: UUID,
    data: UserAvatarUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update user avatar"""
    
    if str(user_id) != current_user_id:
        raise ForbiddenException("You can only update your own avatar")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)
    
    user.avatar_url = data.avatarUrl
    db.commit()
    db.refresh(user)
    
    # Get stats
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    
    return UserProfileSchema(
        **user.__dict__,
        followers_count=followers_count,
        following_count=following_count,
        stories_count=0
    )


@router.post("/{user_id}/follow", response_model=FollowResponse)
async def follow_user(
    user_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Follow a user"""
    
    if str(user_id) == current_user_id:
        raise ForbiddenException("You cannot follow yourself")
    
    # Check if user exists
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise NotFoundException("User", user_id)
    
    # Check if already following
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user_id,
        Follow.following_id == user_id
    ).first()
    
    if not existing_follow:
        new_follow = Follow(
            follower_id=current_user_id,
            following_id=user_id
        )
        db.add(new_follow)
        db.commit()
    
    followers_count = db.query(Follow).filter(Follow.following_id == user_id).count()
    
    return FollowResponse(following=True, followersCount=followers_count)


@router.post("/{user_id}/unfollow", response_model=FollowResponse)
async def unfollow_user(
    user_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Unfollow a user"""
    
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user_id,
        Follow.following_id == user_id
    ).first()
    
    if existing_follow:
        db.delete(existing_follow)
        db.commit()
    
    followers_count = db.query(Follow).filter(Follow.following_id == user_id).count()
    
    return FollowResponse(following=False, followersCount=followers_count)


@router.get("/{user_id}/followers", response_model=List[PublicUserProfileSchema])
async def get_followers(user_id: UUID, db: Session = Depends(get_db)):
    """Get user's followers"""
    
    follows = db.query(Follow).filter(Follow.following_id == user_id).all()
    follower_ids = [f.follower_id for f in follows]
    
    users = db.query(User).filter(User.id.in_(follower_ids)).all()
    
    return [
        PublicUserProfileSchema(
            **user.__dict__,
            followers_count=db.query(Follow).filter(Follow.following_id == user.id).count(),
            following_count=db.query(Follow).filter(Follow.follower_id == user.id).count(),
            stories_count=0
        )
        for user in users
    ]


@router.get("/{user_id}/following", response_model=List[PublicUserProfileSchema])
async def get_following(user_id: UUID, db: Session = Depends(get_db)):
    """Get users that this user is following"""
    
    follows = db.query(Follow).filter(Follow.follower_id == user_id).all()
    following_ids = [f.following_id for f in follows]
    
    users = db.query(User).filter(User.id.in_(following_ids)).all()
    
    return [
        PublicUserProfileSchema(
            **user.__dict__,
            followers_count=db.query(Follow).filter(Follow.following_id == user.id).count(),
            following_count=db.query(Follow).filter(Follow.follower_id == user.id).count(),
            stories_count=0
        )
        for user in users
    ]


@router.get("/me/credits", response_model=CreditsResponse)
async def get_credits(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get user's image generation status
    
    All images cost $1 each (no free images)
    """
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # No free images in new model
    return CreditsResponse(
        freeImagesLeft=0,  # No free images
        resetAt=None,  # No reset in new model
        isPremium=False  # No premium tier
    )


@router.post("/me/credits/use", response_model=UseCreditsResponse)
async def use_credits(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    [DEPRECATED] No free images available - all cost $1
    
    This endpoint is kept for backward compatibility only.
    """
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # No free images available
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail="No free images available. Please purchase for $1 at /payments/purchase-image"
    )


@router.post("/me/referral/apply", response_model=ReferralResponse)
async def apply_referral(
    data: ApplyReferralRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """[DEPRECATED] Referral system disabled in new model"""
    
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Referral system is no longer available"
    )

