import os
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Optional

from database import db, NO_ID, now_iso, clean
from auth import get_current_restaurant_id
from whatsapp.service import get_whatsapp_provider

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


def _mask(val: str) -> str:
    if not val:
        return ""
    if len(val) <= 6:
        return "••••"
    return val[:3] + "••••" + val[-3:]


class ProviderBody(BaseModel):
    provider: str  # simulator | evolution | meta


class EvolutionConfig(BaseModel):
    evolution_api_url: Optional[str] = None
    evolution_api_key: Optional[str] = None
    evolution_instance_name: Optional[str] = None


class MetaConfig(BaseModel):
    meta_graph_api_url: Optional[str] = None
    meta_access_token: Optional[str] = None
    meta_phone_number_id: Optional[str] = None
    meta_waba_id: Optional[str] = None
    meta_verify_token: Optional[str] = None


def _public(conn: dict, base_url: str | None = None) -> dict:
    conn = clean(conn) or {}
    app_url = (base_url or os.environ.get("APP_URL", "")).rstrip("/")
    return {
        "provider": conn.get("provider", "simulator"),
        "status": conn.get("status", "disconnected"),
        "connected_number": conn.get("connected_number"),
        "last_connected_at": conn.get("last_connected_at"),
        "logs": conn.get("logs", [])[-15:],
        "evolution": {
            "evolution_api_url": conn.get("evolution_api_url", ""),
            "evolution_api_key_masked": _mask(conn.get("evolution_api_key", "")),
            "evolution_instance_name": conn.get("evolution_instance_name", ""),
            "configured": bool(conn.get("evolution_api_url") or os.environ.get("EVOLUTION_API_URL")),
        },
        "meta": {
            "meta_phone_number_id": conn.get("meta_phone_number_id", ""),
            "meta_waba_id": conn.get("meta_waba_id", ""),
            "meta_access_token_masked": _mask(conn.get("meta_access_token", "")),
            "meta_verify_token": conn.get("meta_verify_token", ""),
            "webhook_url": f"{app_url}/api/webhooks/whatsapp/meta",
            "configured": bool(conn.get("meta_access_token") and conn.get("meta_phone_number_id")),
        },
        "evolution_webhook_url": f"{app_url}/api/webhooks/whatsapp/evolution/{conn.get('restaurant_id')}",
    }


async def _get_conn(rid: str) -> dict:
    conn = await db.whatsapp_connections.find_one({"restaurant_id": rid}, NO_ID)
    if not conn:
        conn = {"restaurant_id": rid, "provider": "simulator", "status": "connected", "logs": []}
        await db.whatsapp_connections.insert_one({"id": rid, **conn})
    return conn


@router.get("/config")
async def get_config(request: Request, rid: str = Depends(get_current_restaurant_id)):
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base = f"{proto}://{host}" if host else None
    return _public(await _get_conn(rid), base)


@router.post("/provider")
async def set_provider(body: ProviderBody, rid: str = Depends(get_current_restaurant_id)):
    status = "connected" if body.provider == "simulator" else "disconnected"
    await db.whatsapp_connections.update_one(
        {"restaurant_id": rid},
        {"$set": {"provider": body.provider, "status": status},
         "$push": {"logs": f"{now_iso()} — provider switched to {body.provider}"}})
    return _public(await _get_conn(rid))


@router.put("/evolution")
async def set_evolution(body: EvolutionConfig, rid: str = Depends(get_current_restaurant_id)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await db.whatsapp_connections.update_one({"restaurant_id": rid}, {"$set": updates})
    return _public(await _get_conn(rid))


@router.put("/meta")
async def set_meta(body: MetaConfig, rid: str = Depends(get_current_restaurant_id)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await db.whatsapp_connections.update_one({"restaurant_id": rid}, {"$set": updates})
    return _public(await _get_conn(rid))


@router.post("/connect")
async def connect(rid: str = Depends(get_current_restaurant_id)):
    provider = await get_whatsapp_provider(rid)
    status = await provider.connect()
    updates = {"status": status.status}
    if status.connected_number:
        updates["connected_number"] = status.connected_number
    if status.last_connected_at:
        updates["last_connected_at"] = status.last_connected_at
    log_entries = status.logs or [f"{now_iso()} — connect requested ({provider.name})"]
    await db.whatsapp_connections.update_one({"restaurant_id": rid},
                                             {"$set": updates, "$push": {"logs": {"$each": log_entries}}})
    conn = _public(await _get_conn(rid))
    conn["qr_code"] = status.qr_code
    conn["detail"] = status.detail
    return conn


@router.post("/disconnect")
async def disconnect(rid: str = Depends(get_current_restaurant_id)):
    provider = await get_whatsapp_provider(rid)
    status = await provider.disconnect()
    await db.whatsapp_connections.update_one(
        {"restaurant_id": rid},
        {"$set": {"status": status.status, "connected_number": None},
         "$push": {"logs": f"{now_iso()} — disconnected"}})
    return _public(await _get_conn(rid))


@router.get("/status")
async def status(rid: str = Depends(get_current_restaurant_id)):
    provider = await get_whatsapp_provider(rid)
    st = await provider.get_connection_status()
    await db.whatsapp_connections.update_one({"restaurant_id": rid}, {"$set": {"status": st.status}})
    conn = _public(await _get_conn(rid))
    conn["detail"] = st.detail
    conn["qr_code"] = st.qr_code
    return conn
