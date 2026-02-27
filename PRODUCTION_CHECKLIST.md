# ✅ CHECKLIST DE CONFIGURACIÓN PARA PRODUCCIÓN

## 📋 ANTES DE DESPLEGAR

### 1. Generar Claves Seguras ✅
```bash
python generate_secrets.py
```
- [ ] Copiar `SECRET_KEY` a variables de entorno de producción
- [ ] Copiar `JWT_SECRET` a variables de entorno de producción
- [ ] ⚠️ NUNCA compartir estas claves

---

### 2. Configurar Email Service (Resend) ✅
- [ ] Ir a https://resend.com/domains
- [ ] Verificar dominio `dreamduel.lat` (agregar registros DNS)
- [ ] Crear API Key de producción
- [ ] Configurar variable: `RESEND_API_KEY=re_XXXXX`
- [ ] Configurar variable: `FROM_EMAIL=noreply@dreamduel.lat`

**Verificación DNS requerida:**
```
dreamduel.lat TXT "resend-domain-verification=XXXXX"
_resend._domainkey.dreamduel.lat CNAME XXXXX.resend.com
```

---

### 3. PayPal Modo Producción 🔴 CRÍTICO
- [ ] Ir a https://developer.paypal.com/dashboard
- [ ] Cambiar de "Sandbox" a "Live" (esquina superior derecha)
- [ ] Crear nueva App en Live mode
- [ ] Copiar Client ID y Secret
- [ ] Configurar variables:
  ```
  PAYPAL_MODE=live
  PAYPAL_CLIENT_ID=XXXXX
  PAYPAL_CLIENT_SECRET=XXXXX
  ```

- [ ] **Crear planes de producción:**
  ```bash
  # Temporalmente cambiar .env a modo live
  python create_paypal_plan.py
  ```
  
- [ ] Copiar Plan IDs:
  ```
  PAYPAL_MONTHLY_PLAN_ID=P-XXXXX
  PAYPAL_YEARLY_PLAN_ID=P-XXXXX
  ```

- [ ] **Configurar Webhook en PayPal:**
  1. Dashboard Live → Webhooks
  2. Create Webhook
  3. URL: `https://tuapp.up.railway.app/api/payments/webhook`
  4. Events: Seleccionar todos de "Billing subscriptions" y "Payment"
  5. Copiar Webhook ID: `PAYPAL_WEBHOOK_ID=XXXXX`

---

### 4. Google OAuth Producción
- [ ] Ir a https://console.cloud.google.com/apis/credentials
- [ ] Editar tu "OAuth 2.0 Client ID"
- [ ] **Authorized JavaScript origins:**
  ```
  https://tu-dominio.com
  https://tuapp.up.railway.app
  ```
- [ ] **Authorized redirect URIs:**
  ```
  https://tu-dominio.com/auth/callback
  https://tuapp.up.railway.app/auth/callback
  ```
- [ ] Guardar cambios
- [ ] Verificar variables:
  ```
  GOOGLE_CLIENT_ID=123456-abc.apps.googleusercontent.com
  GOOGLE_CLIENT_SECRET=GOCSPX-XXXXX
  ```

---

### 5. Apple Sign In Producción
- [ ] Ir a https://developer.apple.com/account/resources/identifiers
- [ ] **Crear/Editar Service ID:**
  - Identifier: `com.dreamduel.app`
  - Configure: Sign In with Apple
  
- [ ] **Configurar dominios:**
  - Primary App Domain: `dreamduel.lat`
  - Return URLs: `https://dreamduel.lat/auth/callback`
  
- [ ] **Generar Private Key:**
  - Certificates, IDs & Profiles → Keys → Create Key
  - Enable "Sign In with Apple"
  - Descargar archivo `.p8`
  
- [ ] Configurar variables:
  ```
  APPLE_CLIENT_ID=com.dreamduel.app
  APPLE_TEAM_ID=XXXXX
  APPLE_KEY_ID=XXXXX
  APPLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
  ```

---

### 6. Variables de Entorno en Railway/Render
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY=` (generado con generate_secrets.py)
- [ ] `JWT_SECRET=` (generado con generate_secrets.py)
- [ ] `FRONTEND_URL=https://tu-dominio.com`
- [ ] `CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com`
- [ ] `DATABASE_URL=` (Railway lo provee automáticamente)
- [ ] `REDIS_URL=` (Railway lo provee automáticamente)
- [ ] Todas las de PayPal, Google, Apple, Resend
- [ ] `RATE_LIMIT_PER_MINUTE=100`

---

### 7. Setup en Railway (Recomendado)

#### A. Crear Proyecto
- [ ] Ir a https://railway.app
- [ ] Login con GitHub
- [ ] "New Project" → "Deploy from GitHub repo"
- [ ] Seleccionar `DreamDuel-BackEnd-Web`

#### B. Agregar Bases de Datos
- [ ] Click "+ New" → "Database" → "PostgreSQL"
- [ ] Click "+ New" → "Database" → "Redis"
- [ ] Railway auto-configura `DATABASE_URL` y `REDIS_URL`

#### C. Configurar Variables
- [ ] Click en tu servicio → Tab "Variables"
- [ ] Click "New Variable" o "Raw Editor"
- [ ] Pegar todas las variables de `.env.production.example`

#### D. Configurar Deploy
- [ ] Tab "Settings" → "Build & Deploy"
- [ ] **Start Command:**
  ```
  alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
- [ ] **Custom Domain (opcional):**
  - Tab "Settings" → "Networking"
  - Agregar tu dominio

#### E. Deploy
- [ ] Railway hace auto-deploy en cada push a main
- [ ] Ver logs: Tab "Deployments" → Click en deployment actual

---

### 8. Verificar Servicios Habilitados ✅
- [x] Email service habilitado en `auth.py`
- [x] Rate limiting habilitado en `main.py`
- [x] Password hashing con Argon2
- [x] PayPal REST API implementado
- [x] OAuth endpoints listos
- [x] Webhook endpoint listo
- [x] Migraciones ejecutadas (001_initial, 002_oauth)

---

### 9. Testing Post-Deploy
- [ ] **Health Check:**
  ```bash
  curl https://tuapp.up.railway.app/
  ```

- [ ] **Swagger Docs:**
  ```
  https://tuapp.up.railway.app/docs
  ```

- [ ] **Test Registration:**
  - Registrar usuario nuevo
  - Verificar que llegue email de verificación
  
- [ ] **Test Login:**
  - Login con credenciales
  - Verificar token JWT
  
- [ ] **Test Google OAuth:**
  - Login con Google
  - Verificar creación de usuario
  
- [ ] **Test PayPal:**
  - Crear suscripción
  - Aprobar en PayPal
  - Verificar webhook recibido
  - Verificar usuario premium
  
- [ ] **Test Upload:**
  - Subir imagen a Cloudinary
  - Verificar URL generada

---

### 10. Monitoreo y Seguridad
- [ ] **Sentry configurado:**
  ```
  SENTRY_DSN=https://XXXXX@oXXXXXX.ingest.sentry.io/XXXXXX
  ```
  
- [ ] **HTTPS activo** (Railway lo provee automático)
  
- [ ] **CORS configurado correctamente:**
  - Solo tu frontend domain
  - No usar `*` en producción
  
- [ ] **Rate Limiting activo:**
  - 100 requests/minuto configurado
  
- [ ] **Logs monitoreados:**
  - Railway Dashboard → Logs tab
  - Sentry para errores

---

### 11. Frontend Connection
En tu frontend (Next.js), configurar:

```env
# Frontend .env.production
NEXT_PUBLIC_API_URL=https://tuapp.up.railway.app
NEXT_PUBLIC_GOOGLE_CLIENT_ID=123456-abc.apps.googleusercontent.com
NEXT_PUBLIC_APPLE_CLIENT_ID=com.dreamduel.app
```

**Ejemplo de uso:**
```javascript
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
```

---

### 12. Backup y Rollback
- [ ] **Database backup automático** (Railway lo hace automático)
- [ ] **Git tags para versiones:**
  ```bash
  git tag -a v1.0.0 -m "Primera versión en producción"
  git push origin v1.0.0
  ```
- [ ] **Rollback en Railway:**
  - Deployments tab → Click deployment anterior → "Redeploy"

---

## 🚀 LISTO PARA PRODUCCIÓN CUANDO:
- ✅ Todas las variables de entorno configuradas
- ✅ PayPal en modo live con planes creados
- ✅ Google OAuth autorizado para dominio de producción
- ✅ Apple Sign In configurado
- ✅ Resend domain verificado
- ✅ DATABASE_URL y REDIS_URL configurados
- ✅ Migraciones ejecutadas en producción (`alembic upgrade head`)
- ✅ Tests pasados en producción
- ✅ Monitoring activo (Sentry)

---

## 📞 SOPORTE
- Railway Docs: https://docs.railway.app
- PayPal Docs: https://developer.paypal.com/docs
- Resend Docs: https://resend.com/docs
- Google OAuth: https://developers.google.com/identity
- Apple Sign In: https://developer.apple.com/sign-in-with-apple
