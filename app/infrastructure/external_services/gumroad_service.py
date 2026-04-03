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
        product_id = (settings.GUMROAD_PRODUCT_ID or "").strip()
        if not product_id:
            print("⚠️ Gumroad product_id not configured in settings.")
            raise HTTPException(status_code=500, detail="Payment gateway not configured")

        form = {
            "product_id": product_id,
            "license_key": license_key,
            "increment_uses_count": "true",
        }
        print(
            f"Gumroad verify POST: product_id_len={len(product_id)}, "
            f"license_key_len={len(license_key)}, fields={list(form.keys())}"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.verify_url,
                    data=form,
                    timeout=10.0,
                )

                payload = response.json()

                print(f"Gumroad API Response: {payload}")

                if not response.is_success or not payload.get("success"):
                    # Gumroad usually returns success=False for invalid or exhausted keys
                    raise HTTPException(status_code=403, detail="Invalid Gumroad license key or out of uses.")

                purchase = payload.get("purchase", {})
                
                # Check for refunded, disputed, or charged_back
                if purchase.get("refunded") or purchase.get("disputed") or purchase.get("charged_back"):
                    raise HTTPException(status_code=403, detail="This license key has been refunded or disputed.")

                return payload
                
            except httpx.RequestError as e:
                print(f"❌ Error connecting to Gumroad: {e}")
                raise HTTPException(status_code=502, detail="Failed to verify license with Gumroad")

gumroad_service = GumroadService()
