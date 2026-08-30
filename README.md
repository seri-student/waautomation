# AI Restaurant WhatsApp Ordering SaaS

A multi-tenant, AI-powered restaurant ordering system. Customers chat on WhatsApp (or the built-in Simulator); an AI assistant takes the order; restaurant owners manage everything from a live dashboard.

- **Backend:** FastAPI + MongoDB (motor)
- **Frontend:** React + Tailwind + shadcn/ui
- **AI:** Google Gemini via the Emergent Universal Key (`emergentintegrations`)
- **Real-time:** Server-Sent Events (SSE)
- **WhatsApp:** provider abstraction — **Simulator**, **Evolution API**, **Meta Cloud API** (per-restaurant)

---

## 1. Requirements
- Python 3.11+, Node 18+, Yarn, MongoDB
- (Optional, for real WhatsApp) a self-hosted Evolution API server OR a Meta WhatsApp Business account

## 2. Environment Variables (`/app/backend/.env`)
```
MONGO_URL=...            # provided by platform
DB_NAME=...              # provided by platform
JWT_SECRET=...           # random 64-char hex
ADMIN_EMAIL=owner@pizzapalace.pk
ADMIN_PASSWORD=palace123
EMERGENT_LLM_KEY=...     # Universal Key for Gemini
AI_PROVIDER=gemini
AI_MODEL=gemini-3-flash-preview
WHATSAPP_PROVIDER=simulator          # global default; per-restaurant setting overrides
EVOLUTION_API_URL=                   # your Evolution host (optional)
EVOLUTION_API_KEY=
META_GRAPH_API_URL=https://graph.facebook.com/v21.0
META_ACCESS_TOKEN=
META_PHONE_NUMBER_ID=
META_WABA_ID=
META_VERIFY_TOKEN=pizzapalace_verify_token
```
The frontend uses only `REACT_APP_BACKEND_URL`. No secrets are ever exposed to the browser.

## 3. Running Locally
```
# backend
cd backend && pip install -r requirements.txt && uvicorn server:app --host 0.0.0.0 --port 8001
# frontend
cd frontend && yarn install && yarn start
```
On this platform both run under supervisor: `sudo supervisorctl restart backend frontend`.

## 4. Demo Data
On first boot a demo restaurant **Pizza Palace** is seeded with a full PKR menu, an owner login, and sample orders/customers.
- Login: **owner@pizzapalace.pk** / **palace123**

## 5. Testing the Order Flow (no WhatsApp needed)
1. Log in → **WhatsApp** page → **Test Simulator** tab.
2. Chat as a customer: `menu dikhao` → `1 zinger burger aur fries` → `haan coke` → `delivery` → give an address → `yes`.
3. The order appears live on the **Orders** board.
4. Advance status (Confirmed → Preparing → Out for Delivery → Delivered); each step posts a WhatsApp update back into the chat.

## 6. Provider Switching
On the **WhatsApp** page pick a provider (Simulator / Evolution / Meta). The choice is stored per-restaurant, so different restaurants can use different providers simultaneously. The ordering engine is provider-agnostic — switching transport requires **no code changes**.

## 7. Evolution API Setup (self-hosted, Docker)
Evolution API is an unofficial gateway; run it yourself:
```
docker run -d --name evolution -p 8080:8080 \
  -e AUTHENTICATION_API_KEY=change-me \
  -e DATABASE_ENABLED=true -e DATABASE_PROVIDER=postgresql \
  -e DATABASE_CONNECTION_URI=postgresql://user:pass@host:5432/evolution \
  -e CACHE_REDIS_ENABLED=true -e CACHE_REDIS_URI=redis://host:6379 \
  atendai/evolution-api:latest
```
Then in the dashboard → WhatsApp → Evolution API, paste the URL (`http://host:8080`) and API key, click **Connect**, and scan the QR from **WhatsApp → Linked Devices**. Set the Evolution webhook (shown on the page) to receive incoming messages.

## 8. Meta WhatsApp Cloud API Setup
1. Create a Meta app + WhatsApp product, get **Phone Number ID**, **WABA ID**, **Access Token**.
2. In the dashboard → WhatsApp → Meta, paste them + a **Verify Token**, click **Save & Verify**.
3. In Meta → WhatsApp → Configuration, set the webhook to the **Webhook URL** shown on the page using your Verify Token, and subscribe to `messages`.

## 9. Architecture (provider abstraction)
```
Business logic ──► WhatsAppService ──► get_whatsapp_provider(restaurant_id)
                                          ├─ SimulatorProvider
                                          ├─ EvolutionApiProvider ─► Evolution API
                                          └─ MetaCloudProvider    ─► Meta Cloud API
```
Incoming webhooks are normalized into a common `IncomingMessage` and passed to the shared conversation/AI engine. Pricing, cart and order creation are always computed deterministically in the backend — the AI never invents menu data or totals.

## 10. Production Notes
See `WHATSAPP_DISCLAIMER.md`. Prefer the official Meta WhatsApp Business Platform for production.
