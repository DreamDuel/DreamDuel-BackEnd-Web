"""Helper utilities"""

import secrets
import string
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID


def generate_referral_code(length: int = 8) -> str:
    """Generate a unique referral code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def parse_uuid(uuid_str: str) -> Optional[UUID]:
    """Safely parse UUID from string"""
    try:
        return UUID(uuid_str)
    except (ValueError, AttributeError):
        return None


def get_month_start() -> datetime:
    """Get the start of the current month"""
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)


def get_month_end() -> datetime:
    """Get the end of the current month (start of next month)"""
    now = datetime.utcnow()
    if now.month == 12:
        return datetime(now.year + 1, 1, 1)
    return datetime(now.year, now.month + 1, 1)


def get_next_month_start() -> datetime:
    """Get the start of next month"""
    return get_month_end()


def calculate_reset_date() -> datetime:
    """Calculate when free images should reset (start of next month)"""
    return get_next_month_start()


def is_valid_image_extension(filename: str) -> bool:
    """Check if filename has valid image extension"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif'}
    return any(filename.lower().endswith(ext) for ext in valid_extensions)


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case"""
    import re
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase"""
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to max length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_number(num: int) -> str:
    """Format number with K/M suffix (e.g., 1500 -> 1.5K)"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def get_trending_score(views: int, likes: int, created_at: datetime) -> float:
    """
    Calculate trending score for stories
    Factors: views, likes, and recency
    """
    # Hours since creation
    hours_old = (datetime.utcnow() - created_at).total_seconds() / 3600
    
    # Prevent division by zero
    if hours_old < 1:
        hours_old = 1
    
    # Score formula: (views + likes * 2) / hours_old
    # More recent stories with more engagement rank higher
    score = (views + (likes * 2)) / hours_old
    
    return score


def extract_cloudinary_public_id(url: str) -> Optional[str]:
    """Extract Cloudinary public ID from URL"""
    # Example: https://res.cloudinary.com/cloud/image/upload/v123/folder/filename.jpg
    # Public ID: folder/filename
    try:
        parts = url.split('/upload/')
        if len(parts) == 2:
            # Remove version prefix (v123456/)
            path = parts[1]
            if path.startswith('v'):
                path = '/'.join(path.split('/')[1:])
            # Remove file extension
            if '.' in path:
                path = path.rsplit('.', 1)[0]
            return path
    except:
        pass
    return None
