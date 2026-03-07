"""SQLAlchemy database models — Guest checkout only"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.database.session import Base


class GeneratedImage(Base):
    """Generated Image — stores AI-generated images"""
    __tablename__ = "generated_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)          # Null for guests
    session_id = Column(String(255), nullable=True, index=True)               # Guest tracking
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=False)
    style = Column(String(100), nullable=True)
    aspect_ratio = Column(String(20), nullable=True)
    generation_id = Column(String(100), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('ix_generated_images_user_created', user_id, created_at.desc()),
    )

    def __repr__(self):
        return f"<GeneratedImage {self.id}>"


class Invoice(Base):
    """Invoice — payment record for each image generation"""
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)           # Null for guests
    session_id = Column(String(255), nullable=True, index=True)               # Guest tracking

    # PayPal
    paypal_order_id = Column(String(100), unique=True, nullable=True)
    paypal_capture_id = Column(String(100), unique=True, nullable=True)

    # Payment details
    item_type = Column(String(50), default="image_generation", nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(String(50), nullable=False)                               # PENDING, COMPLETED, FAILED, REFUNDED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Invoice {self.paypal_order_id} — {self.status}>"
