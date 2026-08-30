"""Simulator provider — an always-connected in-app test transport.

Outgoing messages are already persisted to the messages collection by the
conversation engine and rendered in the dashboard Simulator, so send is a
no-op here. This lets the entire ordering flow be tested end-to-end without
any external WhatsApp credentials.
"""
from database import now_iso
from .base import WhatsAppProvider, ConnectionStatus


class SimulatorProvider(WhatsAppProvider):
    name = "simulator"

    async def connect(self) -> ConnectionStatus:
        return await self.get_connection_status()

    async def disconnect(self) -> ConnectionStatus:
        return ConnectionStatus(status="disconnected", detail="Simulator stopped")

    async def send_message(self, to_phone: str, text: str) -> bool:
        # Delivery is handled by the dashboard Simulator reading the messages DB.
        return True

    async def get_connection_status(self) -> ConnectionStatus:
        return ConnectionStatus(
            status="connected",
            connected_number="Simulator",
            last_connected_at=now_iso(),
            detail="Built-in test simulator is always connected",
        )

    async def get_qr_code(self) -> ConnectionStatus:
        return ConnectionStatus(status="connected", detail="No QR needed for simulator")
