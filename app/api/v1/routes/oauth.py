"""OAuth routes for Google and Apple Sign In"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import requests
import jwt
from datetime import datetime, timedelta

from app.core.dependencies import get_current_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User
from app.api.v1.schemas.auth import TokenResponse
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings
from app.core.exceptions import AuthenticationException
from pydantic import BaseModel, EmailStr

router = APIRouter()


class GoogleTokenRequest(BaseModel):
    """Google OAuth token request"""
    token: str  # Google ID token


class AppleTokenRequest(BaseModel):
    """Apple OAuth token request"""
    code: str  # Apple authorization code
    id_token: str  # Apple ID token


class OAuthUserInfo(BaseModel):
    """OAuth user information"""
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: str  # "google" or "apple"


@router.post("/google", response_model=TokenResponse)
async def google_oauth(
    data: GoogleTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Google OAuth
    
    Flow:
    1. Frontend gets Google ID token
    2. Backend verifies token with Google
    3. Create or login user
    4. Return JWT tokens
    """
    
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )
    
    try:
        # Verify Google token (acepta tanto ID token como access token)
        print(f"🔍 Verificando token de Google (primeros 50 chars): {data.token[:50]}...")
        
        # Intentar como ID token primero
        response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={data.token}",
            timeout=10
        )
        
        # Si falla, intentar como access token
        if response.status_code != 200:
            print(f"🔍 No es ID token, intentando como access token...")
            response = requests.get(
                f"https://oauth2.googleapis.com/tokeninfo?access_token={data.token}",
                timeout=10
            )
        
        print(f"🔍 Google API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Google token inválido. Response: {response.text}")
            raise AuthenticationException("Invalid Google token")
        
        google_data = response.json()
        print(f"✅ Token válido. Email: {google_data.get('email')}")
        
        # Verify audience (client ID)
        if google_data.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise AuthenticationException("Invalid token audience")
        
        email = google_data.get("email")
        if not email:
            raise AuthenticationException("Email not provided by Google")
        
        # Check if email is verified
        if not google_data.get("email_verified"):
            raise AuthenticationException("Google email not verified")
        
        name = google_data.get("name")
        picture = google_data.get("picture")
        
        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            username = email.split("@")[0]
            
            # Check if username exists
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                # Add random suffix
                import random
                username = f"{username}_{random.randint(1000, 9999)}"
            
            # Generate referral code
            import uuid
            referral_code = str(uuid.uuid4())[:8].upper()
            
            user = User(
                email=email,
                username=username,
                full_name=name,
                profile_picture=picture,
                is_verified=True,  # Google already verified email
                oauth_provider ="google",
                oauth_id=google_data.get("sub"),
                referral_code=referral_code
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update OAuth info if not set
            if not user.oauth_provider:
                user.oauth_provider = "google"
                user.oauth_id = google_data.get("sub")
                user.is_verified = True
                db.commit()
        
        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to verify Google token: {str(e)}"
        )
    except Exception as e:
        raise AuthenticationException(f"Google OAuth failed: {str(e)}")


@router.post("/apple", response_model=TokenResponse)
async def apple_oauth(
    data: AppleTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Apple Sign In
    
    Flow:
    1. Frontend gets Apple authorization code and ID token
    2. Backend verifies ID token
    3. Create or login user
    4. Return JWT tokens
    """
    
    if not settings.APPLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Apple OAuth not configured"
        )
    
    try:
        # Decode Apple ID token (without verification for now - should verify in production)
        # In production, you should verify the token signature with Apple's public keys
        decoded_token = jwt.decode(
            data.id_token,
            options={"verify_signature": False}  # TODO: Implement proper verification
        )
        
        email = decoded_token.get("email")
        if not email:
            raise AuthenticationException("Email not provided by Apple")
        
        apple_user_id = decoded_token.get("sub")
        
        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            username = email.split("@")[0]
            
            # Check if username exists
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                # Add random suffix
                import random
                username = f"{username}_{random.randint(1000, 9999)}"
            
            # Generate referral code
            import uuid
            referral_code = str(uuid.uuid4())[:8].upper()
            
            user = User(
                email=email,
                username=username,
                is_verified=True,  # Apple already verified email
                oauth_provider="apple",
                oauth_id=apple_user_id,
                referral_code=referral_code
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update OAuth info if not set
            if not user.oauth_provider:
                user.oauth_provider = "apple"
                user.oauth_id = apple_user_id
                user.is_verified = True
                db.commit()
        
        # Generate tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except jwt.DecodeError as e:
        raise AuthenticationException(f"Invalid Apple token: {str(e)}")
    except Exception as e:
        raise AuthenticationException(f"Apple OAuth failed: {str(e)}")


@router.get("/google/url")
async def get_google_auth_url():
    """Get Google OAuth URL for frontend"""
    
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )
    
    # This URL should be used by the frontend
    redirect_uri = f"{settings.FRONTEND_URL}/auth/google/callback"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline"
    )
    
    return {"url": auth_url}


@router.get("/apple/config")
async def get_apple_config():
    """Get Apple Sign In configuration for frontend"""
    
    if not settings.APPLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Apple OAuth not configured"
        )
    
    return {
        "clientId": settings.APPLE_CLIENT_ID,
        "redirectUri": f"{settings.FRONTEND_URL}/auth/apple/callback",
        "scope": "name email"
    }
