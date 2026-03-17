"""SQLAlchemy database models - Simplified for imagen generation only"""

import uuid
import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, Text, DateTime, 
    ForeignKey, Enum, JSON, UniqueConstraint, Index, Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.database.session import Base


# Enums
class SubscriptionStatusEnum(str, enum.Enum):
    """Subscription status options"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    INCOMPLETE = "incomplete"


# Models
class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    profile_picture = Column(String(500), nullable=True)  # For OAuth profile pictures
    bio = Column(Text, nullable=True)
    is_premium = Column(Boolean, default=False, nullable=False)  # Deprecated - kept for compatibility
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # OAuth fields
    oauth_provider = Column(String(50), nullable=True)  # "google", "apple", etc.
    oauth_id = Column(String(255), nullable=True)  # User ID from OAuth provider
    
    # Referral system
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    referred_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Image generation tracking - $1 per image (all paid)
    total_images_generated = Column(Integer, default=0, nullable=False)  # Total images generated
    
    # Deprecated fields (kept for backward compatibility - will be removed in future)
    paid_images_count = Column(Integer, default=0, nullable=False)  # DEPRECATED
    is_premium = Column(Boolean, default=False, nullable=False)  # DEPRECATED
    free_images_left = Column(Integer, default=10, nullable=False)  # DEPRECATED
    free_images_reset_at = Column(DateTime(timezone=True), nullable=True)  # DEPRECATED
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    referred_by = relationship("User", remote_side=[id], backref="referrals")
    generated_images = relationship("GeneratedImage", back_populates="user")
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    invoices = relationship("Invoice", back_populates="user")
    analytics_events = relationship("AnalyticsEvent", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"


class GeneratedImage(Base):
    """Generated Image model - stores AI-generated images"""
    __tablename__ = "generated_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for guest users
    session_id = Column(String(255), nullable=True, index=True)  # For guest checkout tracking
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=False)
    style = Column(String(100), nullable=True)
    aspect_ratio = Column(String(20), nullable=True)
    generation_id = Column(String(100), nullable=True)  # Reference to AI service generation
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="generated_images")
    
    __table_args__ = (
        Index('ix_generated_images_created_at_desc', created_at.desc()),
        Index('ix_generated_images_user_created', user_id, created_at.desc()),
    )
    
    def __repr__(self):
        return f"<GeneratedImage {self.id}>"


class Follow(Base):
    """Follow model (user following relationships)"""
    __tablename__ = "follows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    following_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")
    
    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='uq_follower_following'),
    )
    
    def __repr__(self):
        return f"<Follow {self.follower_id} -> {self.following_id}>"


class Subscription(Base):
    """Subscription model (PayPal subscriptions)"""
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Payment Provider fields
    provider_subscription_id = Column(String(100), unique=True, nullable=True)
    
    # Common fields
    plan_id = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # ACTIVE, CANCELLED, SUSPENDED, APPROVAL_PENDING, etc.
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    
    def __repr__(self):
        return f"<Subscription {self.provider_subscription_id} for User {self.user_id}>"


class Invoice(Base):
    """Invoice model - Payment for individual images"""
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for guest checkout
    session_id = Column(String(255), nullable=True, index=True)  # For guest checkout tracking
    
    # Payment Provider fields
    provider_order_id = Column(String(100), unique=True, nullable=True)
    provider_payment_id = Column(String(100), unique=True, nullable=True)
    
    # Payment details
    item_type = Column(String(50), default="image_generation", nullable=False)  # Type of purchase
    quantity = Column(Integer, default=1, nullable=False)  # Number of images purchased
    amount = Column(Float, nullable=False)  # Total amount paid
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(String(50), nullable=False)  # PENDING, COMPLETED, FAILED, REFUNDED
    invoice_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    
    def __repr__(self):
        return f"<Invoice {self.provider_order_id} - {self.quantity} image(s)>"


class AnalyticsEvent(Base):
    """Analytics event model"""
    __tablename__ = "analytics_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")
    
    __table_args__ = (
        Index('ix_analytics_event_type_created', event_type, created_at.desc()),
    )
    
    def __repr__(self):
        return f"<AnalyticsEvent {self.event_type}>"
