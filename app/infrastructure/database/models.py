"""SQLAlchemy database models"""

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
class VisibilityEnum(str, enum.Enum):
    """Story visibility options"""
    PUBLIC = "public"
    PRIVATE = "private"


class SubscriptionStatusEnum(str, enum.Enum):
    """Subscription status options"""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    INCOMPLETE = "incomplete"


class ReportStatusEnum(str, enum.Enum):
    """Report status options"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


# Models
class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    is_premium = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    referred_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    free_images_left = Column(Integer, default=10, nullable=False)
    free_images_reset_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    referred_by = relationship("User", remote_side=[id], backref="referrals")
    stories = relationship("Story", back_populates="author", foreign_keys="Story.author_id")
    comments = relationship("Comment", back_populates="user")
    likes = relationship("Like", back_populates="user")
    saves = relationship("Save", back_populates="user")
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    invoices = relationship("Invoice", back_populates="user")
    analytics_events = relationship("AnalyticsEvent", back_populates="user")
    reports_made = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
    
    def __repr__(self):
        return f"<User {self.username}>"


class Story(Base):
    """Story model"""
    __tablename__ = "stories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    synopsis = Column(Text, nullable=False)
    cover_url = Column(String(500), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    visibility = Column(Enum(VisibilityEnum), default=VisibilityEnum.PUBLIC, nullable=False)
    tags = Column(JSON, default=list, nullable=False)  # List[str]
    visual_style = Column(String(50), nullable=True)
    intensity = Column(Float, default=0.5, nullable=False)
    views = Column(Integer, default=0, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    saves = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    author = relationship("User", back_populates="stories", foreign_keys=[author_id])
    scenes = relationship("Scene", back_populates="story", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="story", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="story")
    likes_rel = relationship("Like", back_populates="story")
    saves_rel = relationship("Save", back_populates="story")
    reports = relationship("Report", back_populates="story")
    
    __table_args__ = (
        Index('ix_stories_created_at_desc', created_at.desc()),
    )
    
    def __repr__(self):
        return f"<Story {self.title}>"


class Scene(Base):
    """Scene model (part of a story)"""
    __tablename__ = "scenes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    text = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    generation_id = Column(String(100), nullable=True)  # Reference to AI generation
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    story = relationship("Story", back_populates="scenes")
    
    __table_args__ = (
        Index('ix_scenes_story_order', story_id, order),
    )
    
    def __repr__(self):
        return f"<Scene {self.order} of Story {self.story_id}>"


class Character(Base):
    """Character model (part of a story)"""
    __tablename__ = "characters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    photo_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    story = relationship("Story", back_populates="characters")
    
    def __repr__(self):
        return f"<Character {self.name}>"


class Comment(Base):
    """Comment model"""
    __tablename__ = "comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)  # For replies
    content = Column(Text, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    story = relationship("Story", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    likes_rel = relationship("Like", back_populates="comment")
    reports = relationship("Report", back_populates="comment")
    
    def __repr__(self):
        return f"<Comment by {self.user_id} on Story {self.story_id}>"


class Like(Base):
    """Like model (for stories and comments)"""
    __tablename__ = "likes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=True)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="likes")
    story = relationship("Story", back_populates="likes_rel")
    comment = relationship("Comment", back_populates="likes_rel")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'story_id', name='uq_user_story_like'),
        UniqueConstraint('user_id', 'comment_id', name='uq_user_comment_like'),
    )
    
    def __repr__(self):
        return f"<Like by {self.user_id}>"


class Save(Base):
    """Save model (saved/bookmarked stories)"""
    __tablename__ = "saves"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="saves")
    story = relationship("Story", back_populates="saves_rel")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'story_id', name='uq_user_story_save'),
    )
    
    def __repr__(self):
        return f"<Save by {self.user_id} for Story {self.story_id}>"


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
    """Subscription model (Stripe subscriptions)"""
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    stripe_customer_id = Column(String(100), unique=True, nullable=False)
    stripe_subscription_id = Column(String(100), unique=True, nullable=False)
    plan_id = Column(String(100), nullable=False)
    status = Column(Enum(SubscriptionStatusEnum), nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    
    def __repr__(self):
        return f"<Subscription {self.stripe_subscription_id} for User {self.user_id}>"


class Invoice(Base):
    """Invoice model (Stripe invoices)"""
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    stripe_invoice_id = Column(String(100), unique=True, nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in cents
    status = Column(String(50), nullable=False)
    invoice_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    
    def __repr__(self):
        return f"<Invoice {self.stripe_invoice_id}>"


class AnalyticsEvent(Base):
    """Analytics event model"""
    __tablename__ = "analytics_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")
    
    __table_args__ = (
        Index('ix_analytics_event_type_created', event_type, created_at.desc()),
    )
    
    def __repr__(self):
        return f"<AnalyticsEvent {self.event_type}>"


class Report(Base):
    """Report model (content reports)"""
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=True)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(Enum(ReportStatusEnum), default=ReportStatusEnum.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_made")
    story = relationship("Story", back_populates="reports")
    comment = relationship("Comment", back_populates="reports")
    
    def __repr__(self):
        return f"<Report by {self.reporter_id}>"
