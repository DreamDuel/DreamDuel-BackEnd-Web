"""Script para crear un plan de suscripción en PayPal Sandbox"""

import requests
import base64
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
BASE_URL = "https://api-m.sandbox.paypal.com"

def get_access_token():
    """Obtener token de acceso"""
    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(f"{BASE_URL}/v1/oauth2/token", headers=headers, data=data)
    
    if response.status_code != 200:
        print(f"❌ Error obteniendo token: {response.text}")
        return None
    
    return response.json()["access_token"]

def create_product(token):
    """Crear un producto en PayPal"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    product_data = {
        "name": "DreamDuel Premium",
        "description": "Acceso premium a DreamDuel con generación ilimitada de imágenes e historias con IA",
        "type": "DIGITAL",
        "category": "SOFTWARE"
    }
    
    response = requests.post(f"{BASE_URL}/v1/catalogs/products", headers=headers, json=product_data)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Error creando producto: {response.text}")
        return None
    
    product = response.json()
    print(f"✅ Producto creado: {product['id']}")
    return product["id"]

def create_plan(token, product_id):
    """Crear plan de suscripción mensual"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    plan_data = {
        "product_id": product_id,
        "name": "Premium Monthly",
        "description": "Suscripción mensual a DreamDuel Premium",
        "status": "ACTIVE",
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 0,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": "15.00",
                        "currency_code": "USD"
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee": {
                "value": "0",
                "currency_code": "USD"
            },
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        }
    }
    
    response = requests.post(f"{BASE_URL}/v1/billing/plans", headers=headers, json=plan_data)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Error creando plan: {response.text}")
        return None
    
    plan = response.json()
    print(f"✅ Plan creado exitosamente!")
    print(f"\n📋 COPIA ESTE PLAN ID:")
    print(f"   {plan['id']}")
    print(f"\n💡 Agrégalo a tu .env como:")
    print(f"   PAYPAL_MONTHLY_PLAN_ID={plan['id']}")
    
    return plan["id"]

def main():
    print("🚀 Creando plan de suscripción en PayPal Sandbox...\n")
    
    # 1. Obtener token
    print("1️⃣  Obteniendo token de acceso...")
    token = get_access_token()
    if not token:
        return
    print("✅ Token obtenido\n")
    
    # 2. Crear producto
    print("2️⃣  Creando producto...")
    product_id = create_product(token)
    if not product_id:
        return
    print()
    
    # 3. Crear plan
    print("3️⃣  Creando plan de suscripción mensual...")
    plan_id = create_plan(token, product_id)
    if not plan_id:
        return
    
    print("\n✅ ¡Todo listo! Ahora actualiza tu .env y reinicia el servidor.")

if __name__ == "__main__":
    main()
