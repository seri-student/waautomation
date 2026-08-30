# PRD — AI Restaurant WhatsApp Ordering SaaS

## Original Problem Statement
Build a COMPLETE WORKING MVP of a multi-tenant, AI-powered restaurant ordering system for Pakistan. Two sides: (1) a customer-facing AI WhatsApp ordering assistant (English/Urdu/Roman Urdu) that shows the menu, takes natural-language orders, builds a cart, calculates the bill deterministically, upsells one add-on, collects delivery/pickup + details, confirms, and creates an order with a number + ETA; (2) a restaurant-owner web dashboard. WhatsApp via a provider abstraction (Evolution API + Meta Cloud API) selectable per-restaurant. AI via Gemini. Real-time order board. Human handoff. Basic analytics.

## Architecture (as built)
- **Backend:** FastAPI + MongoDB (motor). Modular: `services/` (ai, order, conversation, notification), `whatsapp/` (base interface + Simulator/Evolution/Meta providers + factory + WhatsAppService), `routers/` (auth, restaurant, menu, orders, customers, analytics, whatsapp, conversations, simulator, webhooks, stream).
- **Frontend:** React + Tailwind + shadcn/ui. Pages: Login, Dashboard, Orders, OrderDetail, Customers, CustomerDetail, Menu, WhatsApp (Connection/Simulator/Conversations tabs), Settings, AISettings.
- **AI:** Gemini via Emergent Universal Key (`emergentintegrations`), default `gemini-3-flash-preview`, with controlled tool-calling (add_to_cart, calculate_cart, create_order, set_order_type, set_customer_details, get_order_status, request_human_support). Backend computes all money; AI never invents data.
- **Real-time:** SSE (`/api/stream?token=`) + react-query polling fallback; new-order chime + toast.
- **Auth:** JWT Bearer (bcrypt), multi-tenant via `restaurant_id` on every collection; all reads use `clean()`/NO_ID (no ObjectId leaks).

## User Personas
- **Restaurant owner/staff (primary):** non-technical; manages menu, watches live orders, updates status, takes over chats.
- **Customer (secondary):** orders via WhatsApp/Simulator in their own language.

## Core Requirements (static)
- Multi-tenant isolation; per-restaurant WhatsApp provider; deterministic pricing; stateful AI conversation; live order board; status→customer notifications; human handoff; PKR default.

## Implemented (2026-06)
- Full AI ordering flow end-to-end via Simulator (verified): menu → cart → upsell → delivery/pickup → details → summary → confirm → order created with number + ETA, in Roman Urdu.
- WhatsApp provider abstraction with Simulator (live), Evolution API and Meta Cloud API (ready-to-plug; activate on paste of real creds) + normalized webhooks.
- Dashboard home KPIs, live kanban Orders board (SSE), order detail + status stepper + notifications, Menu CRUD, Customers list/detail, Settings, AI Settings, Conversations + human handoff.
- Demo restaurant "Pizza Palace" seeded (PKR menu w/ images, owner login, 4 sample orders/customers).
- Duplicate-order idempotency guard (15-min identical-order dedupe) + prompt hardening.
- Docs: README.md, WHATSAPP_DISCLAIMER.md, auth_testing.md.
- Tests: 40/40 backend pytest passing; frontend E2E passing.

## Backlog (P1/P2 — architecture left ready)
- P1: Evolution/Meta live connection validated against a real server/number; real-time via WebSockets if SSE proves lossy at scale.
- P2: Online payments (JazzCash/Easypaisa/Stripe), loyalty/coupons, broadcasts, QR menu, multi-branch, inventory, POS, rider management, voice ordering, Ollama local AI.

## Known Notes
- Live WhatsApp requires user-provided Evolution host or Meta credentials (none yet) — Simulator covers full testing today.
