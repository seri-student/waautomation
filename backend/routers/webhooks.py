"""Provider-specific webhook handlers.

Each provider's payload is normalized into an IncomingMessage and handed to
the shared conversation engine, which is completely provider-agnostic.
"""
import os
import logging
from fastapi import APIRouter, Request, Response, HTTPException

from database import db, NO_ID, now_iso
from whatsapp.base import IncomingMessage
from services import conversation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks/whatsapp", tags=["webhooks"])


# ---------------- Evolution ----------------
@router.post("/evolution/{restaurant_id}")
async def evolution_webhook(restaurant_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}
    event = body.get("event", "")
    data = body.get("data", {}) or {}

    if event in ("connection.update",):
        state = data.get("state") or ((data.get("instance") or {}).get("state"))
        mapped = {"open": "connected", "connecting": "connecting", "close": "disconnected"}.get(state, state)
        if mapped:
            await db.whatsapp_connections.update_one(
                {"restaurant_id": restaurant_id},
                {"$set": {"status": mapped, "last_connected_at": now_iso() if mapped == "connected" else None},
                 "$push": {"logs": f"{now_iso()} — connection {mapped}"}})
        return {"ok": True}

    if event in ("messages.upsert", "message.upsert", ""):
        key = data.get("key", {}) or {}
        if key.get("fromMe"):
            return {"ok": True}
        remote = key.get("remoteJid", "")
        phone = remote.split("@")[0] if remote else ""
        message = data.get("message", {}) or {}
        text = (message.get("conversation")
                or (message.get("extendedTextMessage") or {}).get("text")
                or "")
        if phone and text:
            await conversation_service.handle_incoming(IncomingMessage(
                restaurant_id=restaurant_id, provider="evolution", customer_phone=phone,
                message_id=key.get("id", ""), text=text, timestamp=now_iso(),
                customer_name=data.get("pushName"),
            ))
    return {"ok": True}


# ---------------- Meta ----------------
@router.get("/meta")
async def meta_verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    env_token = os.environ.get("META_VERIFY_TOKEN", "")
    conn = await db.whatsapp_connections.find_one({"meta_verify_token": token}, NO_ID)
    if mode == "subscribe" and (token == env_token or conn):
        return Response(content=challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/meta")
async def meta_webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {}) or {}
            metadata = value.get("metadata", {}) or {}
            phone_number_id = metadata.get("phone_number_id")
            conn = await db.whatsapp_connections.find_one({"meta_phone_number_id": phone_number_id}, NO_ID)
            if not conn:
                continue
            restaurant_id = conn["restaurant_id"]
            contacts = {c.get("wa_id"): c.get("profile", {}).get("name")
                        for c in value.get("contacts", [])}
            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue
                phone = msg.get("from", "")
                text = (msg.get("text") or {}).get("body", "")
                if phone and text:
                    await conversation_service.handle_incoming(IncomingMessage(
                        restaurant_id=restaurant_id, provider="meta", customer_phone=phone,
                        message_id=msg.get("id", ""), text=text, timestamp=now_iso(),
                        customer_name=contacts.get(phone),
                    ))
    return {"ok": True}
