"""Payment routes - Pay per image model"""

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
    ImagePackage, InvoiceSchema
)
from app.core.exceptions import NotFoundException, PaymentException
from app.infrastructure.external_services.paypal_service import paypal_service
from app.core.config import settings

router = APIRouter()


# Image packages available for purchase
IMAGE_PACKAGES = [
    {"id": "1_image", "images": 1, "price": 2.99, "currency": "USD", "name": "1 Image"},
    {"id": "5_images", "images": 5, "price": 12.99, "currency": "USD", "name": "5 Images Pack", "discount": "13% OFF"},
    {"id": "10_images", "images": 10, "price": 22.99, "currency": "USD", "name": "10 Images Pack", "discount": "23% OFF"},
    {"id": "25_images", "images": 25, "price": 49.99, "currency": "USD", "name": "25 Images Pack", "discount": "33% OFF"},
]


@router.get("/packages", response_model=List[ImagePackage])
async def get_packages():
    """Get available image packages"""
    return [ImagePackage(**pkg) for pkg in IMAGE_PACKAGES]


@router.post("/buy-images", response_model=BuyImagesResponse)
async def buy_images(
    data: BuyImagesRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Purchase image generations
    
    Creates a PayPal order and returns approval URL
    """
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # Get package details
    package = next((p for p in IMAGE_PACKAGES if p["id"] == data.packageId), None)
    
    if not package:
        raise NotFoundException("Package", data.packageId)
    
    # Create PayPal order
    try:
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "description": f"DreamDuel - {package['name']}",
                "amount": {
                    "currency_code": package["currency"],
                    "value": str(package["price"])
                },
                "custom_id": f"{current_user_id}:{package['id']}"  # To identify user and package
            }],
            "application_context": {
                "brand_name": "DreamDuel",
                "return_url": data.returnUrl or f"{settings.FRONTEND_URL}/payment/success",
                "cancel_url": data.cancelUrl or f"{settings.FRONTEND_URL}/payment/cancel"
            }
        }
        
        # Create order via PayPal
        result = paypal_service.create_order(order_data)
        
        # Save pending invoice to database
        invoice = Invoice(
            user_id=current_user_id,
            paypal_order_id=result["order_id"],
            item_type="image_generation",
            quantity=package["images"],
            amount=package["price"],
            currency=package["currency"],
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
    
    This captures the payment and adds image credits to user account
    """
    
    # Find invoice
    invoice = db.query(Invoice).filter(
        Invoice.user_id == current_user_id,
        Invoice.paypal_order_id == data.orderId
    ).first()
    
    if not invoice:
        raise NotFoundException("Invoice", data.orderId)
    
    if invoice.status == "COMPLETED":
        raise PaymentException("Payment already processed")
    
    # Capture payment via PayPal
    try:
        capture_result = paypal_service.capture_order(data.orderId)
        
        # Update invoice
        invoice.paypal_capture_id = capture_result.get("capture_id")
        invoice.status = "COMPLETED"
        
        # Add image credits to user
        user = db.query(User).filter(User.id == current_user_id).first()
        if user:
            user.paid_images_count += invoice.quantity
        
        db.commit()
        
        return PaymentConfirmResponse(
            success=True,
            message=f"Payment successful! {invoice.quantity} image generation(s) added to your account",
            imagesAdded=invoice.quantity,
            totalImagesAvailable=user.paid_images_count - (user.total_images_generated - 1) if user.total_images_generated > 0 else user.paid_images_count + 1  # +1 for first free image
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


@router.get("/balance")
async def get_balance(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's image generation balance"""
    
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise NotFoundException("User", current_user_id)
    
    # Calculate available images
    if user.total_images_generated == 0:
        # User hasn't generated first free image yet
        available_images = 1 + user.paid_images_count
        first_image_free = True
    else:
        # First image used, calculate remaining paid images
        available_images = user.paid_images_count - (user.total_images_generated - 1)
        first_image_free = False
    
    return {
        "totalGenerated": user.total_images_generated,
        "paidImagesCount": user.paid_images_count,
        "availableImages": max(0, available_images),
        "firstImageFree": first_image_free
    }


# ==================== FRONTEND COMPATIBILITY ENDPOINTS ====================


@router.post("/purchase-image", response_model=BuyImagesResponse)
async def purchase_single_image(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Purchase a single image generation (Frontend compatibility endpoint)
    
    Automatically uses the 1-image package
    """
    request_data = BuyImagesRequest(
        packageId="1_image",
        returnUrl=f"{settings.FRONTEND_URL}/payment/success",
        cancelUrl=f"{settings.FRONTEND_URL}/payment/cancel"
    )
    
    return await buy_images(request_data, current_user_id, db)


@router.post("/purchase-package", response_model=BuyImagesResponse)
async def purchase_package(
    data: BuyImagesRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Purchase an image package (Frontend compatibility endpoint)
    
    Alias for /buy-images
    """
    return await buy_images(data, current_user_id, db)


@router.get("/transactions", response_model=List[InvoiceSchema])
async def get_transactions(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """
    Get user's transaction history (Frontend compatibility endpoint)
    
    Alias for /invoices
    """
    return await get_invoices(current_user_id, db, limit)
