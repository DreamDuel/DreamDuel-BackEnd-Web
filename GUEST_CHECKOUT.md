# DreamDuel - Guest Checkout API

## Overview
DreamDuel is now a **guest-only** AI image generation service. No registration or login required.

**How it works:**
1. User enters site → Frontend generates/retrieves `session_id` (UUID)
2. User creates prompt → Click "Pay $1"
3. PayPal checkout → User pays
4. Backend validates payment → Generates AI image
5. Frontend retrieves image by `session_id`

---

## API Endpoints

### Base URL
```
Production: https://dreamduel-backend-web.onrender.com/api
Local: http://localhost:8000/api
```

---

## 1. Purchase Image (Guest Checkout)

**Endpoint:** `POST /payments/guest/purchase-image`

**Description:** Create a PayPal order for $1 image generation

**Request Body:**
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "returnUrl": "https://dreamduelfrontend.vercel.app/payment/success",
  "cancelUrl": "https://dreamduelfrontend.vercel.app/payment/cancel"
}
```

**Response:**
```json
{
  "orderId": "3KR26893PG6838734",
  "approvalUrl": "https://www.paypal.com/checkoutnow?token=3KR26893PG6838734",
  "status": "PENDING"
}
```

**Frontend Flow:**
```javascript
const sessionId = localStorage.getItem('guest_session_id') || crypto.randomUUID();
localStorage.setItem('guest_session_id', sessionId);

const response = await fetch('https://dreamduel-backend-web.onrender.com/api/payments/guest/purchase-image', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    sessionId,
    returnUrl: `${window.location.origin}/payment/success`,
    cancelUrl: `${window.location.origin}/payment/cancel`
  })
});

const { approvalUrl } = await response.json();
window.location.href = approvalUrl; // Redirect to PayPal
```

---

## 2. Confirm Payment

**Endpoint:** `POST /payments/guest/confirm-payment`

**Description:** Capture payment after user approves on PayPal

**Request Body:**
```json
{
  "orderId": "3KR26893PG6838734",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Payment successful! You can now generate your image.",
  "imagesAdded": 1,
  "totalImagesAvailable": 1
}
```

**Frontend Flow:**
```javascript
// On /payment/success page
const urlParams = new URLSearchParams(window.location.search);
const orderId = urlParams.get('token'); // PayPal returns 'token' param
const sessionId = localStorage.getItem('guest_session_id');

await fetch('https://dreamduel-backend-web.onrender.com/api/payments/guest/confirm-payment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ orderId, sessionId })
});
```

---

## 3. Check Image Status

**Endpoint:** `POST /payments/guest/image-status`

**Description:** Check if payment is complete and if image is ready

**Request Body:**
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (Payment Pending):**
```json
{
  "hasPaid": false,
  "imageReady": false,
  "imageUrl": null,
  "orderId": "3KR26893PG6838734",
  "status": "pending_payment"
}
```

**Response (Payment Complete, Image Ready):**
```json
{
  "hasPaid": true,
  "imageReady": true,
  "imageUrl": "https://res.cloudinary.com/.../image.png",
  "orderId": "3KR26893PG6838734",
  "status": "image_ready"
}
```

**Response (Payment Complete, Generating):**
```json
{
  "hasPaid": true,
  "imageReady": false,
  "imageUrl": null,
  "orderId": "3KR26893PG6838734",
  "status": "payment_completed"
}
```

**Frontend Polling:**
```javascript
// After confirming payment, poll for image status
const sessionId = localStorage.getItem('guest_session_id');

const pollInterval = setInterval(async () => {
  const response = await fetch('https://dreamduel-backend-web.onrender.com/api/payments/guest/image-status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId })
  });
  
  const data = await response.json();
  
  if (data.imageReady) {
    clearInterval(pollInterval);
    displayImage(data.imageUrl);
  }
}, 3000); // Poll every 3 seconds
```

---

## 4. Generate Image (Guest)

**Endpoint:** `POST /generate`

**Description:** Generate AI image (requires valid payment for session_id)

**Request Body:**
```json
{
  "prompt": "A majestic dragon flying over mountains",
  "style": "fantasy",
  "aspectRatio": "16:9",
  "negativePrompt": "blurry, low quality",
  "characterImages": [],
  "sessionId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "imageUrl": "https://res.cloudinary.com/.../generated-image.png",
  "prompt": "A majestic dragon flying over mountains",
  "generationId": "gen_abc123",
  "creditsUsed": 1
}
```

**Errors:**
- `402 Payment Required` - No completed payment found for session_id
- `409 Conflict` - Image already generated for this payment
- `500 Internal Server Error` - AI generation failed

**Frontend Flow:**
```javascript
const sessionId = localStorage.getItem('guest_session_id');

const response = await fetch('https://dreamduel-backend-web.onrender.com/api/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: userPrompt,
    style: selectedStyle,
    aspectRatio: '16:9',
    sessionId
  })
});

if (response.status === 402) {
  // Redirect to payment
  initiatePayment();
} else if (response.status === 409) {
  // Image already generated, fetch it via image-status
  fetchImageStatus();
} else {
  const { imageUrl } = await response.json();
  displayImage(imageUrl);
}
```

---

## 5. PayPal Webhook (Backend Only)

**Endpoint:** `POST /payments/webhook`

**Description:** Receives PayPal payment notifications (configured in PayPal dashboard)

**Events Handled:**
- `CHECKOUT.ORDER.APPROVED` - Auto-captures payment
- `PAYMENT.CAPTURE.COMPLETED` - Updates invoice status
- `PAYMENT.CAPTURE.REFUNDED` - Marks as refunded

**Configuration:**
```
Webhook URL: https://dreamduel-backend-web.onrender.com/api/payments/webhook
Webhook ID: 5DH83870TC209884F
```

---

## Complete Workflow Example

```javascript
// 1. Initialize session
let sessionId = localStorage.getItem('guest_session_id');
if (!sessionId) {
  sessionId = crypto.randomUUID();
  localStorage.setItem('guest_session_id', sessionId);
}

// 2. User enters prompt and clicks "Generate"
async function handleGenerate(prompt) {
  try {
    const response = await fetch('https://dreamduel-backend-web.onrender.com/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, sessionId })
    });
    
    if (response.status === 402) {
      // Need to pay first
      await initiatepayment();
    } else {
      const { imageUrl } = await response.json();
      showImage(imageUrl);
    }
  } catch (error) {
    console.error(error);
  }
}

// 3. Initiate payment
async function initiatePayment() {
  const response = await fetch('https://dreamduel-backend-web.onrender.com/api/payments/guest/purchase-image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      sessionId,
      returnUrl: `${window.location.origin}/payment/success`,
      cancelUrl: `${window.location.origin}`
    })
  });
  
  const { approvalUrl } = await response.json();
  window.location.href = approvalUrl;
}

// 4. On /payment/success page
async function handlePaymentSuccess() {
  const urlParams = new URLSearchParams(window.location.search);
  const orderId = urlParams.get('token');
  const sessionId = localStorage.getItem('guest_session_id');
  
  // Confirm payment
  await fetch('https://dreamduel-backend-web.onrender.com/api/payments/guest/confirm-payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ orderId, sessionId })
  });
  
  // Redirect back to generator
  window.location.href = '/generate';
}
```

---

## Database Schema

### Invoice Table
```sql
CREATE TABLE invoices (
  id UUID PRIMARY KEY,
  session_id VARCHAR(255) NOT NULL,  -- Guest session tracking
  user_id UUID NULL,                  -- NULL for guest checkout
  paypal_order_id VARCHAR(100),
  paypal_capture_id VARCHAR(100),
  amount FLOAT NOT NULL,              -- Always 1.00
  currency VARCHAR(10) DEFAULT 'USD',
  status VARCHAR(50),                 -- PENDING, COMPLETED, FAILED, REFUNDED
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX (session_id)
);
```

### Generated_Images Table
```sql
CREATE TABLE generated_images (
  id UUID PRIMARY KEY,
  session_id VARCHAR(255),            -- Guest session tracking
  user_id UUID NULL,                  -- NULL for guest
  prompt TEXT NOT NULL,
  image_url VARCHAR(500) NOT NULL,
  style VARCHAR(100),
  aspect_ratio VARCHAR(20),
  generation_id VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX (session_id)
);
```

---

## Environment Variables

```env
# PayPal
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_secret
PAYPAL_MODE=live  # or 'sandbox'
PAYPAL_WEBHOOK_ID=5DH83870TC209884F

# Frontend
FRONTEND_URL=https://dreamduelfrontend.vercel.app
CORS_ORIGINS=http://localhost:5173,https://dreamduelfrontend.vercel.app

# Database
DATABASE_URL=postgresql://user:pass@host/db

# AI Service
OPENAI_API_KEY=your_openai_key
CLOUDINARY_URL=cloudinary://...
```

---

## Testing

### Manual Test Flow

1. **Generate session ID:**
```javascript
const sessionId = crypto.randomUUID();
console.log(sessionId);
```

2. **Create order:**
```bash
curl -X POST https://dreamduel-backend-web.onrender.com/api/payments/guest/purchase-image \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"550e8400-e29b-41d4-a716-446655440000"}'
```

3. **Visit approval URL in browser and pay**

4. **Confirm payment:**
```bash
curl -X POST https://dreamduel-backend-web.onrender.com/api/payments/guest/confirm-payment \
  -H "Content-Type: application/json" \
  -d '{"orderId":"3KR26893PG6838734","sessionId":"550e8400-e29b-41d4-a716-446655440000"}'
```

5. **Generate image:**
```bash
curl -X POST https://dreamduel-backend-web.onrender.com/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"dragon","sessionId":"550e8400-e29b-41d4-a716-446655440000"}'
```

---

## Important Notes

1. **Session Persistence:** `session_id` is stored in localStorage - if user clears browser data, they lose access to their paid image.

2. **Payment Window:** Payments are valid for 24 hours. After that, user must pay again.

3. **One Image Per Payment:** Each $1 payment allows generating exactly ONE image. Trying to generate again returns 409 Conflict.

4. **Image Storage:** Images are stored in Cloudinary with permanent URLs. Even if session is lost, URL works if user saved it.

5. **No Authentication:** All endpoints are public - no JWT tokens, no login required.

6. **Rate Limiting:** PayPal has rate limits. Production should implement additional rate limiting per session_id.

---

## Deployment Checklist

- [ ] Run database migration 004_guest_checkout.py
- [ ] Update CORS_ORIGINS in Render environment variables
- [ ] Configure PayPal webhook URL in PayPal dashboard
- [ ] Test complete payment flow on staging
- [ ] Verify Cloudinary image storage works
- [ ] Monitor Render logs for errors
- [ ] Test with $1 real PayPal payment
- [ ] Document frontend integration for team

---

## Support

For issues or questions:
- Check Render logs for backend errors
- Verify session_id is persisting in localStorage
- Confirm PayPal webhook is receiving events
- Test with PayPal sandbox before production
