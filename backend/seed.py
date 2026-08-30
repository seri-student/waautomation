"""Idempotent demo seeding: owner account + Pizza Palace + menu + samples."""
import os
from datetime import datetime, timezone, timedelta

from database import db, NO_ID, new_id, now_iso
from auth import hash_password, verify_password

DEMO_RESTAURANT_ID = "demo-pizza-palace"


async def ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.customers.create_index([("restaurant_id", 1), ("phone", 1)])
    await db.orders.create_index([("restaurant_id", 1), ("created_at", -1)])
    await db.menu_items.create_index("restaurant_id")
    await db.conversations.create_index([("restaurant_id", 1), ("customer_id", 1)])


async def seed():
    await ensure_indexes()

    admin_email = os.environ.get("ADMIN_EMAIL", "owner@pizzapalace.pk").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "palace123")

    # Restaurant profile
    restaurant = await db.restaurants.find_one({"id": DEMO_RESTAURANT_ID}, NO_ID)
    if not restaurant:
        restaurant = {
            "id": DEMO_RESTAURANT_ID,
            "name": "Pizza Palace",
            "logo": "",
            "description": "Fast food & pizza — Lahore's favourite since 2015.",
            "whatsapp_number": "+92 300 1234567",
            "contact_number": "+92 42 111 222 333",
            "address": "Main Boulevard, Gulberg III",
            "city": "Lahore",
            "opening_hours": "Mon-Sun, 12:00 PM – 2:00 AM",
            "delivery_areas": "Gulberg, DHA, Model Town, Johar Town",
            "delivery_fee": 150,
            "min_order": 500,
            "prep_time_min": 20,
            "prep_time_max": 30,
            "delivery_time_min": 15,
            "delivery_time_max": 20,
            "currency": "PKR",
            "ai_greeting": "Assalam-o-Alaikum! Welcome to Pizza Palace 🍕 How can I help you today?",
            "created_at": now_iso(),
        }
        await db.restaurants.insert_one({**restaurant})

    # Owner user
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": new_id(), "email": admin_email, "password_hash": hash_password(admin_password),
            "name": "Pizza Palace Owner", "role": "owner", "restaurant_id": DEMO_RESTAURANT_ID,
            "created_at": now_iso(),
        })
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email},
                                  {"$set": {"password_hash": hash_password(admin_password),
                                            "restaurant_id": DEMO_RESTAURANT_ID}})

    # WhatsApp connection config
    if not await db.whatsapp_connections.find_one({"restaurant_id": DEMO_RESTAURANT_ID}):
        await db.whatsapp_connections.insert_one({
            "id": new_id(), "restaurant_id": DEMO_RESTAURANT_ID, "provider": "simulator",
            "status": "connected", "connected_number": "Simulator",
            "evolution_instance_name": f"rest_{DEMO_RESTAURANT_ID[:8]}",
            "evolution_api_url": "", "evolution_api_key": "",
            "meta_phone_number_id": "", "meta_waba_id": "", "meta_access_token": "",
            "meta_verify_token": os.environ.get("META_VERIFY_TOKEN", ""),
            "last_connected_at": now_iso(), "logs": [f"{now_iso()} — simulator ready"],
            "created_at": now_iso(),
        })

    # AI settings
    if not await db.ai_settings.find_one({"restaurant_id": DEMO_RESTAURANT_ID}):
        await db.ai_settings.insert_one({
            "id": new_id(), "restaurant_id": DEMO_RESTAURANT_ID, "provider": "gemini",
            "model": os.environ.get("AI_MODEL", "gemini-2.5-flash"),
            "personality": "friendly Pakistani restaurant receptionist",
            "language_behavior": "Auto-detect and reply in English, Urdu or Roman Urdu",
            "upsell_enabled": True, "max_upsell_attempts": 1, "human_handoff_enabled": True,
            "created_at": now_iso(),
        })

    # Menu (only if empty)
    if await db.menu_items.count_documents({"restaurant_id": DEMO_RESTAURANT_ID}) == 0:
        await _seed_menu()

    # Sample customers + orders (only if empty)
    if await db.orders.count_documents({"restaurant_id": DEMO_RESTAURANT_ID}) == 0:
        await _seed_sample_orders()


async def _seed_menu():
    cats = [
        ("Burgers", 1), ("Pizza", 2), ("Fries", 3), ("Drinks", 4), ("Desserts", 5),
    ]
    cat_ids = {}
    for name, order in cats:
        cid = new_id()
        cat_ids[name] = cid
        await db.menu_categories.insert_one({
            "id": cid, "restaurant_id": DEMO_RESTAURANT_ID, "name": name,
            "sort_order": order, "created_at": now_iso(),
        })

    items = [
        ("Burgers", "Zinger Burger", "Crispy fried chicken fillet with mayo & lettuce", 650, True),
        ("Burgers", "Beef Burger", "Juicy grilled beef patty with cheese", 750, True),
        ("Burgers", "Chicken Cheese Burger", "Grilled chicken with melted cheese", 700, True),
        ("Pizza", "Large Pizza", "Large signature pizza with your choice of toppings", 1499, True),
        ("Pizza", "Medium Pizza", "Medium pizza, perfect for two", 999, True),
        ("Pizza", "Chicken Tikka Pizza", "Desi-style chicken tikka pizza", 1299, True),
        ("Fries", "Regular Fries", "Golden crispy fries", 250, True),
        ("Fries", "Loaded Fries", "Fries topped with cheese & jalapeños", 450, True),
        ("Drinks", "Coke", "Chilled 345ml can", 120, True),
        ("Drinks", "Sprite", "Chilled 345ml can", 120, True),
        ("Drinks", "Mineral Water", "500ml bottle", 80, True),
        ("Desserts", "Brownie", "Warm chocolate fudge brownie", 350, True),
        ("Desserts", "Lava Cake", "Molten chocolate lava cake", 400, True),
    ]
    name_to_id = {}
    images = {
        "Zinger Burger": "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=500&q=80",
        "Beef Burger": "https://images.unsplash.com/photo-1551782450-17144efb9c50?w=500&q=80",
        "Chicken Cheese Burger": "https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=500&q=80",
        "Large Pizza": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=500&q=80",
        "Medium Pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500&q=80",
        "Chicken Tikka Pizza": "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=500&q=80",
        "Regular Fries": "https://images.unsplash.com/photo-1666304752980-678d5c35c911?w=500&q=80",
        "Loaded Fries": "https://images.unsplash.com/photo-1639744210631-209fce3e256c?w=500&q=80",
        "Coke": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=500&q=80",
        "Sprite": "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=500&q=80",
        "Mineral Water": "",
        "Brownie": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500&q=80",
        "Lava Cake": "https://images.unsplash.com/photo-1624353365286-3f8d62daad51?w=500&q=80",
    }
    docs = []
    for cat, name, desc, price, avail in items:
        iid = new_id()
        name_to_id[name] = iid
        docs.append({
            "id": iid, "restaurant_id": DEMO_RESTAURANT_ID, "category_id": cat_ids[cat],
            "name": name, "description": desc, "price": price, "available": avail,
            "image_url": images.get(name, ""), "addon_item_ids": [], "created_at": now_iso(),
        })
    # recommended add-ons
    addons = {
        "Zinger Burger": ["Regular Fries", "Coke"],
        "Beef Burger": ["Loaded Fries", "Coke"],
        "Large Pizza": ["Coke", "Brownie"],
        "Chicken Tikka Pizza": ["Sprite", "Lava Cake"],
        "Loaded Fries": ["Coke"],
    }
    for d in docs:
        if d["name"] in addons:
            d["addon_item_ids"] = [name_to_id[a] for a in addons[d["name"]] if a in name_to_id]
    await db.menu_items.insert_many(docs)


async def _seed_sample_orders():
    samples = [
        ("Ali Raza", "923001112233", "delivery", "House 12, Street 4, DHA Phase 5",
         [("Zinger Burger", 2, 650), ("Regular Fries", 1, 250), ("Coke", 2, 120)], "Delivered", 3),
        ("Sara Khan", "923214445566", "pickup", None,
         [("Large Pizza", 1, 1499), ("Coke", 1, 120)], "Preparing", 0),
        ("Bilal Ahmed", "923337778899", "delivery", "Flat 3B, Model Town Block C",
         [("Chicken Tikka Pizza", 1, 1299), ("Loaded Fries", 1, 450)], "New", 0),
        ("Ayesha Malik", "923451234567", "delivery", "Johar Town, Block G1",
         [("Beef Burger", 1, 750), ("Brownie", 1, 350)], "Out for Delivery", 1),
    ]
    num = 1000
    for name, phone, otype, addr, items, status, days_ago in samples:
        num += 1
        cust = await db.customers.find_one({"restaurant_id": DEMO_RESTAURANT_ID, "phone": phone}, NO_ID)
        if not cust:
            cust = {"id": new_id(), "restaurant_id": DEMO_RESTAURANT_ID, "phone": phone,
                    "name": name, "total_orders": 0, "total_spent": 0.0,
                    "last_order_at": None, "created_at": now_iso()}
            await db.customers.insert_one({**cust})
        subtotal = sum(q * p for _, q, p in items)
        delivery = 150 if otype == "delivery" else 0
        total = subtotal + delivery
        created = (datetime.now(timezone.utc) - timedelta(days=days_ago, hours=days_ago)).isoformat()
        order = {
            "id": new_id(), "restaurant_id": DEMO_RESTAURANT_ID, "customer_id": cust["id"],
            "conversation_id": None, "order_number": num, "customer_name": name,
            "customer_phone": phone, "order_type": otype, "address": addr,
            "items": [{"item_id": new_id(), "name": n, "qty": q, "unit_price": p, "line_total": q * p}
                      for n, q, p in items],
            "subtotal": subtotal, "delivery_fee": delivery, "total": total, "currency": "PKR",
            "status": status, "eta_min": 35, "eta_max": 50,
            "status_history": [{"status": status, "at": created}],
            "created_at": created, "updated_at": created,
        }
        await db.orders.insert_one({**order})
        await db.customers.update_one({"id": cust["id"]},
                                      {"$inc": {"total_orders": 1, "total_spent": total},
                                       "$set": {"last_order_at": created}})
    # bump counter so real orders continue after samples
    await db.counters.update_one({"id": f"orders:{DEMO_RESTAURANT_ID}"},
                                 {"$set": {"seq": num, "id": f"orders:{DEMO_RESTAURANT_ID}"}}, upsert=True)
