"""Stripe payment service"""

import stripe
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import StripeException


# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for Stripe payment processing"""
    
    @staticmethod
    def create_customer(email: str, name: str, metadata: Optional[Dict[str, str]] = None) -> stripe.Customer:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return customer
        except stripe.error.StripeError as e:
            raise StripeException(str(e))
    
    @staticmethod
    def create_subscription(
        customer_id: str,
        price_id: str,
        payment_method_id: Optional[str] = None
    ) -> stripe.Subscription:
        """Create a subscription for a customer"""
        try:
            params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "payment_behavior": "default_incomplete",
                "payment_settings": {"save_default_payment_method": "on_subscription"},
                "expand": ["latest_invoice.payment_intent"],
            }
            
            if payment_method_id:
                params["default_payment_method"] = payment_method_id
            
            subscription = stripe.Subscription.create(**params)
            return subscription
        except stripe.error.StripeError as e:
            raise StripeException(str(e))
    
    @staticmethod
    def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> stripe.Subscription:
        """Cancel a subscription"""
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            return subscription
        except stripe.error.StripeError as e:
            raise StripeException(str(e))
    
    @staticmethod
    def reactivate_subscription(subscription_id: str) -> stripe.Subscription:
        """Reactivate a canceled subscription"""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return subscription
        except stripe.error.StripeError as e:
            raise StripeException(str(e))
    
    @staticmethod
    def get_subscription(subscription_id: str) -> stripe.Subscription:
        """Get subscription details"""
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            raise StripeException(str(e))
    
    @staticmethod
    def update_payment_method(customer_id: str, payment_method_id: str) -> stripe.PaymentMethod:
        """Update customer's default payment method"""
        try:
            # Attach payment method to customer
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Set as default
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
            
            return payment_method
        except stripe.error.StripeError as e:
            raise StripeException(str(e))
    
    @staticmethod
    def list_invoices(customer_id: str, limit: int = 10) -> List[stripe.Invoice]:
        """List customer invoices"""
        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
            return invoices.data
        except stripe.error.StripeError as e:
            raise StripeException(str(e))
    
    @staticmethod
    def create_portal_session(customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """Create a Stripe Customer Portal session"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session
        except stripe.error.StripeError as e:
            raise StripeException(str(e))
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            raise StripeException("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise StripeException("Invalid signature")
    
    @staticmethod
    def get_plans() -> List[Dict[str, Any]]:
        """Get available subscription plans"""
        # This could be fetched from Stripe or hardcoded
        return [
            {
                "id": "monthly",
                "name": "Premium Monthly",
                "price": 999,  # $9.99 in cents
                "interval": "month",
                "features": [
                    "Unlimited AI image generations",
                    "Priority generation queue",
                    "HD image quality",
                    "Advanced editing tools",
                    "No watermarks",
                    "Early access to new features"
                ],
                "stripe_price_id": settings.STRIPE_MONTHLY_PRICE_ID
            },
            {
                "id": "yearly",
                "name": "Premium Yearly",
                "price": 9999,  # $99.99 in cents (save 17%)
                "interval": "year",
                "features": [
                    "All Monthly features",
                    "2 months free (17% savings)",
                    "Priority support",
                    "Exclusive templates",
                    "Commercial license"
                ],
                "stripe_price_id": settings.STRIPE_YEARLY_PRICE_ID
            }
        ]


# Singleton instance
stripe_service = StripeService()
