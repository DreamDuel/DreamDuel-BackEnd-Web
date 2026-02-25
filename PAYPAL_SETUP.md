# Guía Completa de Configuración de PayPal para Perú

Esta guía te ayudará a configurar PayPal en el backend y conectarlo con tu frontend para recibir pagos en Perú.

## 📋 Índice
1. [¿Por qué PayPal para Perú?](#1-por-qué-paypal-para-perú)
2. [Crear Cuenta de PayPal Business](#2-crear-cuenta-de-paypal-business)
3. [Obtener Credenciales de API](#3-obtener-credenciales-de-api)
4. [Crear Productos y Planes de Suscripción](#4-crear-productos-y-planes-de-suscripción)
5. [Configurar Backend](#5-configurar-backend)
6. [Configurar Webhooks](#6-configurar-webhooks)
7. [Integración con Frontend](#7-integración-con-frontend)
8. [Endpoints Disponibles](#8-endpoints-disponibles)
9. [Ejemplos de Frontend](#9-ejemplos-de-frontend)
10. [Costos y Comisiones](#10-costos-y-comisiones)
11. [Retirar Dinero a Banco Peruano](#11-retirar-dinero-a-banco-peruano)

---

## 1. ¿Por qué PayPal para Perú?

### ✅ Ventajas:
- **Disponible en Perú**: A diferencia de Stripe
- **Sin costos iniciales**: Registro y mantenimiento gratis
- **Pago sin cuenta PayPal**: Clientes pagan solo con tarjeta (Visa, Mastercard) como invitados
- **Retiros gratis**: A bancos peruanos (BCP, Interbank, BBVA, etc.) en 1-2 días
- **Aceptación global**: Recibe pagos de todo el mundo

### 💰 Costos (solo pagas cuando vendes):
- **Internacional**: 5.4% + $0.30 USD por transacción
- **Local (Perú)**: 3.4% + $0.30 USD por transacción
- **Sin cuotas mensuales**

---

## 2. Crear Cuenta de PayPal Business

### Paso 2.1: Registro
1. Ve a https://www.paypal.com/pe/business
2. Haz clic en **"Crear cuenta empresarial"**
3. Ingresa tu correo electrónico
4. Elige **"Cuenta business"**

### Paso 2.2: Completar información
1. Información personal:
   - Nombre completo
   - DNI
   - Teléfono peruano
   - Dirección en Perú
2. Información del negocio:
   - Tipo: "Servicios en línea" o "Software/SaaS"
   - Nombre de tu negocio: "DreamDuel"
   - Categoría: "Software y servicios online"

### Paso 2.3: Verificar cuenta
1. PayPal pedirá verificar tu teléfono (SMS)
2. Luego pedirá verificar tu identidad (DNI o RUC)
3. Conecta una cuenta bancaria peruana (opcional pero recomendado)

**Tiempo estimado**: 5-10 minutos

---

## 3. Obtener Credenciales de API

### Paso 3.1: Acceder al Dashboard de Desarrolladores
1. Inicia sesión en https://www.paypal.com
2. Ve a https://developer.paypal.com
3. Haz clic en **"Dashboard"** (arriba a la derecha)

### Paso 3.2: Crear App en Sandbox (Testing)
1. En el Dashboard, ve a **"My Apps & Credentials"**
2. Asegúrate de estar en pestaña **"Sandbox"**
3. Haz clic en **"Create App"**
4. Nombre de la app: "DreamDuel Backend"
5. Haz clic en **"Create App"**

### Paso 3.3: Obtener credenciales de Sandbox
Verás dos credenciales importantes:
- **Client ID**: (APxxxxxxxxxxxxxxxxxxxx)
- **Secret**: Haz clic en "Show" para verlo

**⚠️ IMPORTANTE**: Estas son para **testing**. Para producción, necesitarás otras credenciales.

### Paso 3.4: Habilitar Subscriptions
1. En la misma página de tu app
2. En la sección **"Features"**
3. Marca la opción **"Subscriptions"** 
4. Guarda cambios

---

## 4. Crear Productos y Planes de Suscripción

### Opción A: Por Dashboard (Más Fácil)

#### Paso 4.1: Ir a suscripciones
1. En https://www.paypal.com (modo Sandbox primero)
2. Ve a **"Productos y servicios"** → **"Suscripciones"**
3. O directo: https://www.sandbox.paypal.com/billing/plans

#### Paso 4.2: Crear producto
1. Haz clic en **"Crear producto"**
2. Nombre: "DreamDuel Premium"
3. Tipo: "Servicio" o "Digital"
4. Categoría: "Software"
5. Guardar

#### Paso 4.3: Crear plan mensual
1. Después de crear el producto, haz clic en **"Crear plan"**
2. Información del plan:
   - Nombre: "DreamDuel Premium - Mensual"
   - ID del plan: "dreamduel-premium-monthly" (o lo que prefieras)
   - Descripción: "Suscripción mensual premium de DreamDuel"
3. Precio:
   - Precio: $9.99 USD
   - Frecuencia de facturación: Monthly (Mensual)
   - Ciclos de facturación: Continuo
4. Configuración adicional:
   - Periodo de prueba: 0 días (o 7 si quieres trial gratis)
   - Tarifa de instalación: $0
5. Guardar plan

**Copia el Plan ID**: Lo necesitarás (ej: P-XXXXXXXXXXXXXXXXX)

#### Paso 4.4: Crear plan anual
Repite el proceso:
- Nombre: "DreamDuel Premium - Anual"
- ID: "dreamduel-premium-yearly"
- Precio: $99.99 USD
- Frecuencia: Yearly (Anual)

**Copia este Plan ID también**

### Opción B: Por API (Avanzado)

Puedes crear planes programáticamente usando la API REST de PayPal. El backend ya incluye código para esto.

---

## 5. Configurar Backend

### Paso 5.1: Actualizar requirements.txt

El backend ya incluye la dependencia necesaria:
```txt
paypalrestsdk==1.13.1
```

Instalar:
```bash
pip install paypalrestsdk
```

### Paso 5.2: Actualizar archivo .env

Copia `.env.example` a `.env` y actualiza:

```bash
# PayPal Payment Integration
PAYPAL_MODE=sandbox  # sandbox para testing, live para producción
PAYPAL_CLIENT_ID=tu_client_id_de_sandbox
PAYPAL_CLIENT_SECRET=tu_secret_de_sandbox

# Plan IDs que creaste
PAYPAL_MONTHLY_PLAN_ID=P-XXXXXXXXXXXXXXX
PAYPAL_YEARLY_PLAN_ID=P-YYYYYYYYYYYYYYY

# Webhook ID (lo obtendrás en el paso 6)
PAYPAL_WEBHOOK_ID=WH-XXXXXXXXXXXXXX
```

### Paso 5.3: Verificar configuración

El backend ya está configurado con:
- `app/infrastructure/external_services/paypal_service.py` - Servicio de PayPal
- `app/api/v1/routes/payments.py` - Rutas de pago
- `app/core/config.py` - Configuración

---

## 6. Configurar Webhooks

Los webhooks notifican a tu backend cuando ocurren eventos (pago exitoso, suscripción cancelada, etc.)

### Paso 6.1: Crear webhook

1. Ve a https://developer.paypal.com/dashboard
2. Ve a **"My Apps & Credentials"** → Tu app
3. Sección **"Webhooks"**
4. Haz clic en **"Add Webhook"**
5. Webhook URL:
   ```
   https://tu-backend.com/api/v1/payments/webhook
   ```
   - Para desarrollo local: usa **ngrok** o **localtunnel**
6. Event types (selecciona estos):
   - `BILLING.SUBSCRIPTION.ACTIVATED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `BILLING.SUBSCRIPTION.SUSPENDED`
   - `BILLING.SUBSCRIPTION.UPDATED`
   - `PAYMENT.SALE.COMPLETED`
   - `PAYMENT.SALE.REFUNDED`
7. Haz clic en **"Save"**

### Paso 6.2: Obtener Webhook ID

Después de crear el webhook, verás un **Webhook ID** (WH-xxxx). Cópialo a tu `.env`:

```bash
PAYPAL_WEBHOOK_ID=WH-XXXXXXXXXXXXXX
```

### Paso 6.3: Testing con ngrok (desarrollo local)

```bash
# Instalar ngrok: https://ngrok.com/download

# Iniciar ngrok en el puerto de tu backend
ngrok http 8000

# Verás una URL como: https://abc123.ngrok.io
# Usa esta URL en el webhook: https://abc123.ngrok.io/api/v1/payments/webhook
```

---

## 7. Integración con Frontend

### Opción 1: React con @paypal/react-paypal-js

#### Instalar dependencias:
```bash
npm install @paypal/react-paypal-js
```

#### Configurar PayPal en tu app:
```javascript
// src/App.jsx
import { PayPalScriptProvider } from "@paypal/react-paypal-js";

const initialOptions = {
  "client-id": "TU_CLIENT_ID_AQUI",  // Client ID (NO el secret)
  currency: "USD",
  intent: "subscription",
  vault: true
};

function App() {
  return (
    <PayPalScriptProvider options={initialOptions}>
      {/* Tu app aquí */}
    </PayPalScriptProvider>
  );
}
```

### Opción 2: Vanilla JavaScript

```html
<!-- Incluir PayPal SDK -->
<script src="https://www.paypal.com/sdk/js?client-id=TU_CLIENT_ID&vault=true&intent=subscription"></script>
```

---

## 8. Endpoints Disponibles

El backend incluye estos endpoints:

### 8.1 Obtener planes disponibles
```
GET /api/v1/payments/plans
```

**Response:**
```json
[
  {
    "id": "monthly",
    "name": "Premium Monthly",
    "price": 999,
    "currency": "usd",
    "interval": "month",
    "paypal_plan_id": "P-XXX",
    "features": ["..."]
  }
]
```

### 8.2 Crear suscripción
```
POST /api/v1/payments/subscribe
Authorization: Bearer {token}
```

**Request:**
```json
{
  "planId": "monthly",
  "returnUrl": "https://tu-app.com/success",
  "cancelUrl": "https://tu-app.com/cancel"
}
```

**Response:**
```json
{
  "subscriptionId": "I-XXXXXXXXX",
  "approvalUrl": "https://www.paypal.com/webapps/billing/subscriptions?ba_token=xxx"
}
```

**Flujo:**
1. Backend crea la suscripción en PayPal
2. Frontend redirige al usuario a `approvalUrl`
3. Usuario aprueba en PayPal (ingresa tarjeta o usa su cuenta)
4. PayPal redirige a `returnUrl`
5. Frontend confirma la suscripción

### 8.3 Confirmar suscripción (después de aprobación)
```
POST /api/v1/payments/subscription/confirm
Authorization: Bearer {token}
```

**Request:**
```json
{
  "subscriptionId": "I-XXXXXXXXX"
}
```

### 8.4 Ver estado de suscripción
```
GET /api/v1/payments/subscription/status
Authorization: Bearer {token}
```

**Response:**
```json
{
  "subscriptionId": "I-XXX",
  "status": "ACTIVE",
  "planId": "monthly",
  "nextBillingTime": "2026-03-24T00:00:00Z"
}
```

### 8.5 Cancelar suscripción
```
POST /api/v1/payments/subscription/cancel
Authorization: Bearer {token}
```

**Request:**
```json
{
  "reason": "Usuario solicitó cancelación"
}
```

### 8.6 Ver transacciones
```
GET /api/v1/payments/transactions?limit=10
Authorization: Bearer {token}
```

### 8.7 Webhook (recibe eventos de PayPal)
```
POST /api/v1/payments/webhook
```

Manejado automáticamente por el backend.

---

## 9. Ejemplos de Frontend

### Ejemplo 1: Mostrar planes

```javascript
// PlansPage.jsx
import { useState, useEffect } from 'react';

function PlansPage() {
  const [plans, setPlans] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/payments/plans')
      .then(res => res.json())
      .then(data => setPlans(data));
  }, []);

  return (
    <div className="plans-container">
      <h1>Planes Premium de DreamDuel</h1>
      <div className="plans-grid">
        {plans.map(plan => (
          <div key={plan.id} className="plan-card">
            <h2>{plan.name}</h2>
            <p className="price">${plan.price / 100} USD</p>
            <p className="interval">por {plan.interval === 'month' ? 'mes' : 'año'}</p>
            <ul className="features">
              {plan.features.map((feature, i) => (
                <li key={i}>✓ {feature}</li>
              ))}
            </ul>
            <button 
              onClick={() => handleSubscribe(plan.id)}
              className="subscribe-btn"
            >
              Suscribirse
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  async function handleSubscribe(planId) {
    const token = localStorage.getItem('token');
    
    const response = await fetch('http://localhost:8000/api/v1/payments/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        planId: planId,
        returnUrl: `${window.location.origin}/payment/success`,
        cancelUrl: `${window.location.origin}/payment/cancel`
      })
    });

    const { approvalUrl } = await response.json();
    
    // Redirigir a PayPal para aprobar
    window.location.href = approvalUrl;
  }
}

export default PlansPage;
```

### Ejemplo 2: Página de confirmación (después de PayPal)

```javascript
// PaymentSuccessPage.jsx
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

function PaymentSuccessPage() {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    confirmSubscription();
  }, []);

  async function confirmSubscription() {
    const subscriptionId = searchParams.get('subscription_id');
    const token = localStorage.getItem('token');

    if (!subscriptionId) {
      setError('No subscription ID found');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/v1/payments/subscription/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ subscriptionId })
      });

      if (response.ok) {
        setLoading(false);
        // Suscripción confirmada
      } else {
        throw new Error('Failed to confirm subscription');
      }
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  if (loading) {
    return <div>Confirmando tu suscripción...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="success-page">
      <h1>¡Suscripción Exitosa! 🎉</h1>
      <p>Tu suscripción premium ha sido activada.</p>
      <p>Ya puedes disfrutar de todas las funciones premium de DreamDuel.</p>
      <button onClick={() => window.location.href = '/dashboard'}>
        Ir al Dashboard
      </button>
    </div>
  );
}

export default PaymentSuccessPage;
```

### Ejemplo 3: Con PayPal Buttons (alternativa con componente)

```javascript
// CheckoutPage.jsx
import { PayPalButtons } from "@paypal/react-paypal-js";

function CheckoutPage({ planId }) {
  return (
    <div>
      <h1>Checkout</h1>
      <PayPalButtons
        createSubscription={(data, actions) => {
          return actions.subscription.create({
            plan_id: 'P-XXXXXXXXX' // Tu Plan ID de PayPal
          });
        }}
        onApprove={async (data, actions) => {
          // Llamar a tu backend para confirmar
          const token = localStorage.getItem('token');
          await fetch('http://localhost:8000/api/v1/payments/subscription/confirm', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              subscriptionId: data.subscriptionID
            })
          });
          
          alert('¡Suscripción exitosa!');
          window.location.href = '/dashboard';
        }}
        onError={(err) => {
          console.error('PayPal error:', err);
          alert('Hubo un error con el pago');
        }}
      />
    </div>
  );
}
```

### Ejemplo 4: Ver estado de suscripción

```javascript
// SubscriptionStatus.jsx
import { useState, useEffect } from 'react';

function SubscriptionStatus() {
  const [subscription, setSubscription] = useState(null);

  useEffect(() => {
    fetchSubscription();
  }, []);

  async function fetchSubscription() {
    const token = localStorage.getItem('token');
    
    const response = await fetch('http://localhost:8000/api/v1/payments/subscription/status', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      setSubscription(data);
    }
  }

  async function handleCancel() {
    if (!confirm('¿Seguro que quieres cancelar tu suscripción?')) return;

    const token = localStorage.getItem('token');
    
    await fetch('http://localhost:8000/api/v1/payments/subscription/cancel', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        reason: 'Usuario solicitó cancelación'
      })
    });

    fetchSubscription(); // Recargar estado
  }

  if (!subscription) return <div>Cargando...</div>;

  return (
    <div className="subscription-status">
      <h2>Tu Suscripción</h2>
      <p>Estado: <strong>{subscription.status}</strong></p>
      <p>Plan: {subscription.planId}</p>
      <p>Próximo pago: {new Date(subscription.nextBillingTime).toLocaleDateString()}</p>
      
      {subscription.status === 'ACTIVE' && (
        <button onClick={handleCancel} className="cancel-btn">
          Cancelar Suscripción
        </button>
      )}
    </div>
  );
}
```

---

## 10. Costos y Comisiones

### Comisiones de PayPal en Perú:

| Tipo de Transacción | Comisión |
|---------------------|----------|
| **Pago local** (desde Perú) | 3.4% + $0.30 USD |
| **Pago internacional** (fuera de Perú) | 5.4% + $0.30 USD |
| **Conversión de moneda** | ~4% adicional sobre tipo de cambio |

### Ejemplo de costos:

**Plan Mensual: $9.99 USD (cliente internacional)**
- Precio: $9.99
- Comisión PayPal: 5.4% + $0.30 = $0.54 + $0.30 = $0.84
- **Recibes: $9.15 USD** (~91.6%)

**Plan Anual: $99.99 USD**
- Precio: $99.99
- Comisión PayPal: 5.4% + $0.30 = $5.40 + $0.30 = $5.70
- **Recibes: $94.29 USD** (~94.3%)

### Tips para reducir costos:
1. **Cobra en USD**: Evita conversiones innecesarias
2. **Planes anuales**: Menos transacciones = menos fees fijos de $0.30
3. **Retiros en lote**: Retira cuando tengas buen monto acumulado

---

## 11. Retirar Dinero a Banco Peruano

### Paso 11.1: Vincular cuenta bancaria

1. En PayPal, ve a **"Wallet"** (Billetera)
2. Haz clic en **"Vincular banco"**
3. Selecciona tu banco peruano:
   - BCP (Banco de Crédito del Perú)
   - Interbank
   - BBVA
   - Scotiabank
   - Otros bancos locales
4. Ingresa tu número de cuenta (ahorros o corriente)
5. PayPal hará un depósito pequeño de verificación (S/0.20 aprox)
6. Confirma el monto exacto para verificar

### Paso 11.2: Retirar fondos

1. Ve a **"Transferir dinero"** → **"Transferir a tu banco"**
2. Selecciona tu banco vinculado
3. Ingresa el monto a retirar (en USD o PEN)
4. Confirma

**Tiempo de entrega**: 1-2 días hábiles
**Costo**: **GRATIS** ✓

### Paso 11.3: Conversión USD → PEN

Si quieres recibir en Soles (PEN):
- PayPal convierte automáticamente
- Tipo de cambio: Generalmente ~4% sobre TC interbancario
- Alternativa: Retira en USD y convierte en tu banco (mejor TC)

---

## 🚀 Pasar a Producción (Live)

Cuando estés listo:

1. **Verifica tu cuenta PayPal**:
   - Sube documentos (DNI o RUC, comprobantes)
   - Vincula cuenta bancaria

2. **Crea app en modo Live**:
   - Developer Dashboard → My Apps & Credentials
   - Pestaña **"Live"** (no Sandbox)
   - Create App
   - Obtén Client ID y Secret de producción

3. **Crea planes en modo Live**:
   - Repite la creación de productos y planes en cuenta real
   - Obtén los nuevos Plan IDs

4. **Actualiza `.env` de producción**:
   ```bash
   PAYPAL_MODE=live  # ← IMPORTANTE
   PAYPAL_CLIENT_ID=tu_client_id_live
   PAYPAL_CLIENT_SECRET=tu_secret_live
   PAYPAL_MONTHLY_PLAN_ID=P-XXX_live
   PAYPAL_YEARLY_PLAN_ID=P-YYY_live
   ```

5. **Configura webhook en producción**:
   - Apuntando a tu dominio real: `https://api.dreamduel.com/api/v1/payments/webhook`

6. **Prueba con transacción real pequeña**:
   - Crea suscripción de $1 para verificar
   - Cancélala después de confirmar que funciona

---

## 🧪 Testing en Sandbox

### Cuentas de prueba PayPal:

PayPal crea automáticamente cuentas de prueba. Para verlas:

1. Developer Dashboard → **"Sandbox"** → **"Accounts"**
2. Verás cuentas como:
   - Personal (comprador): sb-xxxxx@personal.example.com
   - Business (vendedor): sb-yyyyy@business.example.com

### Realizar pago de prueba:

1. En tu app (modo sandbox), inicia el proceso de suscripción
2. PayPal te redirige a página de login
3. Usa la cuenta **Personal** de prueba (email y password del sandbox)
4. Completa el "pago" (es ficticio)
5. Verifica que tu backend recibe el webhook

**No se hacen cargos reales en modo sandbox**

---

## ❓ Solución de Problemas

### Error: "Account not verified"
- Ve a tu cuenta PayPal y completa la verificación
- Sube DNI o RUC según te pidan

### Error: "Plan ID not found"
- Verifica que el Plan ID esté correcto en tu `.env`
- Verifica que estés en el modo correcto (sandbox vs live)

### No recibo webhooks
- Verifica que la URL del webhook sea accesible públicamente
- Usa ngrok para desarrollo local
- Revisa PayPal Dashboard → Webhooks → Ver intentos fallidos

### Cliente no puede pagar
- Asegúrate de que PayPal esté configurado para aceptar pagos sin cuenta
- En tu configuración de cuenta, habilita "PayPal Guest Checkout"

### Webhook signature inválida
- Verifica que `PAYPAL_WEBHOOK_ID` esté correcto
- El webhook ID debe coincidir con el webhook en PayPal Developer

---

## 📚 Recursos Adicionales

- [PayPal Developer](https://developer.paypal.com)
- [Documentación de Subscriptions](https://developer.paypal.com/docs/subscriptions/)
- [Sandbox Testing](https://developer.paypal.com/tools/sandbox/)
- [Webhooks Reference](https://developer.paypal.com/api/rest/webhooks/)
- [Centro de Ayuda PayPal Perú](https://www.paypal.com/pe/smarthelp/home)

---

## 🇵🇪 Notas Específicas para Perú

### Documentos para verificación:
- **Persona Natural**: DNI
- **Empresa**: RUC + Ficha RUC + DNI del representante legal

### Bancos compatibles en Perú:
- ✅ BCP (Banco de Crédito del Perú)
- ✅ Interbank
- ✅ BBVA
- ✅ Scotiabank
- ✅ Banco de la Nación
- ✅ Banbif
- ✅ Y otros bancos locales

### Tiempo estimado de setup completo:
- **Crear cuenta**: 5-10 minutos
- **Verificar identidad**: 1-2 días
- **Vincular banco**: 2-3 días
- **Primer retiro**: 1-2 días después de vinculación

**Total: ~1 semana para estar 100% operativo**

---

¡Listo! Ahora puedes recibir pagos de todo el mundo desde Perú con PayPal. 🚀
