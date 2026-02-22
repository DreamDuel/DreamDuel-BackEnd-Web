"""User routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.dependencies import get_current_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User, Story, Follow
from app.api.v1.schemas.user import (
    UserProfileSchema, PublicUserProfileSchema, UserUpdate,
    UserAvatarUpdate, FollowResponse, CreditsResponse,
    UseCreditsResponse, ReferralResponse, ApplyReferralRequest
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
    stories_count = db.query(Story).filter(Story.author_id == user.id, Story.deleted_at.is_(None)).count()
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    
    return UserProfileSchema(
        **user.__dict__,
        followers_count=followers_count,
        following_count=following_count,
        stories_count=stories_count
    )


@router.get("/{user_id}", response_model=PublicUserProfileSchema)
async def get_user_profile(user_id: UUID, db: Session = Depends(get_db)):
    """Get public user profile"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)
    
    # Get stats
    stories_count = db.query(Story).filter(Story.author_id == user.id, Story.deleted_at.is_(None)).count()
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    
    return PublicUserProfileSchema(
        **user.__dict__,
        followers_count=followers_count,
        following_count=following_count,
        stories_count=stories_count
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
    stories_count = db.query(Story).filter(Story.author_id == user.id, Story.deleted_at.is_(None)).count()
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    
    return UserProfileSchema(
        **user.__dict__,
        followers_count=followers_count,
        following_count=following_count,
        stories_count=stories_count
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
    stories_count = db.query(Story).filter(Story.author_id == user.id, Story.deleted_at.is_(None)).count()
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    
    return UserProfileSchema(
        **user.__dict__,
        followers_count=followers_count,
        following_count=following_count,
        stories_count=stories_count
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
            stories_count=db.query(Story).filter(Story.author_id == user.id, Story.deleted_at.is_(None)).count()
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
            stories_count=db.query(Story).filter(Story.author_id == user.id, Story.deleted_at.is_(None)).count()
        )
        for user in users
    ]


@router.get("/me/credits", response_model=CreditsResponse)
async def get_credits(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's remaining credits"""
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # Check if credits need to be reset
    if user.free_images_reset_at and datetime.utcnow() >= user.free_images_reset_at:
        user.free_images_left = 10  # Reset to default
        user.free_images_reset_at = calculate_reset_date()
        db.commit()
        db.refresh(user)
    
    return CreditsResponse(
        freeImagesLeft=user.free_images_left,
        resetAt=user.free_images_reset_at,
        isPremium=user.is_premium
    )


@router.post("/me/credits/use", response_model=UseCreditsResponse)
async def use_credits(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Use one image credit"""
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    if not user.is_premium and user.free_images_left <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No credits remaining. Upgrade to Premium for unlimited generations."
        )
    
    if not user.is_premium:
        user.free_images_left -= 1
        db.commit()
        db.refresh(user)
    
    return UseCreditsResponse(
        success=True,
        creditsLeft=user.free_images_left if not user.is_premium else -1  # -1 = unlimited
    )


@router.post("/me/referral/apply", response_model=ReferralResponse)
async def apply_referral(
    data: ApplyReferralRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Apply a referral code for bonus credits"""
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    if user.referred_by_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already used a referral code"
        )
    
    # Find referrer
    referrer = db.query(User).filter(
        User.referral_code == data.code.upper()
    ).first()
    
    if not referrer:
        raise NotFoundException("Referral code", data.code)
    
    if referrer.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot use your own referral code"
        )
    
    # Apply bonus
    bonus_credits = 5
    user.referred_by_id = referrer.id
    user.free_images_left += bonus_credits
    
    # Give referrer bonus too
    referrer.free_images_left += bonus_credits
    
    db.commit()
    
    return ReferralResponse(
        success=True,
        bonusCredits=bonus_credits,
        message=f"Referral code applied! You received {bonus_credits} bonus credits."
    )
