"""
Script de Prueba Rápida - PayPal Integration
Este script te ayuda a probar rápidamente los endpoints de PayPal
"""

import requests
import json
from typing import Optional

# Configuración
BASE_URL = "http://127.0.0.1:8000/api/v1"
AUTH_TOKEN: Optional[str] = None

def print_response(response, title):
    """Imprime la respuesta de forma legible"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")

def register_user(username: str, email: str, password: str):
    """Registro de usuario"""
    global AUTH_TOKEN
    
    url = f"{BASE_URL}/auth/register"
    payload = {
        "username": username,
        "email": email,
        "password": password
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "REGISTRO DE USUARIO")
    
    if response.status_code in [200, 201]:
        data = response.json()
        AUTH_TOKEN = data.get("token")
        print(f"✅ Token guardado: {AUTH_TOKEN[:50]}...")
        return True
    return False

def login_user(email_or_username: str, password: str):
    """Login de usuario"""
    global AUTH_TOKEN
    
    url = f"{BASE_URL}/auth/login"
    payload = {
        "emailOrUsername": email_or_username,
        "password": password
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "LOGIN DE USUARIO")
    
    if response.status_code == 200:
        data = response.json()
        AUTH_TOKEN = data.get("token")
        print(f"✅ Token guardado: {AUTH_TOKEN[:50]}...")
        return True
    return False

def get_plans():
    """Obtiene los planes disponibles"""
    url = f"{BASE_URL}/payments/plans"
    
    response = requests.get(url)
    print_response(response, "PLANES DISPONIBLES")
    
    if response.status_code == 200:
        return response.json()
    return None

def create_subscription(plan_id: str = "premium_monthly"):
    """Crea una suscripción"""
    url = f"{BASE_URL}/payments/subscribe"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    payload = {
        "planId": plan_id,
        "returnUrl": "http://localhost:3000/payment/success",
        "cancelUrl": "http://localhost:3000/payment/cancel"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print_response(response, "CREAR SUSCRIPCIÓN")
    
    if response.status_code in [200, 201]:
        data = response.json()
        approval_url = data.get("approvalUrl")
        subscription_id = data.get("subscriptionId")
        
        print(f"\n{'🔗 ' * 30}")
        print(f"IMPORTANTE: Abre este link en tu navegador para aprobar el pago:")
        print(f"\n{approval_url}\n")
        print(f"{'🔗 ' * 30}\n")
        print(f"Subscription ID: {subscription_id}")
        print(f"Guarda este ID para confirmar después de aprobar.\n")
        
        return subscription_id
    return None

def confirm_subscription(subscription_id: str):
    """Confirma la suscripción después de la aprobación"""
    url = f"{BASE_URL}/payments/subscription/confirm"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    payload = {
        "subscriptionId": subscription_id
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print_response(response, "CONFIRMAR SUSCRIPCIÓN")
    
    return response.status_code in [200, 201]

def get_subscription_status():
    """Obtiene el estado de la suscripción"""
    url = f"{BASE_URL}/payments/subscription/status"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    print_response(response, "ESTADO DE SUSCRIPCIÓN")
    
    if response.status_code == 200:
        return response.json()
    return None

def cancel_subscription(reason: str = "Testing cancellation"):
    """Cancela la suscripción"""
    url = f"{BASE_URL}/payments/subscription/cancel"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    payload = {
        "reason": reason
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print_response(response, "CANCELAR SUSCRIPCIÓN")
    
    return response.status_code == 200

def reactivate_subscription():
    """Reactiva la suscripción"""
    url = f"{BASE_URL}/payments/subscription/reactivate"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    response = requests.post(url, headers=headers)
    print_response(response, "REACTIVAR SUSCRIPCIÓN")
    
    return response.status_code == 200

def get_transactions():
    """Obtiene historial de transacciones"""
    url = f"{BASE_URL}/payments/transactions"
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    print_response(response, "HISTORIAL DE TRANSACCIONES")
    
    if response.status_code == 200:
        return response.json()
    return None

def main_menu():
    """Menú principal interactivo"""
    global AUTH_TOKEN
    
    print("\n" + "="*60)
    print("🧪 SCRIPT DE PRUEBA - INTEGRACIÓN PAYPAL")
    print("="*60)
    
    while True:
        print("\n📋 MENÚ PRINCIPAL:")
        print("1. 📝 Registrar nuevo usuario")
        print("2. 🔐 Login con usuario existente")
        print("3. 📄 Ver planes disponibles")
        print("4. 💳 Crear suscripción")
        print("5. ✅ Confirmar suscripción (después de aprobar en PayPal)")
        print("6. 📊 Ver estado de suscripción")
        print("7. ❌ Cancelar suscripción")
        print("8. 🔄 Reactivar suscripción")
        print("9. 📜 Ver historial de transacciones")
        print("10. 🚀 Flujo completo de prueba (recomendado)")
        print("0. ❌ Salir")
        
        opcion = input("\n➡️  Selecciona una opción: ")
        
        if opcion == "1":
            username = input("Username: ")
            email = input("Email: ")
            password = input("Password: ")
            register_user(username, email, password)
            
        elif opcion == "2":
            email_or_username = input("Email o Username: ")
            password = input("Password: ")
            login_user(email_or_username, password)
            
        elif opcion == "3":
            get_plans()
            
        elif opcion == "4":
            if not AUTH_TOKEN:
                print("❌ Debes hacer login primero (opción 1 o 2)")
                continue
            plan_id = input("Plan ID (Enter para 'premium_monthly'): ") or "premium_monthly"
            create_subscription(plan_id)
            
        elif opcion == "5":
            if not AUTH_TOKEN:
                print("❌ Debes hacer login primero (opción 1 o 2)")
                continue
            subscription_id = input("Subscription ID (el que recibiste en crear suscripción): ")
            confirm_subscription(subscription_id)
            
        elif opcion == "6":
            if not AUTH_TOKEN:
                print("❌ Debes hacer login primero (opción 1 o 2)")
                continue
            get_subscription_status()
            
        elif opcion == "7":
            if not AUTH_TOKEN:
                print("❌ Debes hacer login primero (opción 1 o 2)")
                continue
            reason = input("Razón de cancelación (Enter para default): ") or "Testing cancellation"
            cancel_subscription(reason)
            
        elif opcion == "8":
            if not AUTH_TOKEN:
                print("❌ Debes hacer login primero (opción 1 o 2)")
                continue
            reactivate_subscription()
            
        elif opcion == "9":
            if not AUTH_TOKEN:
                print("❌ Debes hacer login primero (opción 1 o 2)")
                continue
            get_transactions()
            
        elif opcion == "10":
            print("\n🚀 FLUJO COMPLETO DE PRUEBA")
            print("="*60)
            username = input("Username para nuevo usuario: ")
            email = input("Email: ")
            password = input("Password: ")
            
            # 1. Registrar
            print("\n📝 Paso 1: Registrando usuario...")
            if not register_user(username, email, password):
                print("❌ Error en registro. Abortando.")
                continue
            
            # 2. Ver planes
            print("\n📄 Paso 2: Obteniendo planes...")
            get_plans()
            
            # 3. Crear suscripción
            print("\n💳 Paso 3: Creando suscripción...")
            subscription_id = create_subscription()
            
            if subscription_id:
                input("\n⏸️  PAUSA: Ve al link anterior y aprueba el pago en PayPal Sandbox. Presiona Enter cuando hayas terminado...")
                
                # 4. Confirmar
                print("\n✅ Paso 4: Confirmando suscripción...")
                if confirm_subscription(subscription_id):
                    # 5. Ver estado
                    print("\n📊 Paso 5: Verificando estado...")
                    get_subscription_status()
                    
                    print("\n🎉 ¡Flujo completo exitoso!")
                else:
                    print("❌ Error en confirmación")
            
        elif opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
