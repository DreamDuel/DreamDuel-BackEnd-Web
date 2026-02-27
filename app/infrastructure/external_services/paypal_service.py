"""PayPal payment service for subscriptions and payments"""

import requests
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import PaymentException


class PayPalService:
    """Service for PayPal payment processing and subscriptions using REST API"""
    
    def __init__(self):
        self.base_url = "https://api-m.sandbox.paypal.com" if settings.PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self._access_token = None
        self._token_expires_at = None
    
    def get_access_token(self) -> str:
        """Get OAuth2 access token for PayPal API"""
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.now().timestamp() < self._token_expires_at:
                return self._access_token
        
        # Get new token
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(
            f"{self.base_url}/v1/oauth2/token",
            headers=headers,
            data=data
        )
        
        if response.status_code != 200:
            raise PaymentException(f"Failed to get PayPal access token: {response.text}")
        
        token_data = response.json()
        self._access_token = token_data["access_token"]
        self._token_expires_at = datetime.now().timestamp() + token_data.get("expires_in", 3600) - 60
        
        return self._access_token
    
    def create_subscription(
        self,
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
            access_token = self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            subscription_data = {
                "plan_id": plan_id,
                "application_context": {
                    "brand_name": "DreamDuel",
                    "locale": "es-PE",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "SUBSCRIBE_NOW",
                    "return_url": return_url,
                    "cancel_url": cancel_url
                }
            }
            
            # Add subscriber information if provided
            if subscriber_email or subscriber_name:
                subscription_data["subscriber"] = {}
                if subscriber_email:
                    subscription_data["subscriber"]["email_address"] = subscriber_email
                if subscriber_name:
                    name_parts = subscriber_name.split()
                    subscription_data["subscriber"]["name"] = {
                        "given_name": name_parts[0] if name_parts else "",
                        "surname": " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                    }
            
            response = requests.post(
                f"{self.base_url}/v1/billing/subscriptions",
                headers=headers,
                json=subscription_data
            )
            
            if response.status_code not in [200, 201]:
                raise PaymentException(f"PayPal API error: {response.text}")
            
            result = response.json()
            
            # Get approval URL
            approval_url = None
            for link in result.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            return {
                "subscription_id": result.get("id"),
                "approval_url": approval_url,
                "status": result.get("status")
            }
                
        except requests.exceptions.RequestException as e:
            raise PaymentException(f"PayPal API request failed: {str(e)}")
        except Exception as e:
            raise PaymentException(f"PayPal subscription creation failed: {str(e)}")
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details"""
        try:
            access_token = self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/v1/billing/subscriptions/{subscription_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                raise PaymentException(f"PayPal API error: {response.text}")
            
            result = response.json()
            
            return {
                "id": result.get("id"),
                "status": result.get("status"),
                "plan_id": result.get("plan_id"),
                "start_time": result.get("start_time"),
                "billing_info": result.get("billing_info"),
                "subscriber": result.get("subscriber")
            }
        except requests.exceptions.RequestException as e:
            raise PaymentException(f"PayPal API request failed: {str(e)}")
        except Exception as e:
            raise PaymentException(f"Error getting subscription: {str(e)}")
    
    def cancel_subscription(self, subscription_id: str, reason: str = "Customer request") -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            access_token = self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {"reason": reason}
            
            response = requests.post(
                f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/cancel",
                headers=headers,
                json=data
            )
            
            if response.status_code not in [200, 204]:
                raise PaymentException(f"PayPal API error: {response.text}")
            
            return {
                "subscription_id": subscription_id,
                "status": "CANCELLED",
                "message": "Subscription cancelled successfully"
            }
                
        except requests.exceptions.RequestException as e:
            raise PaymentException(f"PayPal API request failed: {str(e)}")
        except Exception as e:
            raise PaymentException(f"PayPal subscription cancellation failed: {str(e)}")
    
    def suspend_subscription(self, subscription_id: str, reason: str = "Suspended by admin") -> Dict[str, Any]:
        """Suspend a subscription"""
        try:
            access_token = self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {"reason": reason}
            
            response = requests.post(
                f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/suspend",
                headers=headers,
                json=data
            )
            
            if response.status_code not in [200, 204]:
                raise PaymentException(f"PayPal API error: {response.text}")
            
            return {
                "subscription_id": subscription_id,
                "status": "SUSPENDED",
                "message": "Subscription suspended successfully"
            }
                
        except requests.exceptions.RequestException as e:
            raise PaymentException(f"PayPal API request failed: {str(e)}")
        except Exception as e:
            raise PaymentException(f"PayPal subscription suspension failed: {str(e)}")
    
    def activate_subscription(self, subscription_id: str, reason: str = "Reactivated by user") -> Dict[str, Any]:
        """Activate a suspended subscription"""
        try:
            access_token = self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {"reason": reason}
            
            response = requests.post(
                f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/activate",
                headers=headers,
                json=data
            )
            
            if response.status_code not in [200, 204]:
                raise PaymentException(f"PayPal API error: {response.text}")
            
            return {
                "subscription_id": subscription_id,
                "status": "ACTIVE",
                "message": "Subscription activated successfully"
            }
                
        except requests.exceptions.RequestException as e:
            raise PaymentException(f"PayPal API request failed: {str(e)}")
        except Exception as e:
            raise PaymentException(f"PayPal subscription activation failed: {str(e)}")
    
    def list_transactions(self, subscription_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        List subscription transactions
        
        Args:
            subscription_id: PayPal subscription ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        try:
            access_token = self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "start_time": f"{start_date}T00:00:00Z",
                "end_time": f"{end_date}T23:59:59Z"
            }
            
            response = requests.get(
                f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/transactions",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                raise PaymentException(f"PayPal API error: {response.text}")
            
            result = response.json()
            transactions = result.get("transactions", [])
            
            return [{
                "id": t.get("id"),
                "status": t.get("status"),
                "amount": t.get("amount_with_breakdown", {}).get("gross_amount", {}).get("value"),
                "currency": t.get("amount_with_breakdown", {}).get("gross_amount", {}).get("currency_code"),
                "time": t.get("time")
            } for t in transactions]
            
        except requests.exceptions.RequestException as e:
            raise PaymentException(f"PayPal API request failed: {str(e)}")
        except Exception as e:
            raise PaymentException(f"Error listing transactions: {str(e)}")
    
    def verify_webhook_signature(
        self,
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
            access_token = self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "transmission_id": transmission_id,
                "transmission_time": timestamp,
                "cert_url": cert_url,
                "auth_algo": auth_algo,
                "transmission_sig": transmission_sig,
                "webhook_id": webhook_id,
                "webhook_event": event_body
            }
            
            response = requests.post(
                f"{self.base_url}/v1/notifications/verify-webhook-signature",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                return False
            
            result = response.json()
            return result.get('verification_status') == 'SUCCESS'
            
        except Exception as e:
            raise PaymentException(f"Webhook verification failed: {str(e)}")
    
    def get_plans(self) -> List[Dict[str, Any]]:
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
    
    def create_plan(
        self,
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
            access_token = self.get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            billing_plan_data = {
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
            
            response = requests.post(
                f"{self.base_url}/v1/billing/plans",
                headers=headers,
                json=billing_plan_data
            )
            
            if response.status_code not in [200, 201]:
                raise PaymentException(f"PayPal API error: {response.text}")
            
            result = response.json()
            
            return {
                "plan_id": result.get("id"),
                "name": result.get("name"),
                "status": result.get("status")
            }
                
        except requests.exceptions.RequestException as e:
            raise PaymentException(f"PayPal API request failed: {str(e)}")
        except Exception as e:
            raise PaymentException(f"PayPal plan creation failed: {str(e)}")


# Singleton instance
paypal_service = PayPalService()
