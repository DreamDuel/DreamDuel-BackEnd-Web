"""FastAPI dependency injection functions"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User
from app.core.security import decode_token
from app.core.exceptions import AuthenticationException


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user"""
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise AuthenticationException("Invalid or expired token")
    
    # Check token type
    if payload.get("type") != "access":
        raise AuthenticationException("Invalid token type")
    
    # Get user ID from token
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise AuthenticationException("Invalid token payload")
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationException("User not found")
    
    if not user.isActive:
        raise AuthenticationException("User account is inactive")
    
    return user


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get the current user ID from token"""
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise AuthenticationException("Invalid or expired token")
    
    # Check token type
    if payload.get("type") != "access":
        raise AuthenticationException("Invalid token type")
    
    # Get user ID from token
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise AuthenticationException("Invalid token payload")
    
    return str(user_id)


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.isActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except:
        return None


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Get current user ID if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user_id(credentials)
    except:
        return None


def require_verified_email(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to have verified email"""
    if not current_user.isEmailVerified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


def require_subscription(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require user to have active subscription"""
    if current_user.subscriptionTier == "free":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Subscription required"
        )
    return current_user
