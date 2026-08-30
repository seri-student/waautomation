"""Provider-agnostic conversation engine.

Takes a normalized IncomingMessage, manages the customer + conversation +
message records, runs the AI (unless a human has taken over), sends the
reply through the active WhatsApp provider, and broadcasts dashboard events.
"""
import logging

from database import db, NO_ID, new_id, now_iso
from events import bus
from services import ai_service
from whatsapp.base import IncomingMessage
from whatsapp.service import whatsapp_service

logger = logging.getLogger(__name__)


async def _get_or_create_customer(restaurant_id: str, phone: str, name: str | None) -> dict:
    cust = await db.customers.find_one({"restaurant_id": restaurant_id, "phone": phone}, NO_ID)
    if cust:
        return cust
    cust = {
        "id": new_id(), "restaurant_id": restaurant_id, "phone": phone,
        "name": name or "", "total_orders": 0, "total_spent": 0.0,
        "last_order_at": None, "created_at": now_iso(),
    }
    await db.customers.insert_one({**cust})
    return cust


async def _get_or_create_conversation(restaurant_id: str, customer: dict, provider: str) -> dict:
    conv = await db.conversations.find_one(
        {"restaurant_id": restaurant_id, "customer_id": customer["id"]}, NO_ID, sort=[("created_at", -1)])
    if conv:
        if conv.get("provider") != provider:
            await db.conversations.update_one({"id": conv["id"]}, {"$set": {"provider": provider}})
            conv["provider"] = provider
        return conv
    conv = {
        "id": new_id(), "restaurant_id": restaurant_id, "customer_id": customer["id"],
        "customer_phone": customer["phone"], "customer_name": customer.get("name") or "",
        "provider": provider, "state": "GREETING", "cart": [], "order_type": None,
        "address": None, "ai_active": True, "last_message_at": now_iso(), "created_at": now_iso(),
    }
    await db.conversations.insert_one({**conv})
    return conv


async def _save_message(conv, restaurant_id, direction, sender, text, provider, msg_type="text"):
    msg = {
        "id": new_id(), "restaurant_id": restaurant_id, "conversation_id": conv["id"],
        "customer_id": conv["customer_id"], "direction": direction, "sender": sender,
        "text": text, "msg_type": msg_type, "provider": provider, "created_at": now_iso(),
    }
    await db.messages.insert_one({**msg})
    await db.conversations.update_one({"id": conv["id"]}, {"$set": {"last_message_at": now_iso()}})
    await bus.publish(restaurant_id, "message", {"conversation_id": conv["id"], "message": msg})
    return msg


async def handle_incoming(msg: IncomingMessage) -> dict | None:
    """Full pipeline for one incoming customer message. Returns AI reply msg or None."""
    restaurant = await db.restaurants.find_one({"id": msg.restaurant_id}, NO_ID)
    if not restaurant:
        logger.warning("Incoming message for unknown restaurant %s", msg.restaurant_id)
        return None

    customer = await _get_or_create_customer(msg.restaurant_id, msg.customer_phone, msg.customer_name)
    conv = await _get_or_create_conversation(msg.restaurant_id, customer, msg.provider)

    await _save_message(conv, msg.restaurant_id, "in", "customer", msg.text, msg.provider)

    # Human handoff active -> do not auto-reply
    if not conv.get("ai_active", True):
        await bus.publish(msg.restaurant_id, "handoff_pending", {"conversation_id": conv["id"]})
        return None

    ai_settings = await db.ai_settings.find_one({"restaurant_id": msg.restaurant_id}, NO_ID) or {}
    categories = await db.menu_categories.find({"restaurant_id": msg.restaurant_id}, NO_ID).sort("sort_order", 1).to_list(100)
    items = await db.menu_items.find({"restaurant_id": msg.restaurant_id}, NO_ID).to_list(500)
    recent = await db.messages.find({"conversation_id": conv["id"]}, NO_ID).sort("created_at", -1).to_list(10)
    recent = list(reversed(recent))

    reply, created_order = await ai_service.generate_reply(
        restaurant=restaurant, ai_settings=ai_settings, conversation=conv, customer=customer,
        categories=categories, items=items, recent_messages=recent, incoming_text=msg.text,
    )

    reply_msg = await _save_message(conv, msg.restaurant_id, "out", "ai", reply, msg.provider)

    # Deliver via active provider (no-op for simulator)
    try:
        await whatsapp_service.send_customer_message(msg.restaurant_id, msg.customer_phone, reply)
    except Exception as e:  # noqa
        logger.warning("send failed: %s", e)

    if created_order:
        await bus.publish(msg.restaurant_id, "new_order", {"order": created_order})

    return reply_msg
