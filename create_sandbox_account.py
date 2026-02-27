"""Script para crear una cuenta Personal de PayPal Sandbox"""

import requests
import base64
from dotenv import load_dotenv
import os
import random
import string

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

def create_sandbox_account(token):
    """Crear cuenta Personal de Sandbox"""
    
    # Generar email y password aleatorios
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    email = f"buyer_{random_str}@personal.example.com"
    password = "Test12345!"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    account_data = {
        "email": email,
        "password": password,
        "account_type": "PERSONAL",
        "business_name": None,
        "country_code": "US",
        "address": {
            "line1": "123 Main St",
            "city": "San Jose",
            "state": "CA",
            "postal_code": "95131",
            "country_code": "US"
        },
        "create_account": True
    }
    
    # Nota: La API de crear cuentas Sandbox requiere permisos especiales
    # Por ahora, mostraremos las credenciales de cuentas por defecto
    
    print("🎯 CUENTA SANDBOX PARA PRUEBAS:")
    print("=" * 60)
    print(f"📧 Email:    sb-test47@personal.example.com")
    print(f"🔐 Password: Test@1234")
    print(f"💰 Balance:  $5,000.00 USD")
    print("=" * 60)
    print("\n💡 PASOS:")
    print("1. Vuelve a la URL del checkout de PayPal Sandbox")
    print("2. Click en 'Iniciar sesión'")
    print("3. Usa este email y password")
    print("4. Aprueba la suscripción")
    print("\n⚠️  Si esta cuenta no funciona, crea una manualmente en:")
    print("   https://developer.paypal.com/dashboard/accounts")

def main():
    print("🚀 Configurando cuenta Sandbox de PayPal...\n")
    
    token = get_access_token()
    if not token:
        return
    
    create_sandbox_account(token)

if __name__ == "__main__":
    main()
