"""Gumroad integration service"""
import httpx
from fastapi import HTTPException
from app.core.config import settings

class GumroadService:
    def __init__(self):
        self.verify_url = "https://api.gumroad.com/v2/licenses/verify"

    async def verify_license(self, license_key: str) -> dict:
        """
        Verify a Gumroad license key and increment its use count.
        """
        if not settings.GUMROAD_PRODUCT_PERMALINK:
            print("⚠️ Gumroad product permalink not configured in settings.")
            raise HTTPException(status_code=500, detail="Payment gateway not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.verify_url,
                    data={
                        "product_permalink": settings.GUMROAD_PRODUCT_PERMALINK,
                        "license_key": license_key,
                        "increment_uses_count": "true"
                    },
                    timeout=10.0
                )
                
                # Check for HTTP errors and Gumroad's "success" boolean
                data = response.json()
                
                # Debug logging
                print(f"Gumroad API Response: {data}")

                if not response.is_success or not data.get("success"):
                    # Gumroad usually returns success=False for invalid or exhausted keys
                    raise HTTPException(status_code=403, detail="Invalid Gumroad license key or out of uses.")
                
                # Extract the purchase object 
                purchase = data.get("purchase", {})
                
                # Check for refunded, disputed, or charged_back
                if purchase.get("refunded") or purchase.get("disputed") or purchase.get("charged_back"):
                    raise HTTPException(status_code=403, detail="This license key has been refunded or disputed.")

                return data
                
            except httpx.RequestError as e:
                print(f"❌ Error connecting to Gumroad: {e}")
                raise HTTPException(status_code=502, detail="Failed to verify license with Gumroad")

gumroad_service = GumroadService()
