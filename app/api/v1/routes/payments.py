"""Payment routes - Guest checkout for $1 per image"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.dependencies import get_current_user_id  # Keep for legacy endpoints
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import User, Invoice, GeneratedImage
from app.api.v1.schemas.payment import (
    BuyImagesRequest, BuyImagesResponse, 
    PaymentConfirmRequest, PaymentConfirmResponse,
    InvoiceSchema, GuestImageStatusRequest, GuestImageStatusResponse
)
from app.core.exceptions import NotFoundException, PaymentException
from app.infrastructure.external_services.paypal_service import paypal_service
from app.core.config import settings

router = APIRouter()


# Single image price - $1 USD
IMAGE_PRICE = 1.00
CURRENCY = "USD"


@router.post("/guest/purchase-image", response_model=BuyImagesResponse)
async def guest_purchase_image(
    data: BuyImagesRequest,
    db: Session = Depends(get_db)
):
    """
    Guest checkout - Purchase a single image generation for $1 USD
    
    No login required - uses session_id from frontend localStorage
    """
    
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
                "custom_id": f"guest:{data.sessionId}"  # Use session_id for tracking
            }],
            "application_context": {
                "brand_name": "DreamDuel",
                "landing_page": "BILLING",              # Muestra formulario de tarjeta directo
                "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                "user_action": "PAY_NOW",               # Botón dice "Pagar ahora" en vez de "Continuar"
                "return_url": data.returnUrl or f"{settings.FRONTEND_URL}/payment/success",
                "cancel_url": data.cancelUrl or f"{settings.FRONTEND_URL}/payment/cancel"
            }
        }
        
        # Create order via PayPal
        result = paypal_service.create_order(order_data)
        
        # Save pending invoice to database with session_id
        invoice = Invoice(
            session_id=data.sessionId,  # Guest session tracking
            user_id=None,  # No user for guest checkout
            paypal_order_id=result["order_id"],
            item_type="image_generation",
            quantity=1,
            amount=IMAGE_PRICE,
            currency=CURRENCY,
            status="PENDING"
        )
        db.add(invoice)
        db.commit()
        
        print(f"✅ Guest order created: session={data.sessionId}, order_id={result['order_id']}")
        
        return BuyImagesResponse(
            orderId=result["order_id"],
            approvalUrl=result["approval_url"],
            status="PENDING"
        )
        
    except Exception as e:
        print(f"❌ Guest purchase error: {str(e)}")
        raise PaymentException(f"Failed to create payment order: {str(e)}")


@router.post("/guest/confirm-payment", response_model=PaymentConfirmResponse)
async def guest_confirm_payment(
    data: PaymentConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm guest payment after PayPal approval
    
    Uses session_id to identify the transaction
    """
    
    # Find invoice by session_id and order_id
    invoice = db.query(Invoice).filter(
        Invoice.session_id == data.sessionId,
        Invoice.paypal_order_id == data.orderId
    ).first()
    
    if not invoice:
        print(f"❌ Invoice not found: session={data.sessionId}, order={data.orderId}")
        raise NotFoundException("Invoice", data.orderId)
    
    if invoice.status == "COMPLETED":
        print(f"✅ Payment already completed: session={data.sessionId}")
        return PaymentConfirmResponse(
            success=True,
            message="Payment already confirmed",
            imagesAdded=1,
            totalImagesAvailable=1  # Guest gets exactly 1 image
        )
    
    # Capture payment via PayPal
    try:
        capture_result = paypal_service.capture_order(data.orderId)
        
        # Update invoice status
        invoice.paypal_capture_id = capture_result.get("capture_id")
        invoice.status = "COMPLETED"
        
        db.commit()
        
        print(f"✅ Guest payment confirmed: session={data.sessionId}, capture={capture_result.get('capture_id')}")
        
        return PaymentConfirmResponse(
            success=True,
            message="Payment successful! You can now generate your image.",
            imagesAdded=1,
            totalImagesAvailable=1  # Guest gets 1 paid image
        )
        
    except Exception as e:
        print(f"❌ Payment capture failed: {str(e)}")
        invoice.status = "FAILED"
        db.commit()
        raise PaymentException(f"Failed to capture payment: {str(e)}")


@router.post("/guest/image-status", response_model=GuestImageStatusResponse)
async def get_guest_image_status(
    data: GuestImageStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Check if guest has paid and if their image is ready
    
    Frontend polls this after payment redirect
    """
    
    # Check for completed payment
    invoice = db.query(Invoice).filter(
        Invoice.session_id == data.sessionId,
        Invoice.status == "COMPLETED"
    ).first()
    
    if not invoice:
        # Check if pending payment exists
        pending_invoice = db.query(Invoice).filter(
            Invoice.session_id == data.sessionId,
            Invoice.status == "PENDING"
        ).first()
        
        if pending_invoice:
            return GuestImageStatusResponse(
                hasPaid=False,
                imageReady=False,
                imageUrl=None,
                orderId=pending_invoice.paypal_order_id,
                status="pending_payment"
            )
        
        return GuestImageStatusResponse(
            hasPaid=False,
            imageReady=False,
            imageUrl=None,
            orderId=None,
            status="not_found"
        )
    
    # Check if image is generated
    generated_image = db.query(GeneratedImage).filter(
        GeneratedImage.session_id == data.sessionId
    ).order_by(GeneratedImage.created_at.desc()).first()
    
    if generated_image:
        return GuestImageStatusResponse(
            hasPaid=True,
            imageReady=True,
            imageUrl=generated_image.image_url,
            orderId=invoice.paypal_order_id,
            status="image_ready"
        )
    
    return GuestImageStatusResponse(
        hasPaid=True,
        imageReady=False,
        imageUrl=None,
        orderId=invoice.paypal_order_id,
        status="payment_completed"
    )


@router.post("/webhook")
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    """
    PayPal webhook handler for payment notifications
    
    Handles asynchronous payment confirmations from PayPal (guest and registered users)
    """
    
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # Verify webhook signature (important for security)
        # paypal_service.verify_webhook_signature(headers, body)
        
        event = json.loads(body)
        event_type = event.get("event_type")
        
        print(f"🔔 Webhook received: {event_type}")
        
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
                
                # Only update user credits if not guest
                if invoice.user_id:
                    user = db.query(User).filter(User.id == invoice.user_id).first()
                    if user:
                        user.total_images_generated += invoice.quantity
                
                db.commit()
                print(f"✅ Order captured via webhook: {order_id}")
        
        elif event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Payment was captured successfully
            capture_id = event["resource"]["id"]
            
            invoice = db.query(Invoice).filter(
                Invoice.paypal_capture_id == capture_id
            ).first()
            
            if invoice:
                invoice.status = "COMPLETED"
                db.commit()
                print(f"✅ Payment completed: {capture_id}")
        
        elif event_type == "PAYMENT.CAPTURE.REFUNDED":
            # Payment was refunded
            capture_id = event["resource"]["id"]
            
            invoice = db.query(Invoice).filter(
                Invoice.paypal_capture_id == capture_id
            ).first()
            
            if invoice:
                invoice.status = "REFUNDED"
                db.commit()
                print(f"⚠️ Payment refunded: {capture_id}")
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

