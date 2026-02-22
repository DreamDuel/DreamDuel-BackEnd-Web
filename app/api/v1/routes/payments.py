"""Payment routes (Stripe)"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_current_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User, Subscription, Invoice
from app.api.v1.schemas.payment import (
    SubscriptionPlanSchema, SubscribeRequest, SubscribeResponse,
    SubscriptionStatusResponse, PaymentMethodRequest, PaymentMethodResponse,
    InvoiceSchema, PortalResponse, CancelSubscriptionResponse,
    ReactivateSubscriptionResponse
)
from app.core.exceptions import NotFoundException, StripeException
from app.infrastructure.external_services.stripe_service import stripe_service

router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanSchema])
async def get_plans():
    """Get available subscription plans"""
    return stripe_service.get_plans()


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(
    data: SubscribeRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new subscription"""
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # Get or create Stripe customer
    subscription_record = db.query(Subscription).filter(Subscription.user_id == current_user_id).first()
    
    if not subscription_record:
        # Create Stripe customer
        customer = stripe_service.create_customer(
            email=user.email,
            name=user.username,
            metadata={"user_id": str(user.id)}
        )
        
        customer_id = customer.id
    else:
        customer_id = subscription_record.stripe_customer_id
    
    # Get price ID
    plans = stripe_service.get_plans()
    price_id = next((p["stripe_price_id"] for p in plans if p["id"] == data.planId), None)
    
    if not price_id:
        raise NotFoundException("Plan", data.planId)
    
    # Create subscription
    subscription = stripe_service.create_subscription(customer_id, price_id)
    
    # Save to database
    if subscription_record:
        subscription_record.stripe_subscription_id = subscription.id
        subscription_record.plan_id = data.planId
        subscription_record.status = subscription.status
        subscription_record.current_period_start = subscription.current_period_start
        subscription_record.current_period_end = subscription.current_period_end
    else:
        subscription_record = Subscription(
            user_id=current_user_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription.id,
            plan_id=data.planId,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end
        )
        db.add(subscription_record)
    
    # Update user premium status
    if subscription.status == "active":
        user.is_premium = True
    
    db.commit()
    
    # Get client secret for payment
    client_secret = subscription.latest_invoice.payment_intent.client_secret
    
    return SubscribeResponse(
        clientSecret=client_secret,
        subscriptionId=subscription.id
    )


@router.get("/subscription/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get subscription status"""
    
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user_id).first()
    
    if not subscription:
        return SubscriptionStatusResponse(active=False)
    
    return SubscriptionStatusResponse(
        active=subscription.status == "active",
        plan=subscription.plan_id,
        currentPeriodEnd=subscription.current_period_end,
        cancelAtPeriodEnd=subscription.cancel_at_period_end
    )


@router.post("/subscription/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Cancel subscription at period end"""
    
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user_id).first()
    if not subscription:
        raise NotFoundException("Subscription", current_user_id)
    
    stripe_service.cancel_subscription(subscription.stripe_subscription_id, at_period_end=True)
    
    subscription.cancel_at_period_end = True
    db.commit()
    
    return CancelSubscriptionResponse()


@router.post("/subscription/reactivate", response_model=ReactivateSubscriptionResponse)
async def reactivate_subscription(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Reactivate a canceled subscription"""
    
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user_id).first()
    if not subscription:
        raise NotFoundException("Subscription", current_user_id)
    
    stripe_service.reactivate_subscription(subscription.stripe_subscription_id)
    
    subscription.cancel_at_period_end = False
    db.commit()
    
    return ReactivateSubscriptionResponse()


@router.post("/payment-method", response_model=PaymentMethodResponse)
async def update_payment_method(
    data: PaymentMethodRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update payment method"""
    
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user_id).first()
    if not subscription:
        raise NotFoundException("Subscription", current_user_id)
    
    stripe_service.update_payment_method(subscription.stripe_customer_id, data.paymentMethodId)
    
    return PaymentMethodResponse()


@router.get("/invoices", response_model=List[InvoiceSchema])
async def get_invoices(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's invoices"""
    
    invoices = db.query(Invoice).filter(Invoice.user_id == current_user_id).order_by(Invoice.created_at.desc()).all()
    return invoices


@router.post("/portal", response_model=PortalResponse)
async def get_portal_url(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get Stripe Customer Portal URL"""
    
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user_id).first()
    if not subscription:
        raise NotFoundException("Subscription", current_user_id)
    
    session = stripe_service.create_portal_session(
        subscription.stripe_customer_id,
        return_url="https://dreamduel.com/account"
    )
    
    return PortalResponse(url=session.url)


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe_service.verify_webhook_signature(payload, sig_header)
    except Exception as e:
        raise StripeException(str(e))
    
    # Handle different event types
    if event["type"] == "invoice.paid":
        # Invoice paid successfully
        invoice = event["data"]["object"]
        
        # Save invoice to database
        new_invoice = Invoice(
            user_id=invoice.get("metadata", {}).get("user_id"),
            stripe_invoice_id=invoice["id"],
            amount=invoice["amount_paid"],
            status="paid",
            invoice_url=invoice.get("invoice_pdf")
        )
        db.add(new_invoice)
        db.commit()
    
    elif event["type"] == "customer.subscription.updated":
        # Subscription updated
        subscription = event["data"]["object"]
        
        db_subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription["id"]
        ).first()
        
        if db_subscription:
            db_subscription.status = subscription["status"]
            db_subscription.current_period_start = subscription["current_period_start"]
            db_subscription.current_period_end = subscription["current_period_end"]
            db_subscription.cancel_at_period_end = subscription["cancel_at_period_end"]
            
            # Update user premium status
            user = db.query(User).filter(User.id == db_subscription.user_id).first()
            if user:
                user.is_premium = subscription["status"] == "active"
            
            db.commit()
    
    elif event["type"] == "customer.subscription.deleted":
        # Subscription canceled
        subscription = event["data"]["object"]
        
        db_subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription["id"]
        ).first()
        
        if db_subscription:
            db_subscription.status = "canceled"
            
            # Update user premium status
            user = db.query(User).filter(User.id == db_subscription.user_id).first()
            if user:
                user.is_premium = False
            
            db.commit()
    
    return {"status": "success"}
