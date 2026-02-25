# Migración de Stripe a PayPal - COMPLETADO ✅

## Resumen de Cambios

El backend de DreamDuel ha sido actualizado para usar **PayPal** exclusivamente, ya que PayPal está disponible en Perú y Stripe no.

---

## 📦 Archivos Modificados

### 1. Configuración
- ✅ `app/core/config.py` - Configuraciones de PayPal (eliminadas variables de Stripe)
- ✅ `.env.example` - Template actualizado con variables de PayPal
- ✅ `requirements.txt` - Agregado `paypalrestsdk==1.13.1` (eliminado stripe)

### 2. Servicios
- ✅ `app/infrastructure/external_services/paypal_service.py` - **NUEVO** servicio de PayPal
- ❌ `app/infrastructure/external_services/stripe_service.py` - **ELIMINADO**
- ✅ `app/core/exceptions.py` - `PaymentException` (genérica para PayPal)

### 3. Rutas y Schemas
- ✅ `app/api/v1/routes/payments.py` - Reescrito para usar PayPal exclusivamente
- ✅ `app/api/v1/schemas/payment.py` - Actualizado solo para PayPal
- ❌ `app/api/v1/routes/payments_stripe_backup.py` - **ELIMINADO**

### 4. Modelos de Base de Datos
- ✅ `app/infrastructure/database/models.py` - Modelos actualizados solo para PayPal:
  - `Subscription` - Campo `paypal_subscription_id`
  - `Invoice` - Campo `paypal_sale_id`

### 5. Documentación
- ✅ `PAYPAL_SETUP.md` - **NUEVA** guía completa de configuración de PayPal
- ❌ `STRIPE_SETUP.md` - **ELIMINADO**

---

## 🚀 Cambios para Migración de Base de Datos

### IMPORTANTE: Actualizar Base de Datos

Los modelos `Subscription` e `Invoice` fueron actualizados. Necesitas crear una migración de Alembic:

```bash
# 1. Genera la migración automática
alembic revision --autogenerate -m "Add PayPal support to subscriptions and invoices"

# 2. Revisa el archivo de migración generado en migrations/versions/

# 3. Aplica la migración
alembic upgrade head
```

**La migración hará:**
- Agregar columna `paypal_subscription_id` a tabla `subscriptions`
- Agregar columna `paypal_sale_id` a tabla `invoices`
- Agregar columna `currency` a tabla `invoices`
- Hacer columnas de Stripe opcionales (nullable=True)
- Cambiar tipo de columna `status` de ENUM a VARCHAR(50)
- Cambiar tipo de columna `amount` en invoices de Integer a Float

---

## 🔧 Configuración Requerida

### 1. Variables de Entorno (.env)

Actualiza tu archivo `.env` con:

```bash
# PayPal Payment Integration
PAYPAL_MODE=sandbox  # o 'live' para producción
PAYPAL_CLIENT_ID=tu_client_id
PAYPAL_CLIENT_SECRET=tu_secret
PAYPAL_WEBHOOK_ID=tu_webhook_id
PAYPAL_MONTHLY_PLAN_ID=P-XXXXXXXXXXXXXXXXX
PAYPAL_YEARLY_PLAN_ID=P-YYYYYYYYYYYYYYY

# Las variables de Stripe ahora son opcionales
```

### 2. Instalar Dependencias

```bash
pip install paypalrestsdk==1.13.1
```

O reinstalar todo:

```bash
pip install -r requirements.txt
```

---

## 📋 Pasos para Configurar PayPal

Sigue la guía completa en **[PAYPAL_SETUP.md](PAYPAL_SETUP.md)**

**Resumen rápido:**

1. **Crear cuenta PayPal Business**: https://www.paypal.com/pe/business
2. **Obtener credenciales**: https://developer.paypal.com → My Apps & Credentials
3. **Crear planes de suscripción**: En dashboard de PayPal o programáticamente
4. **Configurar webhook**: Para recibir notificaciones de eventos
5. **Actualizar .env**: Con Client ID, Secret y Plan IDs

---

## 🔄 Flujo de Suscripción con PayPal

### Diferencias con Stripe:

**Stripe (anterior):**
1. Frontend crea suscripción
2. Backend devuelve `clientSecret`
3. Frontend confirma pago con Stripe Elements
4. Suscripción activada

**PayPal (nuevo):**
1. Frontend crea suscripción
2. Backend devuelve `approvalUrl` 
3. Frontend **redirige** al usuario a PayPal
4. Usuario aprueba en PayPal (ingresa tarjeta o usa cuenta)
5. PayPal redirige de vuelta a `returnUrl`
6. Frontend llama a `/subscription/confirm` con subscription_id
7. Suscripción activada

### Endpoints Principales:

```http
# 1. Obtener planes
GET /api/v1/payments/plans

# 2. Iniciar suscripción
POST /api/v1/payments/subscribe
Body: { "planId": "monthly", "returnUrl": "...", "cancelUrl": "..." }
Response: { "subscriptionId": "I-XXX", "approvalUrl": "https://paypal.com/..." }

# 3. Confirmar suscripción (después de aprobación en PayPal)
POST /api/v1/payments/subscription/confirm
Body: { "subscriptionId": "I-XXX" }

# 4. Ver estado
GET /api/v1/payments/subscription/status

# 5. Cancelar
POST /api/v1/payments/subscription/cancel
Body: { "reason": "Customer request" }

# 6. Webhook (automático)
POST /api/v1/payments/webhook
```

---

## 💡 Ventajas de PayPal para Perú

1. ✅ **Disponible en Perú** (Stripe no lo está)
2. ✅ **Sin costos iniciales** - Gratis crear cuenta
3. ✅ **Clientes pagan sin cuenta PayPal** - Solo con tarjeta
4. ✅ **Retiros gratis a bancos peruanos** - BCP, Interbank, BBVA, etc.
5. ✅ **Comisiones competitivas**:
   - Local (Perú): 3.4% + $0.30 USD
   - Internacional: 5.4% + $0.30 USD

---

## 🧪 Testing

### Modo Sandbox:

```bash
PAYPAL_MODE=sandbox
```

**No se hacen cargos reales**. PayPal crea cuentas de prueba automáticamente.

### Tarjetas de Prueba:

PayPal Sandbox acepta cualquier tarjeta válida (no necesita números específicos como Stripe).

---

## 🔐 Webhook Verification

El webhook en `/api/v1/payments/webhook` verifica la firma de PayPal automáticamente.

**Eventos manejados:**
- `BILLING.SUBSCRIPTION.ACTIVATED` - Suscripción activada
- `BILLING.SUBSCRIPTION.CANCELLED` - Suscripción cancelada
- `BILLING.SUBSCRIPTION.SUSPENDED` - Suscripción suspendida (pago fallido)
- `PAYMENT.SALE.COMPLETED` - Pago completado (crea invoice)

---

## 🌐 Integración con Frontend

### React Example:

```javascript
// 1. Obtener planes
const plans = await fetch('/api/v1/payments/plans').then(r => r.json());

// 2. Crear suscripción
const response = await fetch('/api/v1/payments/subscribe', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    planId: 'monthly',
    returnUrl: 'https://tu-app.com/payment/success',
    cancelUrl: 'https://tu-app.com/payment/cancel'
  })
});

const { approvalUrl, subscriptionId } = await response.json();

// 3. Redirigir a PayPal
window.location.href = approvalUrl;

// 4. En /payment/success, confirmar suscripción
const urlParams = new URLSearchParams(window.location.search);
const subscriptionId = urlParams.get('subscription_id');

await fetch('/api/v1/payments/subscription/confirm', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ subscriptionId })
});
```

**Más ejemplos en [PAYPAL_SETUP.md](PAYPAL_SETUP.md)**

---

## 📊 Comparación: Stripe vs PayPal

| Característica | Stripe | PayPal |
|---------------|--------|--------|
| **Disponible en Perú** | ❌ No | ✅ Sí |
| **Costos iniciales** | $0 | $0 |
| **Comisión internacional** | 2.9% + $0.30 | 5.4% + $0.30 |
| **Pago sin cuenta** | ✅ Sí | ✅ Sí |
| **Retiros a banco peruano** | ❌ No | ✅ Sí (gratis) |
| **Modo sandbox** | ✅ Sí | ✅ Sí |
| **Webhooks** | ✅ Sí | ✅ Sí |
| **Documentación** | Excelente | Buena |
| **Integración frontend** | Stripe Elements | Redirect flow |

---

## ⚠️ Notas Importantes

1. **Migración de base de datos requerida** - Ejecuta `alembic upgrade head`
2. **Los usuarios existentes con Stripe** - Necesitarán renovar su suscripción con PayPal
3. **Testing primero** - Usa modo sandbox antes de ir a producción
4. **Webhook setup** - Esencial para que las suscripciones funcionen correctamente

---

## 🆘 Soporte

- **Documentación completa**: [PAYPAL_SETUP.md](PAYPAL_SETUP.md)
- **PayPal Developer**: https://developer.paypal.com
- **Dashboard PayPal**: https://www.paypal.com/pe

---

## ✅ Checklist Final

Antes de usar en producción:

- [ ] Ejecutar migración de Alembic
- [ ] Crear cuenta PayPal Business
- [ ] Verificar cuenta con DNI/RUC
- [ ] Obtener credenciales de API (sandbox primero)
- [ ] Crear productos y planes en PayPal
- [ ] Configurar variables en `.env`
- [ ] Configurar webhook en PayPal Developer
- [ ] Probar flujo completo en sandbox
- [ ] Cambiar a modo `live` cuando esté listo
- [ ] Vincular cuenta bancaria para retiros

---

**¡PayPal está listo para usar! 🚀**
