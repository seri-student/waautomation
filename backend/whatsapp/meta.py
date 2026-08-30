"""Meta Official WhatsApp Cloud API provider.

Credentials always stay server-side. Real Graph API calls are made when
configured; otherwise a disconnected status with guidance is returned.
"""
import os
import httpx

from database import now_iso
from .base import WhatsAppProvider, ConnectionStatus


class MetaCloudProvider(WhatsAppProvider):
    name = "meta"

    @property
    def graph_url(self) -> str:
        return (self.config.get("meta_graph_api_url") or os.environ.get("META_GRAPH_API_URL")
                or "https://graph.facebook.com/v21.0").rstrip("/")

    @property
    def access_token(self) -> str:
        return self.config.get("meta_access_token") or os.environ.get("META_ACCESS_TOKEN") or ""

    @property
    def phone_number_id(self) -> str:
        return self.config.get("meta_phone_number_id") or os.environ.get("META_PHONE_NUMBER_ID") or ""

    @property
    def waba_id(self) -> str:
        return self.config.get("meta_waba_id") or os.environ.get("META_WABA_ID") or ""

    def _configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    async def connect(self) -> ConnectionStatus:
        return await self.get_connection_status()

    async def disconnect(self) -> ConnectionStatus:
        return ConnectionStatus(status="disconnected", detail="Meta connection is stateless; credentials retained")

    async def send_message(self, to_phone: str, text: str) -> bool:
        if not self._configured():
            return False
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.post(
                    f"{self.graph_url}/{self.phone_number_id}/messages",
                    headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"},
                    json={
                        "messaging_product": "whatsapp",
                        "to": to_phone,
                        "type": "text",
                        "text": {"body": text},
                    },
                )
                return r.status_code < 300
        except Exception:  # noqa
            return False

    async def get_connection_status(self) -> ConnectionStatus:
        if not self._configured():
            return ConnectionStatus(status="disconnected",
                                    detail="Meta credentials not configured. Add Access Token and Phone Number ID.")
        # Verify credentials by fetching the phone number metadata
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.get(
                    f"{self.graph_url}/{self.phone_number_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params={"fields": "display_phone_number,verified_name"},
                )
                data = r.json() if r.content else {}
            if r.status_code < 300:
                return ConnectionStatus(status="connected",
                                        connected_number=data.get("display_phone_number"),
                                        last_connected_at=now_iso(),
                                        detail=data.get("verified_name"))
            return ConnectionStatus(status="error", detail=str(data))
        except Exception as e:  # noqa
            return ConnectionStatus(status="error", detail=str(e))

    async def get_qr_code(self) -> ConnectionStatus:
        return ConnectionStatus(status="disconnected", detail="Meta Cloud API uses webhooks, not QR codes")
