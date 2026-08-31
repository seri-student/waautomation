"""Baileys provider — talks to the internal Node WhatsApp gateway.

Free, QR-based WhatsApp using @whiskeysockets/baileys (no headless browser).
Credentials/sessions live entirely in the gateway; the backend only relays
provider-agnostic operations to it over localhost.
"""
import os
import httpx

from database import now_iso
from .base import WhatsAppProvider, ConnectionStatus


class BaileysProvider(WhatsAppProvider):
    name = "baileys"

    @property
    def gateway(self) -> str:
        return (os.environ.get("WHATSAPP_GATEWAY_URL") or "http://localhost:3001").rstrip("/")

    def _headers(self) -> dict:
        return {"x-gateway-secret": os.environ.get("WHATSAPP_GATEWAY_SECRET", "")}

    def _url(self, suffix: str) -> str:
        return f"{self.gateway}/instance/{self.restaurant_id}/{suffix}"

    async def connect(self) -> ConnectionStatus:
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(self._url("connect"), headers=self._headers())
                data = r.json() if r.content else {}
            return ConnectionStatus(
                status=data.get("status", "connecting"),
                qr_code=data.get("qr"),
                connected_number=data.get("number"),
                last_connected_at=now_iso() if data.get("status") == "connected" else None,
                detail="Scan this QR code with WhatsApp → Linked Devices" if data.get("qr") else None,
                logs=[f"{now_iso()} — baileys connect ({data.get('status')})"],
            )
        except Exception as e:  # noqa
            return ConnectionStatus(status="error", detail=f"Gateway unreachable: {e}")

    async def disconnect(self) -> ConnectionStatus:
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                await c.post(self._url("logout"), headers=self._headers())
        except Exception:  # noqa
            pass
        return ConnectionStatus(status="disconnected", detail="Logged out",
                                logs=[f"{now_iso()} — baileys disconnected"])

    async def send_message(self, to_phone: str, text: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=25) as c:
                r = await c.post(self._url("send"), headers=self._headers(),
                                 json={"to": to_phone, "text": text})
                return r.status_code < 300
        except Exception:  # noqa
            return False

    async def get_connection_status(self) -> ConnectionStatus:
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.get(self._url("status"), headers=self._headers())
                data = r.json() if r.content else {}
            return ConnectionStatus(
                status=data.get("status", "disconnected"),
                qr_code=data.get("qr"),
                connected_number=data.get("number"),
                last_connected_at=now_iso() if data.get("status") == "connected" else None,
            )
        except Exception as e:  # noqa
            return ConnectionStatus(status="error", detail=f"Gateway unreachable: {e}")

    async def get_qr_code(self) -> ConnectionStatus:
        return await self.connect()
