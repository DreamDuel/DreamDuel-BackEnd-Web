# 🚀 Guía de Deployment DreamDuel Backend

## 📋 Checklist Pre-Deployment

### ✅ Código
- [x] Migrar contraseñas de bcrypt a argon2
- [x] Actualizar servicio PayPal a API REST
- [x] Configurar webhooks de PayPal
- [x] Implementar OAuth (Google, Apple)
- [x] Actualizar requirements.txt
- [ ] Re-habilitar emails (cuando configures Resend en producción)
- [ ] Re-habilitar rate limiting
- [ ] Configurar variables de entorno de producción

### ✅ Base de Datos
- [x] Migraciones creadas (001_initial, 002_oauth)
- [ ] Ejecutar migraciones en producción
- [ ] Configurar backup automático

### ✅ Seguridad
- [x] JWT configurado
- [x] Argon2 para passwords
- [ ] HTTPS habilitado (en producción)
- [ ] SECRET_KEY fuerte generado
- [ ] Cambiar DEBUG=False en producción

---

## 🌐 Opciones de Deployment

### **OPCIÓN 1: Railway (RECOMENDADO - Más fácil)**

**Ventajas:**
- ✅ Deploy automático desde GitHub
- ✅ PostgreSQL incluido gratis
- ✅ Redis incluido gratis
- ✅ SSL/HTTPS automático
- ✅ $5 gratis/mes

**Pasos:**

1. **Ve a** https://railway.app/
2. **Sign up** con GitHub
3. **New Project → Deploy from GitHub repo**
4. **Selecciona tu repositorio:** `DreamDuel-BackEnd-Web`
5. **Railway detectará automáticamente:** Python + requirements.txt

6. **Agregar PostgreSQL:**
   - En tu proyecto, click **"+ New"**
   - Selecciona **"Database → PostgreSQL"**
   - Railway auto-generará `DATABASE_URL`

7. **Agregar Redis:**
   - Click **"+ New"**
   - Selecciona **"Database → Redis"**
   - Railway auto-generará `REDIS_URL`

8. **Configurar Variables de Entorno:**
   - Click en tu servicio → **"Variables"**
   - Agregar todas las variables del `.env`:

```env
# App
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=genera-un-secret-key-super-seguro-aqui-con-64-caracteres
JWT_SECRET=genera-otro-jwt-secret-super-seguro-aqui-con-64-caracteres
FRONTEND_URL=https://tu-dominio-frontend.com
CORS_ORIGINS=https://tu-dominio-frontend.com,https://www.tu-dominio-frontend.com

# Database (auto-generada por Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (auto-generada por Railway)
REDIS_URL=${{Redis.REDIS_URL}}

# PayPal (PRODUCCIÓN)
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=tu_paypal_client_id_de_produccion
PAYPAL_CLIENT_SECRET=tu_paypal_secret_de_produccion
PAYPAL_WEBHOOK_ID=tu_webhook_id_de_produccion
PAYPAL_MONTHLY_PLAN_ID=tu_plan_id_de_produccion
PAYPAL_YEARLY_PLAN_ID=tu_plan_yearly_de_produccion

# Cloudinary
CLOUDINARY_CLOUD_NAME=tu_cloudinary_cloud
CLOUDINARY_API_KEY=tu_cloudinary_api_key
CLOUDINARY_API_SECRET=tu_cloudinary_secret

# Resend
RESEND_API_KEY=tu_resend_api_key
FROM_EMAIL=noreply@tu-dominio.com

# Google OAuth (PRODUCCIÓN)
GOOGLE_CLIENT_ID=tu_google_client_id_produccion.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_google_secret_produccion

# Apple OAuth (PRODUCCIÓN)
APPLE_CLIENT_ID=com.dreamduel.web
APPLE_TEAM_ID=tu_team_id
APPLE_KEY_ID=tu_key_id
APPLE_PRIVATE_KEY=tu_private_key

# AI Services
REPLICATE_API_KEY=tu_replicate_key
ANTHROPIC_API_KEY=tu_anthropic_key
```

9. **Configurar Start Command:**
   - En "Settings → Deploy"
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

10. **Deploy:**
    - Railway hace deploy automático cada push a `main`
    - O click **"Deploy"** manualmente

11. **Obtener URL:**
    - Railway te da una URL como: `https://dreamduel-backend.up.railway.app`
    - Puedes agregar dominio custom después

---

### **OPCIÓN 2: Render**

1. **Ve a** https://render.com/
2. **Crear Web Service** desde GitHub
3. **Configurar:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Agregar PostgreSQL:** Render ofrece PostgreSQL gratis
5. **Variables de entorno:** Igual que Railway

---

### **OPCIÓN 3: Heroku**

Similar a Railway pero:
- No incluye Redis gratis
- Menos intuitivo
- Postgres gratis con límites

---

### **OPCIÓN 4: VPS (DigitalOcean, AWS EC2, etc.)**

**Más complejo** pero más control:

```bash
# En el servidor
git clone https://github.com/tu-usuario/DreamDuel-BackEnd-Web.git
cd DreamDuel-BackEnd-Web

# Instalar dependencias
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env
nano .env  # Agregar todas las variables

# Ejecutar migraciones
alembic upgrade head

# Instalar y configurar nginx
sudo apt install nginx

# Configurar systemd service
sudo nano /etc/systemd/system/dreamduel.service
```

**Archivo dreamduel.service:**
```ini
[Unit]
Description=DreamDuel FastAPI
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/DreamDuel-BackEnd-Web
Environment="PATH=/home/ubuntu/DreamDuel-BackEnd-Web/venv/bin"
ExecStart=/home/ubuntu/DreamDuel-BackEnd-Web/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

---

## 🔧 Configuraciones Post-Deployment

### 1. PayPal Producción

1. **Cambiar a Live:**
   - Ve a https://developer.paypal.com/
   - Cambia de "Sandbox" a "Live" (switch arriba derecha)

2. **Crear credenciales de producción:**
   - Apps → Create App (en modo Live)
   - Copia Client ID y Secret

3. **Crear planes de producción:**
   ```bash
   # Actualizar create_paypal_plan.py con credenciales LIVE
   python create_paypal_plan.py
   ```

4. **Configurar webhook:**
   - URL: `https://tu-dominio.com/api/payments/webhook`
   - Eventos: BILLING.SUBSCRIPTION.*, PAYMENT.SALE.COMPLETED

### 2. Google OAuth Producción

1. **Google Cloud Console:**
   - Agregar dominio de producción a "Authorized JavaScript origins"
   - Agregar callback de producción a "Authorized redirect URIs"

### 3. Apple Sign In Producción

1. **Apple Developer:**
   - Configurar dominio real en Service ID
   - Actualizar Return URLs

### 4. Resend Email

1. **Verificar dominio:**
   - Ve a Resend → Domains
   - Agregar registros DNS (MX, TXT)

2. **Re-habilitar emails en código:**
   - Descomentar código en `app/api/v1/routes/auth.py`

---

## 🧪 Testing en Producción

```bash
# Health check
curl https://tu-dominio.com/

# Swagger
https://tu-dominio.com/docs

# Login
curl -X POST https://tu-dominio.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"emailOrUsername": "test@test.com", "password": "test123"}'
```

---

## 📊 Monitoreo

### Sentry (Recomendado)

1. **Crear cuenta:** https://sentry.io/
2. **Crear proyecto:** Python + FastAPI
3. **Copiar DSN**
4. **Agregar a .env:**
   ```env
   SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
   ```

### Logs en Railway

- Dashboard → Tu servicio → "Logs"
- Logs en tiempo real

---

## 🔐 Seguridad Final

### Generar SECRETS fuertes:

```python
# En Python
import secrets
print(secrets.token_urlsafe(64))  # Para SECRET_KEY
print(secrets.token_urlsafe(64))  # Para JWT_SECRET
```

### Checklist:
- [ ] SECRET_KEY y JWT_SECRET únicos y largos (64+ caracteres)
- [ ] DEBUG=False en producción
- [ ] HTTPS habilitado
- [ ] CORS configurado solo para tu frontend
- [ ] Rate limiting habilitado
- [ ] Sentry configurado
- [ ] Backups de base de datos automatizados

---

## 🌍 Conectar con Frontend

### Variables del frontend (.env.local):

```env
NEXT_PUBLIC_API_URL=https://tu-backend.up.railway.app
NEXT_PUBLIC_GOOGLE_CLIENT_ID=tu_google_client_id
NEXT_PUBLIC_APPLE_CLIENT_ID=com.dreamduel.web
```

### Ejemplo de fetch:

```javascript
// Frontend - Registro
const register = async (username, email, password) => {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  });
  return await response.json();
};

// Login
const login = async (emailOrUsername, password) => {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ emailOrUsername, password })
  });
  return await response.json();
};
```

---

## 🚀 Deploy Checklist Final

- [ ] Código subido a GitHub (main branch)
- [ ] Railway/Render proyecto creado
- [ ] PostgreSQL agregado
- [ ] Redis agregado
- [ ] Variables de entorno configuradas
- [ ] Migraciones ejecutadas
- [ ] PayPal webhooks configurados
- [ ] Google OAuth configurado para producción
- [ ] Apple OAuth configurado para producción
- [ ] Dominio custom configurado (opcional)
- [ ] SSL/HTTPS funcionando
- [ ] Frontend puede conectarse al backend
- [ ] Testing completo end-to-end

**¡Listo para lanzar!** 🎉
