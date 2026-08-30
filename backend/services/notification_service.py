"""Order status change notifications sent back to the customer."""
import logging

from database import db, NO_ID, new_id, now_iso
from events import bus
from whatsapp.service import whatsapp_service

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    "Confirmed": "Good news! Your order #{n} has been confirmed. We're getting it ready. 🎉",
    "Preparing": "Your order #{n} is now being prepared in our kitchen. 👨‍🍳",
    "Ready": "Your order #{n} is ready!",
    "Out for Delivery": "Your order #{n} is out for delivery. It'll reach you soon! 🛵",
    "Delivered": "Your order #{n} has been delivered. Thank you for ordering — enjoy your meal! 🙏",
    "Cancelled": "Your order #{n} has been cancelled. Please contact us if you have any questions.",
}


async def notify_status_change(order: dict, new_status: str):
    template = STATUS_MESSAGES.get(new_status)
    if not template:
        return
    text = template.format(n=order["order_number"])
    restaurant_id = order["restaurant_id"]

    conv = await db.conversations.find_one({"id": order.get("conversation_id")}, NO_ID)
    if not conv:
        conv = await db.conversations.find_one(
            {"restaurant_id": restaurant_id, "customer_id": order["customer_id"]}, NO_ID,
            sort=[("created_at", -1)])

    provider = (conv or {}).get("provider", "simulator")
    if conv:
        msg = {
            "id": new_id(), "restaurant_id": restaurant_id, "conversation_id": conv["id"],
            "customer_id": order["customer_id"], "direction": "out", "sender": "system",
            "text": text, "msg_type": "status_update", "provider": provider, "created_at": now_iso(),
        }
        await db.messages.insert_one({**msg})
        await bus.publish(restaurant_id, "message", {"conversation_id": conv["id"], "message": msg})

    try:
        await whatsapp_service.send_order_notification(restaurant_id, order["customer_phone"], text)
    except Exception as e:  # noqa
        logger.warning("status notify send failed: %s", e)
