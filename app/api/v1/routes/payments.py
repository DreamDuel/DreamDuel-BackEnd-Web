"""Payment routes (PayPal)"""

from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from app.core.dependencies import get_current_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User, Subscription as SubscriptionModel, Invoice
from app.api.v1.schemas.payment import (
    SubscriptionPlanSchema, SubscribeRequest, SubscribeResponse,
    SubscriptionStatusResponse, InvoiceSchema, CancelSubscriptionRequest,
    CancelSubscriptionResponse, ReactivateSubscriptionResponse, ConfirmSubscriptionRequest
)
from app.core.exceptions import NotFoundException, PaymentException
from app.infrastructure.external_services.paypal_service import paypal_service
from app.core.config import settings

router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanSchema])
async def get_plans():
    """Get available subscription plans"""
    return paypal_service.get_plans()


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(
    data: SubscribeRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new PayPal subscription
    
    This creates the subscription and returns an approval URL where
    the user must be redirected to complete the payment with PayPal
    """
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # Check if user already has an active subscription
    existing_subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == current_user_id,
        SubscriptionModel.status.in_(["ACTIVE", "APPROVED"])
    ).first()
    
    if existing_subscription:
        raise PaymentException("User already has an active subscription")
    
    # Get plan details
    plans = paypal_service.get_plans()
    plan = next((p for p in plans if p["id"] == data.planId), None)
    
    if not plan:
        raise NotFoundException("Plan", data.planId)
    
    plan_id = plan["paypal_plan_id"]
    
    if not plan_id:
        raise PaymentException(f"Plan {data.planId} is not configured with a PayPal Plan ID")
    
    # Create PayPal subscription
    try:
        result = paypal_service.create_subscription(
            plan_id=plan_id,
            return_url=data.returnUrl or f"{settings.FRONTEND_URL}/payment/success",
            cancel_url=data.cancelUrl or f"{settings.FRONTEND_URL}/payment/cancel",
            subscriber_email=user.email,
            subscriber_name=user.username
        )
        
        # Save subscription to database (initially in APPROVAL_PENDING status)
        subscription_record = SubscriptionModel(
            user_id=current_user_id,
            paypal_subscription_id=result["subscription_id"],
            plan_id=data.planId,
            status="APPROVAL_PENDING"
        )
        db.add(subscription_record)
        db.commit()
        
        return SubscribeResponse(
            subscriptionId=result["subscription_id"],
            approvalUrl=result["approval_url"],
            status=result["status"]
        )
        
    except Exception as e:
        raise PaymentException(f"Failed to create subscription: {str(e)}")


@router.post("/subscription/confirm")
async def confirm_subscription(
    data: ConfirmSubscriptionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Confirm subscription after user approves it on PayPal
    
    This should be called after the user returns from PayPal
    with the subscription_id
    """
    
    subscription_record = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == current_user_id,
        SubscriptionModel.paypal_subscription_id == data.subscriptionId
    ).first()
    
    if not subscription_record:
        raise NotFoundException("Subscription", data.subscriptionId)
    
    # Get subscription details from PayPal
    try:
        paypal_subscription = paypal_service.get_subscription(data.subscriptionId)
        
        # Update subscription in database
        subscription_record.status = paypal_subscription["status"]
        
        # Update user premium status if subscription is active
        if paypal_subscription["status"] == "ACTIVE":
            user = db.query(User).filter(User.id == current_user_id).first()
            if user:
                user.is_premium = True
        
        db.commit()
        
        return {
            "message": "Subscription confirmed successfully",
            "status": paypal_subscription["status"]
        }
        
    except Exception as e:
        raise PaymentException(f"Failed to confirm subscription: {str(e)}")


@router.get("/subscription/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current subscription status"""
    
    subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == current_user_id
    ).first()
    
    if not subscription or subscription.status not in ["ACTIVE", "APPROVED"]:
        return SubscriptionStatusResponse(
            active=False,
            subscriptionId=None,
            status=subscription.status if subscription else None,
            planId=None,
            nextBillingTime=None
        )
    
    # Get latest status from PayPal
    try:
        paypal_subscription = paypal_service.get_subscription(subscription.paypal_subscription_id)
        
        # Update local status
        subscription.status = paypal_subscription["status"]
        db.commit()
        
        return SubscriptionStatusResponse(
            active=paypal_subscription["status"] == "ACTIVE",
            subscriptionId=subscription.paypal_subscription_id,
            status=paypal_subscription["status"],
            planId=subscription.plan_id,
            nextBillingTime=paypal_subscription.get("billing_info", {}).get("next_billing_time")
        )
        
    except Exception as e:
        # Return local status if PayPal API fails
        return SubscriptionStatusResponse(
            active=subscription.status == "ACTIVE",
            subscriptionId=subscription.paypal_subscription_id,
            status=subscription.status,
            planId=subscription.plan_id,
            nextBillingTime=None
        )


@router.post("/subscription/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    data: CancelSubscriptionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Cancel active subscription"""
    
    subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == current_user_id
    ).first()
    
    if not subscription:
        raise NotFoundException("Subscription", current_user_id)
    
    if subscription.status not in ["ACTIVE", "APPROVED"]:
        raise PaymentException("No active subscription to cancel")
    
    try:
        result = paypal_service.cancel_subscription(
            subscription_id=subscription.paypal_subscription_id,
            reason=data.reason or "Customer request"
        )
        
        # Update database
        subscription.status = "CANCELLED"
        
        # Update user premium status
        user = db.query(User).filter(User.id == current_user_id).first()
        if user:
            user.is_premium = False
        
        db.commit()
        
        return CancelSubscriptionResponse(
            message="Subscription cancelled successfully",
            status="CANCELLED"
        )
        
    except Exception as e:
        raise PaymentException(f"Failed to cancel subscription: {str(e)}")


@router.post("/subscription/reactivate", response_model=ReactivateSubscriptionResponse)
async def reactivate_subscription(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Reactivate a suspended subscription"""
    
    subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == current_user_id
    ).first()
    
    if not subscription:
        raise NotFoundException("Subscription", current_user_id)
    
    if subscription.status != "SUSPENDED":
        raise PaymentException("Only suspended subscriptions can be reactivated")
    
    try:
        result = paypal_service.activate_subscription(
            subscription_id=subscription.paypal_subscription_id,
            reason="Reactivated by user"
        )
        
        # Update database
        subscription.status = "ACTIVE"
        
        # Update user premium status
        user = db.query(User).filter(User.id == current_user_id).first()
        if user:
            user.is_premium = True
        
        db.commit()
        
        return ReactivateSubscriptionResponse(
            message="Subscription reactivated successfully",
            status="ACTIVE"
        )
        
    except Exception as e:
        raise PaymentException(f"Failed to reactivate subscription: {str(e)}")


@router.get("/transactions", response_model=List[dict])
async def get_transactions(
    limit: int = 10,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get subscription transaction history"""
    
    subscription = db.query(SubscriptionModel).filter(
        SubscriptionModel.user_id == current_user_id
    ).first()
    
    if not subscription:
        return []
    
    # For now, return invoices from database
    # You can enhance this to fetch actual transactions from PayPal
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user_id
    ).order_by(Invoice.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": inv.id,
            "amount": inv.amount,
            "currency": "USD",
            "status": inv.status,
            "created_at": inv.created_at.isoformat()
        }
        for inv in invoices
    ]


@router.post("/webhook")
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle PayPal webhooks
    
    PayPal sends webhooks for various events like:
    - BILLING.SUBSCRIPTION.ACTIVATED
    - BILLING.SUBSCRIPTION.CANCELLED
    - BILLING.SUBSCRIPTION.SUSPENDED
    - PAYMENT.SALE.COMPLETED
    """
    
    # Get webhook headers
    transmission_id = request.headers.get("PAYPAL-TRANSMISSION-ID")
    timestamp = request.headers.get("PAYPAL-TRANSMISSION-TIME")
    webhook_id = settings.PAYPAL_WEBHOOK_ID
    cert_url = request.headers.get("PAYPAL-CERT-URL")
    transmission_sig = request.headers.get("PAYPAL-TRANSMISSION-SIG")
    auth_algo = request.headers.get("PAYPAL-AUTH-ALGO")
    
    # Get event body
    body = await request.body()
    event_body = body.decode("utf-8")
    
    # Verify webhook signature
    try:
        if webhook_id:
            is_valid = paypal_service.verify_webhook_signature(
                transmission_id=transmission_id,
                timestamp=timestamp,
                webhook_id=webhook_id,
                event_body=event_body,
                cert_url=cert_url,
                transmission_sig=transmission_sig,
                auth_algo=auth_algo
            )
            
            if not is_valid:
                raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception as e:
        # Log error but continue processing in development
        if settings.ENVIRONMENT == "production":
            raise HTTPException(status_code=400, detail=f"Webhook verification failed: {str(e)}")
    
    # Parse event
    event = json.loads(event_body)
    event_type = event.get("event_type")
    resource = event.get("resource", {})
    
    # Handle different event types
    if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        # Subscription activated
        subscription_id = resource.get("id")
        
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.paypal_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = "ACTIVE"
            
            # Update user premium status
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                user.is_premium = True
            
            db.commit()
    
    elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        # Subscription cancelled
        subscription_id = resource.get("id")
        
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.paypal_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = "CANCELLED"
            
            # Update user premium status
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                user.is_premium = False
            
            db.commit()
    
    elif event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
        # Subscription suspended (usually due to payment failure)
        subscription_id = resource.get("id")
        
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.paypal_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = "SUSPENDED"
            
            # Update user premium status
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                user.is_premium = False
            
            db.commit()
    
    elif event_type == "BILLING.SUBSCRIPTION.UPDATED":
        # Subscription updated
        subscription_id = resource.get("id")
        
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.paypal_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = resource.get("status", subscription.status)
            db.commit()
    
    elif event_type == "PAYMENT.SALE.COMPLETED":
        # Payment completed - create invoice record
        sale_id = resource.get("id")
        subscription_id = resource.get("billing_agreement_id")
        
        if subscription_id:
            subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.paypal_subscription_id == subscription_id
            ).first()
            
            if subscription:
                # Create invoice record
                invoice = Invoice(
                    user_id=subscription.user_id,
                    paypal_sale_id=sale_id,
                    amount=float(resource.get("amount", {}).get("total", 0)),
                    currency=resource.get("amount", {}).get("currency", "USD"),
                    status="paid"
                )
                db.add(invoice)
                db.commit()
    
    return {"status": "success"}
