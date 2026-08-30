import os
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, EmailStr

from database import db, NO_ID, new_id, now_iso, clean
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    name: str
    restaurant_name: str


class LoginBody(BaseModel):
    email: EmailStr
    password: str


async def _default_restaurant(name: str) -> str:
    rid = new_id()
    await db.restaurants.insert_one({
        "id": rid, "name": name, "logo": "", "description": "",
        "whatsapp_number": "", "contact_number": "", "address": "", "city": "",
        "opening_hours": "Mon-Sun, 11:00 AM – 11:00 PM", "delivery_areas": "",
        "delivery_fee": 150, "min_order": 500, "prep_time_min": 20, "prep_time_max": 30,
        "delivery_time_min": 15, "delivery_time_max": 20, "currency": "PKR",
        "ai_greeting": f"Assalam-o-Alaikum! Welcome to {name}. How can I help you today?",
        "created_at": now_iso(),
    })
    await db.whatsapp_connections.insert_one({
        "id": new_id(), "restaurant_id": rid, "provider": "simulator", "status": "connected",
        "connected_number": "Simulator", "evolution_instance_name": f"rest_{rid[:8]}",
        "evolution_api_url": "", "evolution_api_key": "", "meta_phone_number_id": "",
        "meta_waba_id": "", "meta_access_token": "",
        "meta_verify_token": os.environ.get("META_VERIFY_TOKEN", ""),
        "last_connected_at": now_iso(), "logs": [f"{now_iso()} — simulator ready"], "created_at": now_iso(),
    })
    await db.ai_settings.insert_one({
        "id": new_id(), "restaurant_id": rid, "provider": "gemini",
        "model": os.environ.get("AI_MODEL", "gemini-2.5-flash"),
        "personality": "friendly Pakistani restaurant receptionist",
        "language_behavior": "Auto-detect and reply in English, Urdu or Roman Urdu",
        "upsell_enabled": True, "max_upsell_attempts": 1, "human_handoff_enabled": True,
        "created_at": now_iso(),
    })
    return rid


@router.post("/register")
async def register(body: RegisterBody):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    rid = await _default_restaurant(body.restaurant_name)
    uid = new_id()
    await db.users.insert_one({
        "id": uid, "email": email, "password_hash": hash_password(body.password),
        "name": body.name, "role": "owner", "restaurant_id": rid, "created_at": now_iso(),
    })
    token = create_access_token(uid, email)
    return {"access_token": token, "token_type": "bearer",
            "user": {"id": uid, "email": email, "name": body.name, "restaurant_id": rid}}


@router.post("/login")
async def login(body: LoginBody):
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], email)
    return {"access_token": token, "token_type": "bearer",
            "user": {"id": user["id"], "email": email, "name": user.get("name"),
                     "restaurant_id": user.get("restaurant_id")}}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    restaurant = clean(await db.restaurants.find_one({"id": user.get("restaurant_id")}, NO_ID))
    return {"user": user, "restaurant": restaurant}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}
