"""Payment routes - $1 per image model"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from app.core.dependencies import get_current_user_id
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User, Invoice
from app.api.v1.schemas.payment import (
    BuyImagesRequest, BuyImagesResponse, 
    PaymentConfirmRequest, PaymentConfirmResponse,
    InvoiceSchema
)
from app.core.exceptions import NotFoundException, PaymentException
from app.infrastructure.external_services.paypal_service import paypal_service
from app.core.config import settings

router = APIRouter()


# Single image price - $1 USD
IMAGE_PRICE = 1.00
CURRENCY = "USD"


@router.post("/purchase-image", response_model=BuyImagesResponse)
async def purchase_single_image(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Purchase a single image generation for $1 USD
    
    Creates a PayPal order and returns approval URL
    """
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # Create PayPal order for $1
    try:
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "description": "DreamDuel - AI Image Generation",
                "amount": {
                    "currency_code": CURRENCY,
                    "value": str(IMAGE_PRICE)
                },
                "custom_id": f"{current_user_id}:single_image"
            }],
            "application_context": {
                "brand_name": "DreamDuel",
                "return_url": f"{settings.FRONTEND_URL}/payment/success",
                "cancel_url": f"{settings.FRONTEND_URL}/payment/cancel"
            }
        }
        
        # Create order via PayPal
        result = paypal_service.create_order(order_data)
        
        # Save pending invoice to database
        invoice = Invoice(
            user_id=current_user_id,
            paypal_order_id=result["order_id"],
            item_type="image_generation",
            quantity=1,
            amount=IMAGE_PRICE,
            currency=CURRENCY,
            status="PENDING"
        )
        db.add(invoice)
        db.commit()
        
        return BuyImagesResponse(
            orderId=result["order_id"],
            approvalUrl=result["approval_url"],
            status="PENDING"
        )
        
    except Exception as e:
        raise PaymentException(f"Failed to create payment order: {str(e)}")


@router.post("/confirm-payment", response_model=PaymentConfirmResponse)
async def confirm_payment(
    data: PaymentConfirmRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Confirm payment after user approves on PayPal
    
    Marks payment as completed - user can now generate the image
    """
    
    # Find invoice
    invoice = db.query(Invoice).filter(
        Invoice.user_id == current_user_id,
        Invoice.paypal_order_id == data.orderId
    ).first()
    
    if not invoice:
        raise NotFoundException("Invoice", data.orderId)
    
    if invoice.status == "COMPLETED":
        return PaymentConfirmResponse(
            success=True,
            message="Payment already confirmed",
            imagesAdded=1,
            totalImagesAvailable=0  # Not tracking balance anymore
        )
    
    # Capture payment via PayPal
    try:
        capture_result = paypal_service.capture_order(data.orderId)
        
        # Update invoice status
        invoice.paypal_capture_id = capture_result.get("capture_id")
        invoice.status = "COMPLETED"
        
        db.commit()
        
        return PaymentConfirmResponse(
            success=True,
            message="Payment successful! You can now generate your image.",
            imagesAdded=1,
            totalImagesAvailable=0  # Not tracking balance
        )
        
    except Exception as e:
        invoice.status = "FAILED"
        db.commit()
        raise PaymentException(f"Failed to capture payment: {str(e)}")


@router.get("/invoices", response_model=List[InvoiceSchema])
async def get_invoices(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get user's payment history"""
    
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user_id
    ).order_by(Invoice.created_at.desc()).limit(limit).all()
    
    return [
        InvoiceSchema(
            id=str(inv.id),
            userId=str(inv.user_id),
            amount=inv.amount,
            currency=inv.currency,
            quantity=inv.quantity,
            itemType=inv.item_type,
            status=inv.status,
            paypalOrderId=inv.paypal_order_id,
            createdAt=inv.created_at
        )
        for inv in invoices
    ]


@router.post("/webhook")
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    """
    PayPal webhook handler for payment notifications
    
    This handles asynchronous payment confirmations from PayPal
    """
    
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # Verify webhook signature (important for security)
        # paypal_service.verify_webhook_signature(headers, body)
        
        event = json.loads(body)
        event_type = event.get("event_type")
        
        if event_type == "CHECKOUT.ORDER.APPROVED":
            # Order was approved by user
            order_id = event["resource"]["id"]
            
            invoice = db.query(Invoice).filter(
                Invoice.paypal_order_id == order_id
            ).first()
            
            if invoice and invoice.status == "PENDING":
                # Auto-capture the order
                capture_result = paypal_service.capture_order(order_id)
                
                invoice.paypal_capture_id = capture_result.get("capture_id")
                invoice.status = "COMPLETED"
                
                # Add image credits
                user = db.query(User).filter(User.id == invoice.user_id).first()
                if user:
                    user.paid_images_count += invoice.quantity
                
                db.commit()
        
        elif event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Payment was captured successfully
            capture_id = event["resource"]["id"]
            
            invoice = db.query(Invoice).filter(
                Invoice.paypal_capture_id == capture_id
            ).first()
            
            if invoice:
                invoice.status = "COMPLETED"
                db.commit()
        
        elif event_type == "PAYMENT.CAPTURE.REFUNDED":
            # Payment was refunded
            capture_id = event["resource"]["id"]
            
            invoice = db.query(Invoice).filter(
                Invoice.paypal_capture_id == capture_id
            ).first()
            
            if invoice:
                invoice.status = "REFUNDED"
                
                # Deduct image credits
                user = db.query(User).filter(User.id == invoice.user_id).first()
                if user:
                    user.paid_images_count = max(0, user.paid_images_count - invoice.quantity)
                
                db.commit()
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions", response_model=List[InvoiceSchema])
async def get_transactions(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get user's payment history / transactions"""
    
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user_id
    ).order_by(Invoice.created_at.desc()).limit(limit).all()
    
    return [
        InvoiceSchema(
            id=str(inv.id),
            userId=str(inv.user_id),
            amount=inv.amount,
            currency=inv.currency,
            quantity=inv.quantity,
            itemType=inv.item_type,
            status=inv.status,
            paypalOrderId=inv.paypal_order_id,
            createdAt=inv.created_at
        )
        for inv in invoices
    ]

