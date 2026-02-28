# 🚀 GUÍA RÁPIDA: DEPLOY EN RAILWAY

## PASO 1: CREAR CUENTA
1. Ve a: https://railway.app
2. Click "Start a New Project"
3. Click "Login with GitHub"
4. Autoriza Railway en GitHub

---

## PASO 2: CREAR PROYECTO
1. En Railway Dashboard, click "New Project"
2. Selecciona "Deploy from GitHub repo"
3. Busca y selecciona: **DreamDuel-BackEnd-Web**
4. Railway detecta automáticamente que es Python/FastAPI ✅

---

## PASO 3: AGREGAR POSTGRESQL
1. En tu proyecto, click botón "+ New"
2. Selecciona "Database"
3. Click "Add PostgreSQL"
4. Railway crea la base de datos automáticamente
5. La variable DATABASE_URL se configura sola ✅

---

## PASO 4: AGREGAR REDIS
1. Click botón "+ New" otra vez
2. Selecciona "Database"
3. Click "Add Redis"
4. Railway crea Redis automáticamente
5. La variable REDIS_URL se configura sola ✅

---

## PASO 5: CONFIGURAR VARIABLES DE ENTORNO

1. Click en tu servicio de backend (el que dice "dreamduel-backend-web")
2. Ve a la pestaña "Variables"
3. Click "Raw Editor" (arriba a la derecha)
4. Pega estas variables (REEMPLAZA LOS VALORES):

```env
# App Settings
ENVIRONMENT=production
DEBUG=False
APP_NAME=DreamDuel
SECRET_KEY=^X)GzKKFu|w_=?Jse8q(3Ufz#z)f3DusL}X#DCR-}}wpU-V755|+l=aNSp-B2T3a
JWT_SECRET=a*R+mcMUcU|p&YFiqk:=E_e^%3!B=*XgLWB}jch?M3gYzmdvRQ^83BJ#A,Ded1lb
API_V1_PREFIX=/api
FRONTEND_URL=https://tu-frontend.com
CORS_ORIGINS=https://tu-frontend.com,https://www.tu-frontend.com

# JWT
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# PayPal (Por ahora usa SANDBOX, luego cambias a LIVE)
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=AR6T0ru_xbj7LrE604VdR5VZGw50P4c05XxCCF_1ZcPrLItrU98TyTd4tCoTZzJfevFdCmH3gmf0cB_n
PAYPAL_CLIENT_SECRET=EIDnwAlhseKwp1PZqDxEElp4bWwgaNyo6Q9IyWjoUnKb0smPvJMO8r1AMZ2KqEj7OARctTV950WHMfPg
PAYPAL_WEBHOOK_ID=
PAYPAL_MONTHLY_PLAN_ID=P-2RT56739PB2154449NGRB4UQ
PAYPAL_YEARLY_PLAN_ID=

# Cloudinary
CLOUDINARY_CLOUD_NAME=drmshetga
CLOUDINARY_API_KEY=424968928673351
CLOUDINARY_API_SECRET=hs_xTDxeiUaLeymad8EtSv7h4Ag

# Resend
RESEND_API_KEY=re_Fp5JSHBK_EbMQ5aV5ETtswHRPZatyxcm3
FROM_EMAIL=noreply@dreamduel.lat

# Google OAuth (Configura después en Google Cloud Console)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Apple Sign In (Configura después en Apple Developer)
APPLE_CLIENT_ID=com.dreamduel.app
APPLE_TEAM_ID=your_apple_team_id
APPLE_KEY_ID=your_apple_key_id
APPLE_PRIVATE_KEY=your_apple_private_key

# Celery (Railway Redis URLs se configuran automáticas)
CELERY_BROKER_URL=${{Redis.REDIS_URL}}/1
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/2

# Sentry (Opcional)
SENTRY_DSN=https://693537a66270d775b11919143b33f1d3@o4510959334850560.ingest.us.sentry.io/4510959340486656

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

5. Click "Update Variables"

**IMPORTANTE:** Railway auto-configura:
- `DATABASE_URL` (desde PostgreSQL que agregaste)
- `REDIS_URL` (desde Redis que agregaste)
- `PORT` (Railway lo asigna automáticamente)

---

## PASO 6: CONFIGURAR START COMMAND

1. En tu servicio, ve a pestaña "Settings"
2. Scroll hasta "Deploy"
3. En "Start Command" pon:
   ```
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Click "Update"

Esto ejecuta las migraciones antes de iniciar el servidor ✅

---

## PASO 7: DEPLOY AUTOMÁTICO

Railway hace deploy automático. Verás:
1. "Building..." (instala dependencias)
2. "Deploying..." (ejecuta migraciones y arranca servidor)
3. "Active" (✅ Deploy exitoso!)

---

## PASO 8: OBTENER URL DE PRODUCCIÓN

1. En tu servicio, ve a pestaña "Settings"
2. Scroll hasta "Networking"
3. Click "Generate Domain"
4. Railway te da una URL como:
   ```
   https://dreamduel-backend-production.up.railway.app
   ```

**¡Guarda esta URL!** La necesitas para:
- Configurar en tu frontend
- Configurar webhooks de PayPal
- Configurar Google/Apple OAuth

---

## PASO 9: VERIFICAR QUE FUNCIONA

Abre en tu navegador:
```
https://tu-url.up.railway.app/docs
```

Deberías ver la documentación Swagger ✅

Prueba el health check:
```
https://tu-url.up.railway.app/health
```

Debe retornar:
```json
{
  "status": "ok",
  "db": "ok",
  "redis": "ok",
  "environment": "production",
  "version": "1.0.0"
}
```

---

## PASO 10: CONFIGURAR SERVICIOS EXTERNOS (DESPUÉS)

Una vez que tengas la URL, configura:

### A. PayPal Webhooks
1. Ve a https://developer.paypal.com/dashboard
2. Webhooks → Create Webhook
3. URL: `https://tu-url.up.railway.app/api/payments/webhook`
4. Events: Todos de "Billing" y "Payment"

### B. Google OAuth
1. Ve a https://console.cloud.google.com/apis/credentials
2. Edita tu OAuth Client
3. Authorized origins: `https://tu-url.up.railway.app`
4. Redirect URIs: `https://tu-frontend.com/auth/callback`

### C. Apple Sign In
1. Ve a https://developer.apple.com/account
2. Configura Service ID
3. Domain: `tu-dominio.com`
4. Return URL: `https://tu-frontend.com/auth/callback`

---

## 🎯 COSTO

Railway te da:
- **$5 USD de crédito gratis al mes**
- PostgreSQL gratis (500MB)
- Redis gratis (100MB)
- 500 horas de ejecución gratis

**Costo después del free tier:** ~$5-15 USD/mes dependiendo del uso

---

## 🔄 AUTO-DEPLOY

Cada vez que hagas `git push origin main`, Railway:
1. Detecta el cambio
2. Hace build automático
3. Ejecuta migraciones
4. Redeploy sin downtime

---

## 📞 SOPORTE

- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

---

## ✅ CHECKLIST RÁPIDO

- [ ] Cuenta creada en Railway
- [ ] Proyecto conectado con GitHub
- [ ] PostgreSQL agregado
- [ ] Redis agregado
- [ ] Variables de entorno configuradas
- [ ] Start command configurado
- [ ] Deploy exitoso (status: Active)
- [ ] URL generada
- [ ] /docs funciona
- [ ] /health retorna OK
- [ ] PayPal webhook configurado
- [ ] Google OAuth configurado
- [ ] Frontend conectado

**¡LISTO PARA PRODUCCIÓN!** 🚀
