# 🔔 Configuración de Webhooks y OAuth

Esta guía te ayudará a configurar los webhooks de PayPal y OAuth de Google/Apple para tu aplicación.

---

## 📋 Índice

1. [PayPal Webhooks](#paypal-webhooks)
2. [Google OAuth](#google-oauth)
3. [Apple Sign In](#apple-sign-in)
4. [Variables de Entorno](#variables-de-entorno)
5. [Testing](#testing)

---

## 🔔 PayPal Webhooks

### Paso 1: Crear Webhook en PayPal Dashboard

1. **Ve a:** https://developer.paypal.com/dashboard/webhooks
2. **Click en "Create Webhook"**
3. **Webhook Configuration:**
   - **Webhook URL:** `https://tu-dominio.com/api/payments/webhook`
   - Para desarrollo local con ngrok: `https://abc123.ngrok.io/api/payments/webhook`

4. **Selecciona los siguientes eventos:**
   - ✅ `BILLING.SUBSCRIPTION.ACTIVATED`
   - ✅ `BILLING.SUBSCRIPTION.CANCELLED`
   - ✅ `BILLING.SUBSCRIPTION.SUSPENDED`
   - ✅ `BILLING.SUBSCRIPTION.UPDATED`
   - ✅ `PAYMENT.SALE.COMPLETED`

5. **Click "Create"**

6. **Copia el Webhook ID** (se ve como `WH-XXXXXXXXX`)

### Paso 2: Configurar en tu .env

```env
PAYPAL_WEBHOOK_ID=WH-XXXXXXXXX
```

### Paso 3: Testing con ngrok (para desarrollo local)

```bash
# Instalar ngrok
winget install ngrok

# Iniciar ngrok
ngrok http 8000

# Ngrok te dará una URL como: https://abc123.ngrok.io
# Usa esta URL + /api/payments/webhook en PayPal Dashboard
```

### Verificación

El webhook está configurado para:
- ✅ Activar premium cuando se aprueba suscripción
- ✅ Cancelar premium cuando se cancela suscripción
- ✅ Suspender premium por falta de pago
- ✅ Crear registros de facturación

---

## 🔐 Google OAuth

### Paso 1: Crear Proyecto en Google Cloud Console

1. **Ve a:** https://console.cloud.google.com/
2. **Crear nuevo proyecto:** "DreamDuel" (o el nombre que prefieras)
3. **Habilitar Google+ API:**
   - Ve a "APIs & Services" > "Library"
   - Busca "Google+ API"
   - Click "Enable"

### Paso 2: Crear OAuth Credentials

1. **Ve a:** "APIs & Services" > "Credentials"
2. **Click "Create Credentials" > "OAuth client ID"**
3. **Configure:**
   - **Application type:** Web application
   - **Name:** DreamDuel Web Client
   - **Authorized JavaScript origins:**
     ```
     http://localhost:3000
     https://tu-dominio.com
     ```
   - **Authorized redirect URIs:**
     ```
     http://localhost:3000/auth/google/callback
     https://tu-dominio.com/auth/google/callback
     ```

4. **Click "Create"**

5. **Copia:**
   - Client ID
   - Client Secret

### Paso 3: Configurar en tu .env

```env
GOOGLE_CLIENT_ID=tu_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_google_client_secret
```

### Frontend Integration

```javascript
// Frontend - Obtener token de Google
const googleLogin = async () => {
  // Usar Google Sign-In SDK
  const response = await google.accounts.id.initialize({
    client_id: 'TU_GOOGLE_CLIENT_ID',
    callback: async (response) => {
      // Enviar token a tu backend
      const result = await fetch('http://localhost:8000/api/oauth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: response.credential })
      });
      
      const data = await result.json();
      // data.access_token y data.refresh_token
    }
  });
};
```

---

## 🍎 Apple Sign In

### Paso 1: Configurar en Apple Developer

1. **Ve a:** https://developer.apple.com/account/
2. **Ve a:** "Certificates, Identifiers & Profiles"
3. **Click "Identifiers" > "+"**
4. **Selecciona "App IDs"**
5. **Configure:**
   - **Description:** DreamDuel
   - **Bundle ID:** com.dreamduel.web
   - **Capabilities:** ✅ Sign In with Apple

6. **Click "Continue" > "Register"**

### Paso 2: Crear Service ID

1. **Click "Identifiers" > "+"**
2. **Selecciona "Services IDs"**
3. **Configure:**
   - **Description:** DreamDuel Web Service
   - **Identifier:** com.dreamduel.web.service
   - ✅ Sign In with Apple

4. **Click "Configure"**
5. **Domains and Subdomains:**
   ```
   tu-dominio.com
   ```
6. **Return URLs:**
   ```
   https://tu-dominio.com/auth/apple/callback
   ```

### Paso 3: Configurar en tu .env

```env
APPLE_CLIENT_ID=com.dreamduel.web.service
APPLE_TEAM_ID=tu_team_id
APPLE_KEY_ID=tu_key_id
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\ntu_private_key\n-----END PRIVATE KEY-----
```

### Frontend Integration

```javascript
// Frontend - Apple Sign In
const appleLogin = async () => {
  AppleID.auth.init({
    clientId: 'com.dreamduel.web.service',
    scope: 'name email',
    redirectURI: 'https://tu-dominio.com/auth/apple/callback',
    usePopup: true
  });
  
  const response = await AppleID.auth.signIn();
  
  // Enviar a tu backend
  const result = await fetch('http://localhost:8000/api/oauth/apple', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code: response.authorization.code,
      id_token: response.authorization.id_token
    })
  });
  
  const data = await result.json();
  // data.access_token y data.refresh_token
};
```

---

## 🔑 Variables de Entorno

Asegúrate de tener todas estas variables en tu `.env`:

```env
# App
FRONTEND_URL=http://localhost:3000

# PayPal
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=tu_paypal_client_id
PAYPAL_CLIENT_SECRET=tu_paypal_secret
PAYPAL_WEBHOOK_ID=WH-XXXXXXXXX
PAYPAL_MONTHLY_PLAN_ID=P-XXXXXXXXX

# Google OAuth
GOOGLE_CLIENT_ID=tu_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu_google_client_secret

# Apple OAuth
APPLE_CLIENT_ID=com.dreamduel.web.service
APPLE_TEAM_ID=tu_team_id
APPLE_KEY_ID=tu_key_id
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\ntu_key\n-----END PRIVATE KEY-----
```

---

## ✅ Testing

### Probar PayPal Webhook

```bash
# Simular webhook de PayPal
curl -X POST http://localhost:8000/api/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "BILLING.SUBSCRIPTION.ACTIVATED",
    "resource": {
      "id": "I-TEST123",
      "status": "ACTIVE"
    }
  }'
```

### Probar Google OAuth

1. **Ve a Swagger:** http://localhost:8000/docs
2. **POST /api/oauth/google**
3. **Pega un Google ID token válido**

### Probar Apple OAuth

1. **Ve a Swagger:** http://localhost:8000/docs
2. **POST /api/oauth/apple**
3. **Pega code e id_token de Apple**

---

## 📚 Endpoints Disponibles

### PayPal Webhooks
- `POST /api/payments/webhook` - Recibe eventos de PayPal

### Google OAuth
- `POST /api/oauth/google` - Login con Google
- `GET /api/oauth/google/url` - Obtener URL de autorización

### Apple OAuth
- `POST /api/oauth/apple` - Login con Apple
- `GET /api/oauth/apple/config` - Obtener configuración

---

## 🚀 Producción

Antes de ir a producción:

1. ✅ Cambiar `PAYPAL_MODE=live`
2. ✅ Obtener credenciales de PayPal de producción
3. ✅ Actualizar webhook URL a dominio real (sin ngrok)
4. ✅ Configurar Google OAuth con dominio de producción
5. ✅ Configurar Apple con dominio de producción
6. ✅ Implementar verificación de firma de Apple ID token
7. ✅ Habilitar HTTPS
8. ✅ Configurar rate limiting

---

## ❓ Troubleshooting

### PayPal Webhook no funciona
- ✅ Verifica que ngrok esté corriendo
- ✅ Verifica que la URL del webhook sea correcta
- ✅ Revisa los logs de PayPal Dashboard

### Google OAuth falla
- ✅ Verifica que el Client ID sea correcto
- ✅ Verifica authorized redirect URIs
- ✅ Asegúrate de que Google+ API esté habilitado

### Apple Sign In falla
- ✅ Verifica Service ID
- ✅ Verifica Return URLs
- ✅ Implementa verificación de token signature
