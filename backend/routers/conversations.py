from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import db, NO_ID, new_id, now_iso, clean, clean_list
from auth import get_current_restaurant_id
from events import bus
from whatsapp.service import whatsapp_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class HandoffBody(BaseModel):
    ai_active: bool


class ReplyBody(BaseModel):
    text: str


@router.get("")
async def list_conversations(rid: str = Depends(get_current_restaurant_id)):
    convs = clean_list(await db.conversations.find({"restaurant_id": rid}, NO_ID)
                       .sort("last_message_at", -1).to_list(200))
    result = []
    for c in convs:
        last = clean(await db.messages.find_one({"conversation_id": c["id"]}, NO_ID,
                                                sort=[("created_at", -1)]))
        cust = clean(await db.customers.find_one({"id": c["customer_id"]}, NO_ID))
        result.append({**c, "last_message": last, "customer": cust})
    return result


@router.get("/{conversation_id}/messages")
async def get_messages(conversation_id: str, rid: str = Depends(get_current_restaurant_id)):
    conv = clean(await db.conversations.find_one({"id": conversation_id, "restaurant_id": rid}, NO_ID))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = clean_list(await db.messages.find({"conversation_id": conversation_id}, NO_ID)
                          .sort("created_at", 1).to_list(500))
    return {"conversation": conv, "messages": messages}


@router.post("/{conversation_id}/handoff")
async def set_handoff(conversation_id: str, body: HandoffBody, rid: str = Depends(get_current_restaurant_id)):
    conv = clean(await db.conversations.find_one({"id": conversation_id, "restaurant_id": rid}, NO_ID))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    state = "SELECTING_ITEMS" if body.ai_active else "HUMAN_HANDOFF"
    await db.conversations.update_one({"id": conversation_id},
                                      {"$set": {"ai_active": body.ai_active, "state": state}})
    await bus.publish(rid, "handoff", {"conversation_id": conversation_id, "ai_active": body.ai_active})
    return {"ok": True, "ai_active": body.ai_active}


@router.post("/{conversation_id}/reply")
async def human_reply(conversation_id: str, body: ReplyBody, rid: str = Depends(get_current_restaurant_id)):
    conv = clean(await db.conversations.find_one({"id": conversation_id, "restaurant_id": rid}, NO_ID))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg = {
        "id": new_id(), "restaurant_id": rid, "conversation_id": conversation_id,
        "customer_id": conv["customer_id"], "direction": "out", "sender": "human",
        "text": body.text, "msg_type": "text", "provider": conv.get("provider", "simulator"),
        "created_at": now_iso(),
    }
    await db.messages.insert_one({**msg})
    await db.conversations.update_one({"id": conversation_id}, {"$set": {"last_message_at": now_iso()}})
    await bus.publish(rid, "message", {"conversation_id": conversation_id, "message": msg})
    await whatsapp_service.send_human_reply(rid, conv["customer_phone"], body.text)
    return {"ok": True, "message": msg}
