"""Validation utilities"""

import re
from typing import Optional
from fastapi import HTTPException, status


def validate_username(username: str) -> str:
    """
    Validate username
    - 3-50 characters
    - Alphanumeric, underscore, hyphen only
    - Cannot start/end with special characters
    """
    if not username or len(username) < 3 or len(username) > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be between 3 and 50 characters"
        )
    
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username can only contain letters, numbers, underscores, and hyphens"
        )
    
    return username.lower()


def validate_email(email: str) -> str:
    """Validate email format"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_regex, email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format"
        )
    
    return email.lower()


def validate_password(password: str) -> str:
    """
    Validate password strength
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long"
        )
    
    if not re.search(r'[A-Z]', password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one uppercase letter"
        )
    
    if not re.search(r'[a-z]', password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one lowercase letter"
        )
    
    if not re.search(r'\d', password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one number"
        )
    
    return password


def validate_referral_code(code: str) -> bool:
    """Validate referral code format"""
    # Referral codes should be 6-20 alphanumeric characters
    return bool(re.match(r'^[A-Z0-9]{6,20}$', code.upper()))


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input to prevent XSS
    - Strip leading/trailing whitespace
    - Remove null bytes
    - Limit length if specified
    """
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Strip whitespace
    text = text.strip()
    
    # Limit length
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_tags(tags: list[str]) -> list[str]:
    """
    Validate story tags
    - Max 10 tags
    - Each tag 2-30 characters
    - Alphanumeric and spaces only
    """
    if len(tags) > 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum 10 tags allowed"
        )
    
    validated_tags = []
    for tag in tags:
        tag = tag.strip().lower()
        
        if len(tag) < 2 or len(tag) > 30:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tag '{tag}' must be between 2 and 30 characters"
            )
        
        if not re.match(r'^[a-z0-9\s]+$', tag):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tag '{tag}' can only contain letters, numbers, and spaces"
            )
        
        validated_tags.append(tag)
    
    return validated_tags


def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_regex = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return bool(re.match(url_regex, url))
