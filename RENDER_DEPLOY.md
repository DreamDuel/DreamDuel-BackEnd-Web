# Deploy a Render - Guía Paso a Paso

## Configuración Previa

### 1. Base de Datos PostgreSQL (Neon.tech - GRATIS)

1. Ve a https://neon.tech/
2. Regístrate con GitHub/Google
3. Crea un nuevo proyecto: "DreamDuel"
4. Copia la **Connection String** (DATABASE_URL)
   - Formato: `postgresql://user:password@hostname/database?sslmode=require`

### 2. Redis (Upstash - GRATIS)

1. Ve a https://upstash.com/
2. Regístrate con GitHub/Google
3. Crea una base Redis
4. Copia la **REDIS_URL**
   - Formato: `rediss://default:password@hostname:port`

---

## Deploy en Render

### Paso 1: Conectar Repositorio

1. Ve a https://dashboard.render.com/
2. Haz clic en **"New +"** → **"Web Service"**
3. Conecta tu cuenta de GitHub
4. Selecciona el repositorio: `DreamDuel/DreamDuel-BackEnd-Web`
5. Haz clic en **"Connect"**

### Paso 2: Configuración del Servicio

**Configuración básica:**
- Name: `dreamduel-backend`
- Region: `Oregon (US West)`
- Branch: `main`
- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Selecciona **"Free"**

### Paso 3: Variables de Entorno

Haz clic en **"Advanced"** → **"Add Environment Variable"**

Agrega estas variables (copia desde tu .env local):

```
ENVIRONMENT=production
DEBUG=False
APP_NAME=DreamDuel
SECRET_KEY=<tu_secret_key>
JWT_SECRET=<tu_jwt_secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Base de Datos (Neon.tech)
DATABASE_URL=<tu_neon_database_url>

# Redis (Upstash)
REDIS_URL=<tu_upstash_redis_url>

# PayPal
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=<tu_paypal_client_id>
PAYPAL_CLIENT_SECRET=<tu_paypal_client_secret>
PAYPAL_WEBHOOK_ID=TU_WEBHOOK_ID_LIVE

# Cloudinary
CLOUDINARY_CLOUD_NAME=drmshetga
CLOUDINARY_API_KEY=424968928673351
CLOUDINARY_API_SECRET=hs_xTDxeiUaLeymad8EtSv7h4Ag

# Resend Email
RESEND_API_KEY=re_Fp5JSHBK_EbMQ5aV5ETtswHRPZatyxcm3
FROM_EMAIL=noreply@dreamduel.lat

# Google OAuth
GOOGLE_CLIENT_ID=<tu_google_client_id>
GOOGLE_CLIENT_SECRET=<tu_google_client_secret>

# CORS
CORS_ORIGINS=https://dreamduel.com,https://www.dreamduel.com

# Frontend
FRONTEND_URL=https://dreamduel.com

# API
API_V1_PREFIX=/api

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Sentry (opcional)
SENTRY_DSN=https://693537a66270d775b11919143b33f1d3@o4510959334850560.ingest.us.sentry.io/4510959340486656
```

### Paso 4: Ejecutar Migraciones

**Después del primer deploy:**

1. Ve a la pestaña **"Shell"** en el dashboard de Render
2. Ejecuta:
   ```bash
   alembic upgrade head
   ```

**O desde tu terminal local:**
1. Configura DATABASE_URL en tu .env con la de Neon
2. Ejecuta localmente:
   ```bash
   alembic upgrade head
   ```

### Paso 5: Verificar Deploy

1. Espera a que termine el build (~5-10 minutos)
2. Verás una URL: `https://dreamduel-backend.onrender.com`
3. Prueba: `https://dreamduel-backend.onrender.com/health`
4. Deberías ver: `{"status":"ok","db":"ok","redis":"ok",...}`

---

## Post-Deploy

### 1. Configurar Webhook de PayPal

1. Ve a https://developer.paypal.com/dashboard/
2. Selecciona tu app en modo Live
3. Ve a "Webhooks"
4. Agrega webhook URL: `https://dreamduel-backend.onrender.com/api/payments/webhook`
5. Selecciona eventos:
   - PAYMENT.CAPTURE.COMPLETED
   - PAYMENT.CAPTURE.DENIED
   - PAYMENT.CAPTURE.REFUNDED
6. Copia el **Webhook ID**
7. Actualiza la variable `PAYPAL_WEBHOOK_ID` en Render

### 2. Actualizar Frontend

Cambia la URL del backend en tu frontend:
```typescript
const API_URL = 'https://dreamduel-backend.onrender.com'
```

### 3. Configurar Google OAuth

1. Ve a https://console.cloud.google.com/apis/credentials
2. Edita tu OAuth Client ID
3. Agrega a **Authorized redirect URIs**:
   ```
   https://dreamduel-backend.onrender.com/api/oauth/google/callback
   ```

---

## Importante: Limitación de Render Free

⚠️ **El servicio se duerme después de 15 minutos sin actividad**

**Consecuencias:**
- Primera request después de dormir: tarda 30-60 segundos
- Requests subsecuentes: normales

**Solución temporal:**
- Hacer ping cada 10-14 minutos (puedes usar cron-job.org gratis)

**Solución permanente:**
- Upgrade a plan Starter ($7/mes) - no se duerme

---

## URLs Finales

- **Backend:** `https://dreamduel-backend.onrender.com`
- **API Docs:** `https://dreamduel-backend.onrender.com/docs`
- **Health Check:** `https://dreamduel-backend.onrender.com/health`

---

## Troubleshooting

### Build falla:
- Verifica que requirements.txt está completo
- Checa logs en Render Dashboard

### "Database connection failed":
- Verifica DATABASE_URL en variables de entorno
- Asegúrate que Neon.tech está activo

### "Redis connection failed":
- Verifica REDIS_URL en variables de entorno
- Upstash debe estar configurado

### Servicio muy lento:
- Es normal en plan Free
- Primera request tarda (se despierta)
- Considera upgrade a Starter si necesitas velocidad
