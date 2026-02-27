# 🎨 DreamDuel Backend API

Backend API para DreamDuel - Plataforma de generación de imágenes con IA.

## 🚀 Tech Stack

- **Framework:** FastAPI 0.109.0
- **Database:** PostgreSQL + SQLAlchemy
- **Cache:** Redis
- **Authentication:** JWT + Argon2 password hashing
- **Payments:** PayPal Subscriptions API
- **Storage:** Cloudinary
- **OAuth:** Google + Apple Sign In
- **Email:** Resend

---

## 📚 Documentación API

**Swagger UI:** `http://localhost:8000/docs`  
**ReDoc:** `http://localhost:8000/redoc`

---

## 🔗 Endpoints Principales

### **Authentication** (`/api/auth`)

```http
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout
POST /api/auth/password-reset
POST /api/auth/password-reset/confirm
POST /api/auth/verify-email
```

### **OAuth** (`/api/oauth`)

```http
POST /api/oauth/google      # Login con Google
POST /api/oauth/apple       # Login con Apple
GET  /api/oauth/google/url  # URL de autorización Google
GET  /api/oauth/apple/config # Config de Apple Sign In
```

### **Users** (`/api/users`)

```http
GET    /api/users/me           # Perfil del usuario actual
PUT    /api/users/me           # Actualizar perfil
DELETE /api/users/me           # Eliminar cuenta
GET    /api/users/{username}   # Perfil público
POST   /api/users/{id}/follow  # Seguir usuario
DELETE /api/users/{id}/unfollow # Dejar de seguir
```

### **Payments (PayPal)** (`/api/payments`)

```http
GET  /api/payments/plans                    # Planes disponibles
POST /api/payments/subscribe                # Crear suscripción
POST /api/payments/subscription/confirm     # Confirmar suscripción
GET  /api/payments/subscription/status      # Estado de suscripción
POST /api/payments/subscription/cancel      # Cancelar suscripción
POST /api/payments/subscription/reactivate  # Reactivar suscripción
GET  /api/payments/invoices                 # Historial de facturas
POST /api/payments/webhook                  # Webhook de PayPal
```

### **Image Generation** (`/api/generate`)

```http
POST /api/generate/image      # Generar imagen con IA
GET  /api/generate/history    # Historial de generaciones
GET  /api/generate/{id}       # Detalles de una generación
DELETE /api/generate/{id}     # Eliminar generación
```

### **Upload** (`/api/upload`)

```http
POST /api/upload/avatar       # Subir avatar
POST /api/upload/image        # Subir imagen
```

### **Analytics** (`/api/analytics`)

```http
POST /api/analytics/event     # Registrar evento
GET  /api/analytics/stats     # Estadísticas del usuario
```

---

## 🔐 Autenticación

Todos los endpoints (excepto register/login/oauth) requieren JWT token:

```javascript
// Header
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## 💳 Flujo de Suscripción PayPal

### 1. Frontend: Iniciar suscripción

```javascript
const response = await fetch('/api/payments/subscribe', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    planId: 'monthly', // o 'yearly'
    returnUrl: 'https://tu-app.com/payment/success',
    cancelUrl: 'https://tu-app.com/payment/cancel'
  })
});

const { approvalUrl, subscriptionId } = await response.json();

// Redirigir al usuario a approvalUrl
window.location.href = approvalUrl;
```

### 2. Usuario aprueba en PayPal

PayPal redirige a: `returnUrl?subscription_id=I-XXXXXXXXX`

### 3. Frontend: Confirmar suscripción

```javascript
// Extraer subscription_id de la URL
const params = new URLSearchParams(window.location.search);
const subscriptionId = params.get('subscription_id');

// Confirmar con backend
await fetch('/api/payments/subscription/confirm', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ subscriptionId })
});

// Usuario ahora es premium
```

---

## 🔑 OAuth Flow

### Google Login

```javascript
// 1. Obtener Google ID token (usando Google Sign In SDK)
const googleUser = await google.accounts.id.initialize({
  client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID
});

// 2. Enviar a backend
const response = await fetch('/api/oauth/google', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ token: googleUser.credential })
});

const { access_token, refresh_token } = await response.json();
```

### Apple Login

```javascript
// 1. Apple Sign In
const appleResponse = await AppleID.auth.signIn();

// 2. Enviar a backend
const response = await fetch('/api/oauth/apple', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    code: appleResponse.authorization.code,
    id_token: appleResponse.authorization.id_token
  })
});

const { access_token, refresh_token } = await response.json();
```

---

## 🛠️ Setup Local

### 1. Clonar repositorio

```bash
git clone https://github.com/DreamDuel/DreamDuel-BackEnd-Web.git
cd DreamDuel-BackEnd-Web
```

### 2. Instalar dependencias

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crear `.env`:

```env
# App
DEBUG=True
ENVIRONMENT=development
SECRET_KEY=tu-secret-key-aqui
JWT_SECRET=tu-jwt-secret-aqui
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dreamduel_dev

# Redis
REDIS_URL=redis://localhost:6379

# PayPal Sandbox
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=tu_paypal_client_id
PAYPAL_CLIENT_SECRET=tu_paypal_secret
PAYPAL_MONTHLY_PLAN_ID=P-XXXXXXXXX

# Cloudinary
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret

# Resend
RESEND_API_KEY=tu_resend_key
FROM_EMAIL=noreply@localhost

# Google OAuth
GOOGLE_CLIENT_ID=tu_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_google_secret

# AI Services
REPLICATE_API_KEY=tu_replicate_key
```

### 4. Ejecutar migraciones

```bash
alembic upgrade head
```

### 5. Iniciar servidor

```bash
uvicorn app.main:app --reload --port 8000
```

**API disponible en:** http://localhost:8000  
**Docs:** http://localhost:8000/docs

---

## 📦 Scripts Útiles

```bash
# Crear plan de PayPal
python create_paypal_plan.py

# Testing de PayPal
python test_paypal.py

# Ejecutar migraciones
alembic upgrade head

# Crear nueva migración
alembic revision --autogenerate -m "descripcion"

# Rollback migración
alembic downgrade -1
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app tests/

# Test específico
pytest tests/test_auth.py
```

---

## 🌐 Deploy

Ver [DEPLOYMENT.md](DEPLOYMENT.md) para guía completa de deployment.

**Quick start con Railway:**

1. Push a GitHub
2. Conectar Railway con GitHub
3. Configurar variables de entorno
4. Railway hace auto-deploy

---

## 📝 Variables de Entorno

Ver `.env.example` para lista completa de variables requeridas.

**Mínimas para desarrollo:**
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `JWT_SECRET`
- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`
- `CLOUDINARY_*`

---

## 🔧 Configuración de Webhooks

Ver [WEBHOOKS_SETUP.md](WEBHOOKS_SETUP.md) para:
- PayPal Webhooks
- Google OAuth setup
- Apple Sign In setup

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crear branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

---

## 📄 Licencia

Privado - DreamDuel © 2026

---

## 📞 Soporte

Para preguntas o issues, crear un issue en GitHub o contactar al equipo de desarrollo.
