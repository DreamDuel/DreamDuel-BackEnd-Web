"""Authentication routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User
from app.api.v1.schemas.auth import (
    RegisterRequest, LoginRequest, OAuthRequest,
    PasswordResetRequest, PasswordResetConfirmRequest,
    EmailVerificationRequest, RefreshTokenRequest,
    AuthResponse, LogoutResponse, MessageResponse
)
from app.api.v1.schemas.user import UserProfileSchema
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token,
    create_password_reset_token, verify_password_reset_token,
    create_email_verification_token, verify_email_verification_token
)
from app.core.exceptions import UnauthorizedException, ConflictException, NotFoundException
from app.infrastructure.external_services.email_service import email_service
from app.utils.helpers import generate_referral_code, calculate_reset_date
from datetime import datetime, timedelta

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if username already exists
    if db.query(User).filter(User.username == data.username.lower()).first():
        raise ConflictException("User", "username", data.username)
    
    # Check if email already exists
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise ConflictException("User", "email", data.email)
    
    # Handle referral code
    referred_by_user = None
    if data.referral_code:
        referred_by_user = db.query(User).filter(
            User.referral_code == data.referral_code.upper()
        ).first()
    
    # Create new user
    new_user = User(
        username=data.username.lower(),
        email=data.email.lower(),
        password_hash=get_password_hash(data.password),
        referral_code=generate_referral_code(),
        referred_by_id=referred_by_user.id if referred_by_user else None,
        free_images_left=15 if referred_by_user else 10,  # Bonus for referral
        free_images_reset_at=calculate_reset_date()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send verification email
    verification_token = create_email_verification_token(new_user.email)
    try:
        email_service.send_verification_email(
            to=new_user.email,
            username=new_user.username,
            verification_token=verification_token
        )
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        pass  # Don't fail registration if email fails
    
    # Create tokens
    access_token = create_access_token({"sub": str(new_user.id)})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})
    
    # Build user profile
    user_profile = UserProfileSchema(
        **new_user.__dict__,
        followers_count=0,
        following_count=0,
        stories_count=0
    )
    
    return AuthResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=user_profile
    )


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login with email/username and password"""
    
    # Find user by email or username
    user = db.query(User).filter(
        (User.email == data.emailOrUsername.lower()) |
        (User.username == data.emailOrUsername.lower())
    ).first()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise UnauthorizedException("Invalid credentials")
    
    # Create tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    # Get user stats
    from app.infrastructure.database.models import Follow
    followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
    
    user_profile = UserProfileSchema(
        **user.__dict__,
        followers_count=followers_count,
        following_count=following_count,
        stories_count=0
    )
    
    return AuthResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=user_profile
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(user_id: str = Depends(get_current_user_id)):
    """Logout (client should discard tokens)"""
    # In a production app, you might want to blacklist the token
    # For now, we rely on client-side token removal
    return LogoutResponse()


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token"""
    
    try:
        payload = decode_token(data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("User", user_id)
        
        # Create new tokens
        access_token = create_access_token({"sub": user_id})
        new_refresh_token = create_refresh_token({"sub": user_id})
        
        # Get user stats
        from app.infrastructure.database.models import Follow
        followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
        following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
        
        user_profile = UserProfileSchema(
            **user.__dict__,
            followers_count=followers_count,
            following_count=following_count,
            stories_count=0
        )
        
        return AuthResponse(
            token=access_token,
            refresh_token=new_refresh_token,
            user=user_profile
        )
        
    except Exception as e:
        raise UnauthorizedException(str(e))


@router.post("/password-reset", response_model=MessageResponse)
async def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset email"""
    
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    # Always return success to prevent email enumeration
    if user:
        reset_token = create_password_reset_token(user.email)
        try:
            email_service.send_password_reset_email(
                to=user.email,
                username=user.username,
                reset_token=reset_token
            )
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            pass  # Don't fail if email fails
    
    return MessageResponse(message="Password reset email sent if account exists")


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(data: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    """Confirm password reset with token"""
    
    email = verify_password_reset_token(data.token)
    if not email:
        raise UnauthorizedException("Invalid or expired reset token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise NotFoundException("User", email)
    
    # Update password
    user.password_hash = get_password_hash(data.newPassword)
    db.commit()
    
    return MessageResponse(message="Password updated successfully")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(data: EmailVerificationRequest, db: Session = Depends(get_db)):
    """Verify email with token"""
    
    email = verify_email_verification_token(data.token)
    if not email:
        raise UnauthorizedException("Invalid or expired verification token")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise NotFoundException("User", email)
    
    user.is_verified = True
    db.commit()
    
    # Send welcome email
    try:
        email_service.send_welcome_email(to=user.email, username=user.username)
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        pass
    
    return MessageResponse(message="Email verified successfully")


# Note: OAuth endpoints (Google/Apple) moved to /api/oauth/ routes
# See app/api/v1/routes/oauth.py for implementation
