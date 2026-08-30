"""Evolution API provider (unofficial self-hosted WhatsApp gateway).

Real HTTP calls are made when EVOLUTION_API_URL + EVOLUTION_API_KEY are
configured (globally via env or per-restaurant in config). When not
configured the provider reports a disconnected status with guidance,
so the dashboard flow still works and connects the moment creds exist.
"""
import os
import httpx

from database import now_iso
from .base import WhatsAppProvider, ConnectionStatus


class EvolutionApiProvider(WhatsAppProvider):
    name = "evolution"

    @property
    def base_url(self) -> str:
        return (self.config.get("evolution_api_url") or os.environ.get("EVOLUTION_API_URL") or "").rstrip("/")

    @property
    def api_key(self) -> str:
        return self.config.get("evolution_api_key") or os.environ.get("EVOLUTION_API_KEY") or ""

    @property
    def instance(self) -> str:
        return self.config.get("evolution_instance_name") or f"rest_{self.restaurant_id[:8]}"

    def _headers(self) -> dict:
        return {"apikey": self.api_key, "Content-Type": "application/json"}

    def _configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    async def connect(self) -> ConnectionStatus:
        if not self._configured():
            return ConnectionStatus(
                status="disconnected",
                detail="Evolution API not configured. Set EVOLUTION_API_URL and EVOLUTION_API_KEY, then reconnect.",
                logs=[f"{now_iso()} — connect blocked: missing Evolution URL/key"],
            )
        logs = [f"{now_iso()} — creating/fetching instance '{self.instance}'"]
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                # Create instance (idempotent-ish; ignore already-exists errors)
                await c.post(
                    f"{self.base_url}/instance/create",
                    headers=self._headers(),
                    json={"instanceName": self.instance, "qrcode": True, "integration": "WHATSAPP-BAILEYS"},
                )
                logs.append(f"{now_iso()} — requesting QR / connect")
                r = await c.get(f"{self.base_url}/instance/connect/{self.instance}", headers=self._headers())
                data = r.json() if r.content else {}
            qr = data.get("base64") or (data.get("qrcode") or {}).get("base64")
            return ConnectionStatus(
                status="connecting" if qr else "disconnected",
                qr_code=qr,
                detail="Scan this QR code with WhatsApp → Linked Devices",
                logs=logs + [f"{now_iso()} — QR generated" if qr else f"{now_iso()} — no QR returned"],
            )
        except Exception as e:  # noqa
            return ConnectionStatus(status="error", detail=f"Evolution connect failed: {e}", logs=logs)

    async def disconnect(self) -> ConnectionStatus:
        if self._configured():
            try:
                async with httpx.AsyncClient(timeout=20) as c:
                    await c.delete(f"{self.base_url}/instance/logout/{self.instance}", headers=self._headers())
            except Exception:  # noqa
                pass
        return ConnectionStatus(status="disconnected", detail="Instance logged out",
                                logs=[f"{now_iso()} — disconnected"])

    async def send_message(self, to_phone: str, text: str) -> bool:
        if not self._configured():
            return False
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.post(
                    f"{self.base_url}/message/sendText/{self.instance}",
                    headers=self._headers(),
                    json={"number": to_phone, "text": text},
                )
                return r.status_code < 300
        except Exception:  # noqa
            return False

    async def get_connection_status(self) -> ConnectionStatus:
        if not self._configured():
            return ConnectionStatus(status="disconnected", detail="Evolution API not configured")
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.get(f"{self.base_url}/instance/connectionState/{self.instance}", headers=self._headers())
                data = r.json() if r.content else {}
            state = ((data.get("instance") or {}).get("state")) or data.get("state") or "disconnected"
            mapped = {"open": "connected", "connecting": "connecting", "close": "disconnected"}.get(state, state)
            return ConnectionStatus(status=mapped, last_connected_at=now_iso() if mapped == "connected" else None)
        except Exception as e:  # noqa
            return ConnectionStatus(status="error", detail=str(e))

    async def get_qr_code(self) -> ConnectionStatus:
        return await self.connect()
