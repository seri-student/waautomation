"""AI ordering assistant powered by Gemini (Emergent Universal Key).

The LLM handles natural-language understanding and phrasing only. Every
business action goes through controlled tools that the backend validates
and executes deterministically. The AI never invents menu data or totals.
"""
import os
import json
import logging
from datetime import datetime, timezone, timedelta

from emergentintegrations.llm.chat import LlmChat, UserMessage

from database import db, NO_ID
from services import order_service

logger = logging.getLogger(__name__)

FALLBACK = ("Sorry, I'm having a little trouble right now. Let me connect you with our team — "
            "please hold on a moment. / Maazrat, thodi dikkat aa rahi hai. Main aap ko team se connect karta hoon.")

TOOLS = [
    {"type": "function", "function": {
        "name": "add_to_cart",
        "description": "Add a menu item to the customer's cart by its name.",
        "parameters": {"type": "object", "properties": {
            "item_name": {"type": "string", "description": "Menu item name as the customer referred to it"},
            "quantity": {"type": "integer", "description": "Quantity, default 1"}},
            "required": ["item_name"]}}},
    {"type": "function", "function": {
        "name": "remove_from_cart",
        "description": "Remove an item from the cart by name.",
        "parameters": {"type": "object", "properties": {
            "item_name": {"type": "string"}}, "required": ["item_name"]}}},
    {"type": "function", "function": {
        "name": "update_cart_quantity",
        "description": "Set the quantity of an item already in the cart.",
        "parameters": {"type": "object", "properties": {
            "item_name": {"type": "string"}, "quantity": {"type": "integer"}},
            "required": ["item_name", "quantity"]}}},
    {"type": "function", "function": {
        "name": "calculate_cart",
        "description": "Get the current cart with backend-calculated subtotal, delivery fee and total.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "set_order_type",
        "description": "Record whether the order is delivery or pickup.",
        "parameters": {"type": "object", "properties": {
            "order_type": {"type": "string", "enum": ["delivery", "pickup"]}}, "required": ["order_type"]}}},
    {"type": "function", "function": {
        "name": "set_customer_details",
        "description": "Save the customer's name, and address (address only for delivery).",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string"}, "address": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "create_order",
        "description": "Place the final order. Only call AFTER the customer explicitly confirms the full summary.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "get_order_status",
        "description": "Look up the status of an existing order by its number.",
        "parameters": {"type": "object", "properties": {
            "order_number": {"type": "integer"}}, "required": ["order_number"]}}},
    {"type": "function", "function": {
        "name": "request_human_support",
        "description": "Hand the conversation to a human staff member (complaint, unusual request, or uncertainty).",
        "parameters": {"type": "object", "properties": {"reason": {"type": "string"}}}}},
]


def _menu_text(categories: list, items: list) -> str:
    lines = []
    by_cat = {}
    for it in items:
        by_cat.setdefault(it["category_id"], []).append(it)
    for cat in categories:
        lines.append(f"\n### {cat['name']}")
        for it in by_cat.get(cat["id"], []):
            status = "" if it.get("available", True) else " (UNAVAILABLE)"
            addon = ""
            lines.append(f"- {it['name']} — {it['price']:.0f}{status}"
                         + (f" | {it.get('description')}" if it.get("description") else "") + addon)
    return "\n".join(lines) if lines else "(No menu items configured)"


def _cart_text(cart: list) -> str:
    if not cart:
        return "(empty)"
    return ", ".join([f"{c['qty']}x {c['name']}" for c in cart])


def _build_system_prompt(restaurant, ai_settings, conversation, customer, categories, items, recent_messages):
    cur = restaurant.get("currency", "PKR")
    hours = restaurant.get("opening_hours", "")
    history = "\n".join([f"{'Customer' if m['direction'] == 'in' else 'You'}: {m['text']}"
                         for m in recent_messages[-8:]])
    personality = ai_settings.get("personality") or "friendly Pakistani restaurant receptionist"
    upsell_line = ("You MAY suggest ONE relevant complementary item (a configured add-on) at a time. "
                   "Never upsell more than once after a decline.") if ai_settings.get("upsell_enabled", True) \
        else "Do NOT upsell."
    return f"""You are an AI restaurant ordering assistant for "{restaurant['name']}".
Act like a {personality}. Keep replies SHORT, warm and conversational.

LANGUAGE: Detect the customer's language and reply in the SAME one.
- English message -> reply in English
- Urdu script -> reply in Urdu script
- Roman Urdu (Urdu written in English letters) -> reply in Roman Urdu

STRICT RULES:
- Only use the menu, prices, fees and info below. NEVER invent items, prices, discounts or policies.
- CRITICAL: The moment a customer names any menu item they want, immediately call add_to_cart for it. NEVER say an item was added, or show it in a summary, unless you actually called the tool for it in this conversation.
- NEVER calculate totals yourself. Use the calculate_cart / create_order tools; the backend computes money.
- Add/modify items ONLY via tools (add_to_cart, remove_from_cart, update_cart_quantity).
- CONFIRMATION: once order type is set (and address for delivery) and the customer's name is known, if the customer clearly affirms (yes / confirm / haan / ok kardo / place order), call create_order right away — do NOT ask further clarifying questions.
- NO DUPLICATES: if an order was already placed this session (see "Last placed order" below), do NOT re-add those items or call create_order again. Simply tell the customer their order #N is already placed and share its status, unless they explicitly ask to start a brand-new/additional order.
- {upsell_line}
- Ask only what's needed. For delivery collect name + address; for pickup collect name. Phone is already known.
- Before placing the order show a clear summary (items, qty, subtotal, delivery fee, total, type, address, ETA) and ask for confirmation.
- Only call create_order AFTER the customer clearly confirms (e.g. "yes", "confirm", "place order", "haan", "ok kardo").
- If the customer has a complaint, wants a human, or you're unsure, call request_human_support.

RESTAURANT INFO:
- Currency: {cur}
- Delivery fee: {restaurant.get('delivery_fee', 0):.0f} {cur} (delivery only)
- Minimum order: {restaurant.get('min_order', 0):.0f} {cur}
- Preparation: {restaurant.get('prep_time_min', 20)}-{restaurant.get('prep_time_max', 30)} min
- Delivery: {restaurant.get('delivery_time_min', 15)}-{restaurant.get('delivery_time_max', 20)} min
- Opening hours: {hours}
- Address: {restaurant.get('address', '')}, {restaurant.get('city', '')}

MENU:
{_menu_text(categories, items)}

CURRENT ORDER CONTEXT:
- Cart: {_cart_text(conversation.get('cart', []))}
- Order type: {conversation.get('order_type') or 'not set'}
- Customer name: {conversation.get('customer_name') or customer.get('name') or 'unknown'}
- Customer phone: {customer.get('phone')}
- Delivery address: {conversation.get('address') or 'not set'}
- Last placed order: {('#' + str(conversation.get('last_order_number')) + ' (already placed — do NOT reorder)') if conversation.get('last_order_number') else 'none this session'}

RECENT CONVERSATION:
{history or '(this is the first message)'}
"""


async def _dispatch(name: str, args: dict, restaurant: dict, items: list, conversation_id: str, customer: dict):
    conv = await db.conversations.find_one({"id": conversation_id}, NO_ID)
    cart = conv.get("cart", [])

    def totals():
        return order_service.compute_totals(restaurant, cart, conv.get("order_type"))

    if name == "add_to_cart":
        it = order_service.match_menu_item(items, args.get("item_name", ""))
        if not it:
            return {"error": "item_not_found", "available_items": [i["name"] for i in items if i.get("available", True)]}
        if not it.get("available", True):
            return {"error": "item_unavailable", "item": it["name"]}
        qty = max(1, int(args.get("quantity", 1) or 1))
        for c in cart:
            if c["item_id"] == it["id"]:
                c["qty"] += qty
                break
        else:
            cart.append({"item_id": it["id"], "name": it["name"], "unit_price": float(it["price"]), "qty": qty})
        await db.conversations.update_one({"id": conversation_id}, {"$set": {"cart": cart, "state": "SELECTING_ITEMS"}})
        addons = [i["name"] for i in items if i["id"] in (it.get("addon_item_ids") or []) and i.get("available", True)]
        return {"ok": True, "cart": cart, "totals": totals(), "suggested_addons": addons[:1]}

    if name == "remove_from_cart":
        it = order_service.match_menu_item(items, args.get("item_name", ""))
        cart = [c for c in cart if not (it and c["item_id"] == it["id"])]
        await db.conversations.update_one({"id": conversation_id}, {"$set": {"cart": cart}})
        return {"ok": True, "cart": cart, "totals": totals()}

    if name == "update_cart_quantity":
        it = order_service.match_menu_item(items, args.get("item_name", ""))
        qty = int(args.get("quantity", 1))
        for c in cart:
            if it and c["item_id"] == it["id"]:
                if qty <= 0:
                    cart = [x for x in cart if x["item_id"] != it["id"]]
                else:
                    c["qty"] = qty
                break
        await db.conversations.update_one({"id": conversation_id}, {"$set": {"cart": cart}})
        return {"ok": True, "cart": cart, "totals": totals()}

    if name == "calculate_cart":
        return {"cart": cart, "totals": totals()}

    if name == "set_order_type":
        ot = args.get("order_type")
        await db.conversations.update_one({"id": conversation_id},
                                          {"$set": {"order_type": ot, "state": "COLLECTING_ORDER_TYPE"}})
        conv["order_type"] = ot
        return {"ok": True, "order_type": ot, "totals": totals()}

    if name == "set_customer_details":
        upd = {}
        if args.get("name"):
            upd["customer_name"] = args["name"]
        if args.get("address"):
            upd["address"] = args["address"]
        if upd:
            await db.conversations.update_one({"id": conversation_id}, {"$set": upd})
            if args.get("name"):
                await db.customers.update_one({"id": customer["id"]}, {"$set": {"name": args["name"]}})
        return {"ok": True, **upd}

    if name == "create_order":
        if not cart:
            return {"error": "empty_cart"}
        if not conv.get("order_type"):
            return {"error": "order_type_missing", "message": "Ask delivery or pickup first."}
        if conv.get("order_type") == "delivery" and not conv.get("address"):
            return {"error": "address_missing"}
        if not (conv.get("customer_name") or customer.get("name")):
            return {"error": "name_missing"}
        t = totals()
        if t["subtotal"] < float(restaurant.get("min_order", 0)):
            return {"error": "below_minimum", "minimum": restaurant.get("min_order"), "subtotal": t["subtotal"]}
        # Idempotency: block a duplicate identical order placed in the last 15 minutes
        sig = sorted([(c["item_id"], int(c["qty"])) for c in cart])
        now = datetime.now(timezone.utc)
        recent = await db.orders.find(
            {"restaurant_id": restaurant["id"], "customer_id": customer["id"]}, NO_ID
        ).sort("created_at", -1).to_list(5)
        for o in recent:
            try:
                created = datetime.fromisoformat(o["created_at"])
            except Exception:  # noqa
                continue
            if (now - created) <= timedelta(minutes=15):
                osig = sorted([(i.get("item_id"), int(i.get("qty", 0))) for i in o.get("items", [])])
                if osig == sig and o.get("status") != "Cancelled":
                    await db.conversations.update_one(
                        {"id": conversation_id},
                        {"$set": {"cart": [], "state": "ORDER_PLACED",
                                  "last_order_id": o["id"], "last_order_number": o["order_number"]}})
                    return {"error": "duplicate_order", "order_number": o["order_number"],
                            "message": "This exact order was already placed."}
        order = await order_service.create_order(restaurant=restaurant, conversation=conv, customer=customer)
        await db.conversations.update_one({"id": conversation_id},
                                          {"$set": {"cart": [], "state": "ORDER_PLACED",
                                                    "last_order_id": order["id"],
                                                    "last_order_number": order["order_number"]}})
        return {"_order_created": True, "order": order, "ok": True,
                "order_number": order["order_number"], "eta_min": order["eta_min"], "eta_max": order["eta_max"],
                "total": order["total"]}

    if name == "get_order_status":
        o = await db.orders.find_one({"restaurant_id": restaurant["id"],
                                      "order_number": int(args.get("order_number", 0))}, NO_ID)
        if not o:
            return {"error": "order_not_found"}
        return {"order_number": o["order_number"], "status": o["status"], "total": o["total"]}

    if name == "request_human_support":
        await db.conversations.update_one({"id": conversation_id},
                                          {"$set": {"ai_active": False, "state": "HUMAN_HANDOFF"}})
        return {"ok": True, "handoff": True, "reason": args.get("reason", "")}

    return {"error": "unknown_tool"}


async def generate_reply(*, restaurant, ai_settings, conversation, customer, categories, items,
                         recent_messages, incoming_text):
    """Run one AI turn. Returns (reply_text, created_order_or_None)."""
    system = _build_system_prompt(restaurant, ai_settings, conversation, customer, categories, items, recent_messages)
    model = ai_settings.get("model") or os.environ.get("AI_MODEL", "gemini-2.5-flash")
    key = os.environ["EMERGENT_LLM_KEY"]
    created_order = None
    try:
        chat = (LlmChat(api_key=key, session_id=conversation["id"], system_message=system)
                .with_model("gemini", model)
                .with_tools(TOOLS, tool_choice="auto"))
        resp = await chat.send_message_with_tools(UserMessage(text=incoming_text))
        guard = 0
        while getattr(resp, "tool_calls", None) and guard < 6:
            guard += 1
            for tc in resp.tool_calls:
                try:
                    args = tc.arguments if isinstance(tc.arguments, dict) else json.loads(tc.arguments or "{}")
                except Exception:  # noqa
                    args = {}
                result = await _dispatch(tc.name, args, restaurant, items, conversation["id"], customer)
                if result.get("_order_created"):
                    created_order = result["order"]
                    result = {k: v for k, v in result.items() if k not in ("_order_created", "order")}
                chat.add_tool_result(tc.id, json.dumps(result, default=str))
            resp = await chat.send_message_with_tools()
        reply = (resp.content or "").strip() or "Ji, main aap ki kya madad kar sakta hoon?"
        return reply, created_order
    except Exception as e:  # noqa
        logger.exception("AI generate_reply failed: %s", e)
        return FALLBACK, None
