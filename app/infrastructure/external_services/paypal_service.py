"""PayPal payment service for subscriptions and payments"""

import paypalrestsdk
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import PaymentException


# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # sandbox or live
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})


class PayPalService:
    """Service for PayPal payment processing and subscriptions"""
    
    @staticmethod
    def create_subscription(
        plan_id: str,
        return_url: str,
        cancel_url: str,
        subscriber_email: Optional[str] = None,
        subscriber_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a PayPal subscription
        
        Args:
            plan_id: PayPal plan ID (P-XXXXXXXXX)
            return_url: URL to redirect after successful subscription
            cancel_url: URL to redirect if user cancels
            subscriber_email: Optional subscriber email
            subscriber_name: Optional subscriber name
            
        Returns:
            Dictionary with subscription_id and approval_url
        """
        try:
            subscription_attributes = {
                "plan_id": plan_id,
                "application_context": {
                    "brand_name": "DreamDuel",
                    "locale": "es-PE",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "SUBSCRIBE_NOW",
                    "payment_method": {
                        "payer_selected": "PAYPAL",
                        "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                    },
                    "return_url": return_url,
                    "cancel_url": cancel_url
                }
            }
            
            # Add subscriber information if provided
            if subscriber_email or subscriber_name:
                subscription_attributes["subscriber"] = {}
                if subscriber_email:
                    subscription_attributes["subscriber"]["email_address"] = subscriber_email
                if subscriber_name:
                    subscription_attributes["subscriber"]["name"] = {
                        "given_name": subscriber_name.split()[0] if subscriber_name else "",
                        "surname": " ".join(subscriber_name.split()[1:]) if len(subscriber_name.split()) > 1 else ""
                    }
            
            subscription = paypalrestsdk.BillingSubscription(subscription_attributes)
            
            if subscription.create():
                # Get approval URL
                approval_url = None
                for link in subscription.links:
                    if link.rel == "approve":
                        approval_url = link.href
                        break
                
                return {
                    "subscription_id": subscription.id,
                    "approval_url": approval_url,
                    "status": subscription.status
                }
            else:
                raise PaymentException(f"Error creating subscription: {subscription.error}")
                
        except Exception as e:
            raise PaymentException(f"PayPal subscription creation failed: {str(e)}")
    
    @staticmethod
    def get_subscription(subscription_id: str) -> Dict[str, Any]:
        """Get subscription details"""
        try:
            subscription = paypalrestsdk.BillingSubscription.find(subscription_id)
            
            return {
                "id": subscription.id,
                "status": subscription.status,
                "plan_id": subscription.plan_id,
                "start_time": subscription.start_time if hasattr(subscription, 'start_time') else None,
                "billing_info": subscription.billing_info if hasattr(subscription, 'billing_info') else None,
                "subscriber": subscription.subscriber if hasattr(subscription, 'subscriber') else None
            }
        except Exception as e:
            raise PaymentException(f"Error getting subscription: {str(e)}")
    
    @staticmethod
    def cancel_subscription(subscription_id: str, reason: str = "Customer request") -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            subscription = paypalrestsdk.BillingSubscription.find(subscription_id)
            
            cancel_note = {
                "reason": reason
            }
            
            if subscription.cancel(cancel_note):
                return {
                    "subscription_id": subscription_id,
                    "status": "CANCELLED",
                    "message": "Subscription cancelled successfully"
                }
            else:
                raise PaymentException(f"Error cancelling subscription: {subscription.error}")
                
        except Exception as e:
            raise PaymentException(f"PayPal subscription cancellation failed: {str(e)}")
    
    @staticmethod
    def suspend_subscription(subscription_id: str, reason: str = "Suspended by admin") -> Dict[str, Any]:
        """Suspend a subscription"""
        try:
            subscription = paypalrestsdk.BillingSubscription.find(subscription_id)
            
            suspend_note = {
                "reason": reason
            }
            
            if subscription.suspend(suspend_note):
                return {
                    "subscription_id": subscription_id,
                    "status": "SUSPENDED",
                    "message": "Subscription suspended successfully"
                }
            else:
                raise PaymentException(f"Error suspending subscription: {subscription.error}")
                
        except Exception as e:
            raise PaymentException(f"PayPal subscription suspension failed: {str(e)}")
    
    @staticmethod
    def activate_subscription(subscription_id: str, reason: str = "Reactivated by user") -> Dict[str, Any]:
        """Activate a suspended subscription"""
        try:
            subscription = paypalrestsdk.BillingSubscription.find(subscription_id)
            
            activate_note = {
                "reason": reason
            }
            
            if subscription.activate(activate_note):
                return {
                    "subscription_id": subscription_id,
                    "status": "ACTIVE",
                    "message": "Subscription activated successfully"
                }
            else:
                raise PaymentException(f"Error activating subscription: {subscription.error}")
                
        except Exception as e:
            raise PaymentException(f"PayPal subscription activation failed: {str(e)}")
    
    @staticmethod
    def list_transactions(subscription_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        List subscription transactions
        
        Args:
            subscription_id: PayPal subscription ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        try:
            subscription = paypalrestsdk.BillingSubscription.find(subscription_id)
            
            params = {
                "start_time": f"{start_date}T00:00:00Z",
                "end_time": f"{end_date}T23:59:59Z"
            }
            
            transactions = subscription.transactions(params)
            
            return [{
                "id": t.id if hasattr(t, 'id') else None,
                "status": t.status if hasattr(t, 'status') else None,
                "amount": t.amount_with_breakdown.gross_amount.value if hasattr(t, 'amount_with_breakdown') else None,
                "currency": t.amount_with_breakdown.gross_amount.currency_code if hasattr(t, 'amount_with_breakdown') else None,
                "time": t.time if hasattr(t, 'time') else None
            } for t in transactions.get('transactions', [])]
            
        except Exception as e:
            raise PaymentException(f"Error listing transactions: {str(e)}")
    
    @staticmethod
    def verify_webhook_signature(
        transmission_id: str,
        timestamp: str,
        webhook_id: str,
        event_body: str,
        cert_url: str,
        transmission_sig: str,
        auth_algo: str
    ) -> bool:
        """
        Verify PayPal webhook signature
        
        This ensures the webhook actually came from PayPal
        """
        try:
            # Webhook event verification
            response = paypalrestsdk.WebhookEvent.verify(
                transmission_id=transmission_id,
                timestamp=timestamp,
                webhook_id=webhook_id,
                event_body=event_body,
                cert_url=cert_url,
                transmission_sig=transmission_sig,
                auth_algo=auth_algo
            )
            
            return response.get('verification_status') == 'SUCCESS'
            
        except Exception as e:
            raise PaymentException(f"Webhook verification failed: {str(e)}")
    
    @staticmethod
    def get_plans() -> List[Dict[str, Any]]:
        """Get available subscription plans"""
        # This is hardcoded but could be fetched from PayPal API
        # or stored in database
        return [
            {
                "id": "monthly",
                "name": "Premium Monthly",
                "price": 999,  # $9.99 in cents
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Generación ilimitada de imágenes con IA",
                    "Generación ilimitada de historias con IA",
                    "Sin marcas de agua",
                    "Calidad HD",
                    "Soporte prioritario",
                    "Acceso anticipado a nuevas funciones"
                ],
                "paypal_plan_id": settings.PAYPAL_MONTHLY_PLAN_ID
            },
            {
                "id": "yearly",
                "name": "Premium Yearly",
                "price": 9999,  # $99.99 in cents (save 17%)
                "currency": "usd",
                "interval": "year",
                "features": [
                    "Todas las funciones del plan mensual",
                    "2 meses gratis (ahorro del 17%)",
                    "Soporte VIP",
                    "Plantillas exclusivas",
                    "Licencia comercial",
                    "API access (próximamente)"
                ],
                "paypal_plan_id": settings.PAYPAL_YEARLY_PLAN_ID
            }
        ]
    
    @staticmethod
    def create_plan(
        product_id: str,
        name: str,
        description: str,
        price: float,
        currency: str = "USD",
        interval: str = "MONTH"
    ) -> Dict[str, Any]:
        """
        Create a billing plan programmatically
        
        Args:
            product_id: PayPal product ID
            name: Plan name
            description: Plan description
            price: Price amount (e.g., 9.99)
            currency: Currency code (USD, PEN, etc.)
            interval: MONTH or YEAR
        """
        try:
            billing_plan_attributes = {
                "product_id": product_id,
                "name": name,
                "description": description,
                "status": "ACTIVE",
                "billing_cycles": [
                    {
                        "frequency": {
                            "interval_unit": interval,
                            "interval_count": 1
                        },
                        "tenure_type": "REGULAR",
                        "sequence": 1,
                        "total_cycles": 0,  # 0 = infinite
                        "pricing_scheme": {
                            "fixed_price": {
                                "value": str(price),
                                "currency_code": currency
                            }
                        }
                    }
                ],
                "payment_preferences": {
                    "auto_bill_outstanding": True,
                    "setup_fee": {
                        "value": "0",
                        "currency_code": currency
                    },
                    "setup_fee_failure_action": "CONTINUE",
                    "payment_failure_threshold": 3
                }
            }
            
            billing_plan = paypalrestsdk.BillingPlan(billing_plan_attributes)
            
            if billing_plan.create():
                return {
                    "plan_id": billing_plan.id,
                    "name": billing_plan.name,
                    "status": billing_plan.status
                }
            else:
                raise PaymentException(f"Error creating plan: {billing_plan.error}")
                
        except Exception as e:
            raise PaymentException(f"PayPal plan creation failed: {str(e)}")


# Singleton instance
paypal_service = PayPalService()
