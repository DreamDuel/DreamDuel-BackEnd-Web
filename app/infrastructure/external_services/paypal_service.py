"""PayPal payment service — one-time orders (pay per image)"""

import requests
import base64
from typing import Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import PaymentException


class PayPalService:
    """PayPal REST API — create and capture one-time orders"""

    def __init__(self):
        self.base_url = (
            "https://api-m.sandbox.paypal.com"
            if settings.PAYPAL_MODE == "sandbox"
            else "https://api-m.paypal.com"
        )
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self._access_token = None
        self._token_expires_at = None

    def get_access_token(self) -> str:
        """Get (cached) OAuth2 access token"""
        if self._access_token and self._token_expires_at:
            if datetime.now().timestamp() < self._token_expires_at:
                return self._access_token

        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        response = requests.post(
            f"{self.base_url}/v1/oauth2/token",
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"}
        )

        if response.status_code != 200:
            raise PaymentException(f"Failed to get PayPal access token: {response.text}")

        token_data = response.json()
        self._access_token = token_data["access_token"]
        self._token_expires_at = datetime.now().timestamp() + token_data.get("expires_in", 3600) - 60
        return self._access_token

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a PayPal order for a one-time payment"""
        try:
            token = self.get_access_token()
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=order_data
            )

            if response.status_code not in [200, 201]:
                raise PaymentException(f"PayPal create order error: {response.text}")

            result = response.json()

            approval_url = next(
                (link["href"] for link in result.get("links", []) if link.get("rel") == "approve"),
                None
            )

            return {
                "order_id": result.get("id"),
                "approval_url": approval_url,
                "status": result.get("status")
            }

        except requests.exceptions.RequestException as e:
            raise PaymentException(f"PayPal request failed: {str(e)}")
        except PaymentException:
            raise
        except Exception as e:
            raise PaymentException(f"PayPal order creation failed: {str(e)}")

    def capture_order(self, order_id: str) -> Dict[str, Any]:
        """Capture (complete) a PayPal order after user approval"""
        try:
            token = self.get_access_token()
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            )

            if response.status_code not in [200, 201]:
                raise PaymentException(f"PayPal capture error: {response.text}")

            result = response.json()

            capture_id = None
            if result.get("purchase_units"):
                captures = result["purchase_units"][0].get("payments", {}).get("captures", [])
                if captures:
                    capture_id = captures[0].get("id")

            return {
                "capture_id": capture_id,
                "status": result.get("status"),
                "order_id": result.get("id")
            }

        except requests.exceptions.RequestException as e:
            raise PaymentException(f"PayPal request failed: {str(e)}")
        except PaymentException:
            raise
        except Exception as e:
            raise PaymentException(f"PayPal capture failed: {str(e)}")


# Singleton
paypal_service = PayPalService()
