"""Payment schemas (PayPal compatible)"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class SubscriptionPlanSchema(BaseModel):
    """Subscription plan schema"""
    id: str
    name: str
    price: int  # in cents
    currency: str = "usd"
    interval: str  # 'month' or 'year'
    features: List[str]
    paypal_plan_id: Optional[str] = None


class SubscribeRequest(BaseModel):
    """Subscribe request"""
    planId: str = Field(..., min_length=1)
    returnUrl: Optional[str] = None  # For PayPal redirect after approval
    cancelUrl: Optional[str] = None  # For PayPal redirect on cancel


class SubscribeResponse(BaseModel):
    """Subscribe response"""
    subscriptionId: str
    # For PayPal: approval URL where user completes payment
    approvalUrl: Optional[str] = None
    status: Optional[str] = None


class ConfirmSubscriptionRequest(BaseModel):
    """Confirm subscription request (after PayPal approval)"""
    subscriptionId: str = Field(..., min_length=1)


class SubscriptionStatusResponse(BaseModel):
    """Subscription status response"""
    active: bool
    subscriptionId: Optional[str] = None
    status: Optional[str] = None
    planId: Optional[str] = None
    nextBillingTime: Optional[str] = None  # ISO 8601 datetime string
    # Legacy fields for backward compatibility
    plan: Optional[str] = None
    currentPeriodEnd: Optional[datetime] = None
    cancelAtPeriodEnd: bool = False


class CancelSubscriptionRequest(BaseModel):
    """Cancel subscription request"""
    immediate: bool = False
    reason: Optional[str] = "Customer request"


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
    paypal_sale_id: Optional[str] = None
    amount: float
    currency: str = "USD"
    status: str
    invoice_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PortalResponse(BaseModel):
    """Payment provider customer portal response"""
    url: str


class CancelSubscriptionResponse(BaseModel):
    """Cancel subscription response"""
    success: bool = True
    message: str = "Subscription cancelled successfully"
    status: Optional[str] = None


class ReactivateSubscriptionResponse(BaseModel):
    """Reactivate subscription response"""
    success: bool = True
    message: str = "Subscription reactivated"
    status: Optional[str] = None
