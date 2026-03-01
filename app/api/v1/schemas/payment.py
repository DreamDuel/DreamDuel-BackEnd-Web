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
    id: str
    userId: str
    paypalOrderId: Optional[str] = None
    amount: float
    currency: str = "USD"
    quantity: int = 1
    itemType: str = "image_generation"
    status: str
    createdAt: datetime
    
    class Config:
        from_attributes = True


# New schemas for pay-per-image model

class ImagePackage(BaseModel):
    """Image package schema"""
    id: str
    name: str
    images: int
    price: float
    currency: str = "USD"
    discount: Optional[str] = None


class BuyImagesRequest(BaseModel):
    """Buy images request"""
    packageId: str = Field(..., min_length=1)
    returnUrl: Optional[str] = None
    cancelUrl: Optional[str] = None


class BuyImagesResponse(BaseModel):
    """Buy images response"""
    orderId: str
    approvalUrl: str
    status: str


class PaymentConfirmRequest(BaseModel):
    """Payment confirmation request"""
    orderId: str = Field(..., min_length=1)


class PaymentConfirmResponse(BaseModel):
    """Payment confirmation response"""
    success: bool
    message: str
    imagesAdded: int
    totalImagesAvailable: int


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
