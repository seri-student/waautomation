# AI Restaurant WhatsApp Ordering SaaS — MVP Plan

## What this is
A multi-tenant web product with two sides:
1. **Customer side** — an AI WhatsApp ordering assistant that chats, shows the menu, builds a cart, prices the order, upsells once, collects details, confirms, and creates the order.
2. **Restaurant-owner side** — a web dashboard to watch orders in real time, manage the menu, view customers, take over conversations, and configure WhatsApp + AI.

Each restaurant is fully isolated — its own menu, orders, customers, conversations, settings, and WhatsApp/AI configuration. Nothing leaks between restaurants.

## The honest WhatsApp situation (please read)
A **live** WhatsApp connection (scanning a real QR, receiving real messages from a real phone) needs an external service that this environment cannot host or keep running for you:
- **Evolution API** must run on your own machine or a VPS (it needs its own database + Redis and a stable server). I **cannot** stand up and keep a live Evolution server + real WhatsApp number running for you from here.
- **Meta Cloud API** needs a Meta Business account, an approved phone number, and access tokens that only you can create.

Because you have no credentials yet, here is what you get **working today**, and what is **ready to plug in later**:

| Capability | Status now |
|---|---|
| Built-in **WhatsApp Simulator** (a test chat in the dashboard) | ✅ Fully working — drives the exact same AI ordering engine end to end |
| **Evolution API** provider (create instance, QR, connect, send/receive, webhook) | ✅ Built & ready — works the moment you paste a live Evolution URL + key |
| **Meta Cloud API** provider (webhook verify, incoming, outgoing, status) | ✅ Built & ready — works the moment you paste live Meta credentials |
| A step-by-step **guide to self-host Evolution API** (Docker) and connect it | ✅ Included in the README, with exact commands |

So you will be able to test the **entire order flow today** through the Simulator, and switch to a real WhatsApp number later by pasting credentials — with **no code changes**. The provider is stored per-restaurant, so different restaurants can use different providers at the same time.

**Decision point:** Is the Simulator-for-now + ready-to-plug providers + self-host guide approach acceptable? Or do you want to pause the build until you have live Evolution/Meta credentials to paste?

## What the AI assistant will do
- Chat naturally in **English, Urdu, and Roman Urdu**, auto-detecting and replying in the customer's language.
- Behave like a friendly Pakistani restaurant receptionist — short, helpful messages.
- Only ever use real menu/prices/fees/hours from the database (never invents items or prices).
- All money math (subtotal, delivery fee, total) is computed by the backend, not the AI.
- Suggest **one** relevant add-on at a time, and stop if the customer declines.
- Walk through: greet → menu → add items → cart → delivery or pickup → collect name/phone (+address if delivery) → show full summary with estimated time → confirm → create order.
- Hand off to a human when asked or when unsure.

## Dashboard pages
- **Login / Logout** (email + password).
- **Dashboard home** — today's orders, today's sales, pending/completed counts, average order value, live WhatsApp status + active provider, recent orders.
- **Orders** — live list that updates in **real time** (no manual refresh); order detail with full breakdown; staff can move status through New → Confirmed → Preparing → Ready → Out for Delivery → Delivered / Cancelled. Each status change sends a WhatsApp update to the customer through whichever provider is active.
- **Customers** — list + profile (name, phone, total orders, total spent, last order, order history, recent conversation).
- **Menu** — add/edit/delete categories and items; set price, availability, image, and recommended add-on/upsell.
- **WhatsApp** — pick provider per restaurant (Simulator / Evolution / Meta); for Evolution: connect, QR code, connected number, last-connected, status, reconnect/disconnect, connection logs; for Meta: phone number ID, WABA ID, tokens (masked), webhook URL + verification status. Also opens the **Simulator** test chat.
- **Restaurant Settings** — name, address, phone, opening hours, delivery fee, minimum order, prep time, delivery time, currency (default **PKR**), AI greeting.
- **AI Settings** — provider (Gemini now; Ollama shown as a future option), personality, language behavior, upselling on/off, max upsell attempts, human-handoff on/off.
- **Human handoff** — "Take Over Conversation" pauses the AI so staff reply manually; "Resume AI" hands control back. Manual replies go out through the active provider.
- **Basic analytics** — today / this week / this month sales, average order value, top 5 items.

## Demo data (ready on first login)
- A demo restaurant **"Pizza Palace"** with categories (Burgers, Pizza, Fries, Drinks, Desserts) and realistic PKR prices (e.g. Zinger Burger PKR 650, Fries PKR 250, Coke PKR 120, Large Pizza PKR 1,499, Brownie PKR 350), plus recommended add-ons.
- A demo owner login and a few sample customers/orders so the dashboard looks alive immediately.
- The exact demo login credentials will be shown to you when the build is done.

## Decisions already made (assumptions — tell me if any are wrong)
1. **AI:** Gemini via the Emergent Universal Key (no key needed from you). I'll use a fast Gemini model by default, changeable in AI Settings.
2. **Real-time:** the Orders board and dashboard update live without refresh, including a visual new-order notification.
3. **Auth:** email + password owner login (secure, hashed). Sign-up of new restaurants is included so the product is genuinely multi-tenant, but you'll mainly use the demo account.
4. **Currency default PKR**, Pakistan-oriented copy and examples.
5. **Not in this MVP** (architecture left ready for them): online payments (JazzCash/Easypaisa/Stripe), loyalty/coupons, broadcasts/marketing, QR menu, multi-branch, inventory, POS, delivery-rider management, voice ordering, Ollama local AI.

## What "done" means
You can log in, open the Simulator, chat like a customer ("menu dikhao", "1 zinger burger aur fries", "haan coke", "delivery", give an address, "yes"), watch the order appear live on the dashboard, move it through every status, and see each status update posted back into the conversation — all end to end. Evolution and Meta will do the same the moment real credentials are added.
