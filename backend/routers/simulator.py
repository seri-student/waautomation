"""Built-in WhatsApp Simulator — drives the exact same ordering engine."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import db, NO_ID, clean, clean_list
from auth import get_current_restaurant_id
from whatsapp.base import IncomingMessage
from services import conversation_service

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


class SimMessage(BaseModel):
    phone: str
    name: str | None = None
    text: str


@router.post("/message")
async def send_sim_message(body: SimMessage, rid: str = Depends(get_current_restaurant_id)):
    incoming = IncomingMessage(
        restaurant_id=rid, provider="simulator", customer_phone=body.phone.strip(),
        message_id=f"sim-{body.phone}", text=body.text, timestamp="",
        customer_name=body.name,
    )
    await conversation_service.handle_incoming(incoming)
    return await _load(rid, body.phone.strip())


@router.get("/messages")
async def get_sim_messages(phone: str, rid: str = Depends(get_current_restaurant_id)):
    return await _load(rid, phone.strip())


async def _load(rid: str, phone: str):
    cust = clean(await db.customers.find_one({"restaurant_id": rid, "phone": phone}, NO_ID))
    if not cust:
        return {"conversation": None, "messages": []}
    conv = clean(await db.conversations.find_one(
        {"restaurant_id": rid, "customer_id": cust["id"]}, NO_ID, sort=[("created_at", -1)]))
    if not conv:
        return {"conversation": None, "messages": []}
    messages = clean_list(await db.messages.find({"conversation_id": conv["id"]}, NO_ID)
                          .sort("created_at", 1).to_list(500))
    return {"conversation": conv, "messages": messages}
