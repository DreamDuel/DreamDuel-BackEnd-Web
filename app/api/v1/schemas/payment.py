"""Payment schemas"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class SubscriptionPlanSchema(BaseModel):
    """Subscription plan schema"""
    id: str
    name: str
    price: int  # in cents
    interval: str  # 'month' or 'year'
    features: List[str]
    stripe_price_id: str


class SubscribeRequest(BaseModel):
    """Subscribe request"""
    planId: str = Field(..., min_length=1)


class SubscribeResponse(BaseModel):
    """Subscribe response"""
    clientSecret: str
    subscriptionId: str


class SubscriptionStatusResponse(BaseModel):
    """Subscription status response"""
    active: bool
    plan: Optional[str] = None
    currentPeriodEnd: Optional[datetime] = None
    cancelAtPeriodEnd: bool = False


class PaymentMethodRequest(BaseModel):
    """Payment method request"""
    paymentMethodId: str = Field(..., min_length=1)


class PaymentMethodResponse(BaseModel):
    """Payment method response"""
    success: bool = True
    message: str = "Payment method updated"


class InvoiceSchema(BaseModel):
    """Invoice schema"""
    id: UUID
    stripe_invoice_id: str
    amount: int  # in cents
    status: str
    invoice_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PortalResponse(BaseModel):
    """Stripe customer portal response"""
    url: str


class CancelSubscriptionResponse(BaseModel):
    """Cancel subscription response"""
    success: bool = True
    message: str = "Subscription will be canceled at period end"


class ReactivateSubscriptionResponse(BaseModel):
    """Reactivate subscription response"""
    success: bool = True
    message: str = "Subscription reactivated"
