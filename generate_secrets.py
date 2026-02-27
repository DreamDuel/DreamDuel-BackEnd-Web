"""
Genera SECRET_KEY y JWT_SECRET seguros para producción
"""
import secrets
import string

def generate_secure_key(length=64):
    """Genera una clave criptográficamente segura"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print("=" * 80)
    print("🔑 CLAVES SEGURAS PARA PRODUCCIÓN")
    print("=" * 80)
    print()
    
    secret_key = generate_secure_key(64)
    jwt_secret = generate_secure_key(64)
    
    print("Copia estas claves a tu .env de PRODUCCIÓN:")
    print()
    print(f"SECRET_KEY={secret_key}")
    print()
    print(f"JWT_SECRET={jwt_secret}")
    print()
    print("=" * 80)
    print("⚠️  NUNCA compartas estas claves ni las subas a GitHub")
    print("=" * 80)
