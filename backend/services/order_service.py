"""Deterministic order calculation and creation.

All money math lives here — never in the AI. Prices, delivery fee and
totals are always computed from the database.
"""
from database import db, NO_ID, new_id, now_iso, next_order_number

ORDER_STATUSES = ["New", "Confirmed", "Preparing", "Ready", "Out for Delivery", "Delivered", "Cancelled"]


def match_menu_item(menu_items: list, name: str):
    if not name:
        return None
    n = name.strip().lower()
    # exact, then contains, then token overlap
    for it in menu_items:
        if it["name"].strip().lower() == n:
            return it
    for it in menu_items:
        if n in it["name"].strip().lower() or it["name"].strip().lower() in n:
            return it
    for it in menu_items:
        item_tokens = set(it["name"].lower().split())
        if item_tokens & set(n.split()):
            return it
    return None


def compute_totals(restaurant: dict, cart: list, order_type: str | None) -> dict:
    items = []
    subtotal = 0.0
    for c in cart:
        line = round(float(c["unit_price"]) * int(c["qty"]), 2)
        subtotal += line
        items.append({
            "item_id": c["item_id"],
            "name": c["name"],
            "qty": int(c["qty"]),
            "unit_price": float(c["unit_price"]),
            "line_total": line,
        })
    delivery_fee = float(restaurant.get("delivery_fee", 0)) if order_type == "delivery" else 0.0
    total = round(subtotal + delivery_fee, 2)
    return {
        "items": items,
        "subtotal": round(subtotal, 2),
        "delivery_fee": round(delivery_fee, 2),
        "total": total,
        "currency": restaurant.get("currency", "PKR"),
    }


def estimate_eta(restaurant: dict, order_type: str | None) -> dict:
    prep_min = int(restaurant.get("prep_time_min", 20))
    prep_max = int(restaurant.get("prep_time_max", 30))
    if order_type == "delivery":
        eta_min = prep_min + int(restaurant.get("delivery_time_min", 15))
        eta_max = prep_max + int(restaurant.get("delivery_time_max", 20))
    else:
        eta_min, eta_max = prep_min, prep_max
    return {"eta_min": eta_min, "eta_max": eta_max}


async def create_order(*, restaurant: dict, conversation: dict, customer: dict) -> dict:
    """Create an order from the conversation cart. Returns the order dict."""
    cart = conversation.get("cart", [])
    order_type = conversation.get("order_type") or "delivery"
    totals = compute_totals(restaurant, cart, order_type)
    eta = estimate_eta(restaurant, order_type)
    number = await next_order_number(restaurant["id"])

    order = {
        "id": new_id(),
        "restaurant_id": restaurant["id"],
        "customer_id": customer["id"],
        "conversation_id": conversation["id"],
        "order_number": number,
        "customer_name": conversation.get("customer_name") or customer.get("name") or "Customer",
        "customer_phone": conversation.get("customer_phone") or customer.get("phone"),
        "order_type": order_type,
        "address": conversation.get("address") if order_type == "delivery" else None,
        "items": totals["items"],
        "subtotal": totals["subtotal"],
        "delivery_fee": totals["delivery_fee"],
        "total": totals["total"],
        "currency": totals["currency"],
        "status": "New",
        "eta_min": eta["eta_min"],
        "eta_max": eta["eta_max"],
        "status_history": [{"status": "New", "at": now_iso()}],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    await db.orders.insert_one({**order})

    # Update customer aggregates
    await db.customers.update_one(
        {"id": customer["id"]},
        {"$inc": {"total_orders": 1, "total_spent": totals["total"]},
         "$set": {"last_order_at": now_iso(),
                  "name": order["customer_name"]}},
    )
    order.pop("_id", None)
    return order
