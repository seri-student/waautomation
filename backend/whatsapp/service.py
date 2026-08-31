"""Provider factory + high-level WhatsAppService.

The rest of the application only ever talks to WhatsAppService. It loads the
per-restaurant WhatsApp configuration, picks the right provider implementation,
and exposes provider-agnostic operations.
"""
from database import db, NO_ID
from .base import WhatsAppProvider, ConnectionStatus
from .simulator import SimulatorProvider
from .evolution import EvolutionApiProvider
from .meta import MetaCloudProvider
from .baileys import BaileysProvider

_PROVIDERS = {
    "simulator": SimulatorProvider,
    "evolution": EvolutionApiProvider,
    "meta": MetaCloudProvider,
    "baileys": BaileysProvider,
}


async def _load_config(restaurant_id: str) -> dict:
    conn = await db.whatsapp_connections.find_one({"restaurant_id": restaurant_id}, NO_ID)
    return conn or {"restaurant_id": restaurant_id, "provider": "simulator"}


async def get_whatsapp_provider(restaurant_id: str) -> WhatsAppProvider:
    config = await _load_config(restaurant_id)
    provider_name = config.get("provider", "simulator")
    cls = _PROVIDERS.get(provider_name, SimulatorProvider)
    return cls(restaurant_id, config)


class WhatsAppService:
    """Provider-agnostic facade used by the ordering engine and dashboard."""

    @staticmethod
    async def send_customer_message(restaurant_id: str, to_phone: str, text: str) -> bool:
        provider = await get_whatsapp_provider(restaurant_id)
        return await provider.send_message(to_phone, text)

    @staticmethod
    async def send_order_notification(restaurant_id: str, to_phone: str, text: str) -> bool:
        provider = await get_whatsapp_provider(restaurant_id)
        return await provider.send_message(to_phone, text)

    @staticmethod
    async def send_human_reply(restaurant_id: str, to_phone: str, text: str) -> bool:
        provider = await get_whatsapp_provider(restaurant_id)
        return await provider.send_message(to_phone, text)

    @staticmethod
    async def get_connection_status(restaurant_id: str) -> ConnectionStatus:
        provider = await get_whatsapp_provider(restaurant_id)
        return await provider.get_connection_status()


whatsapp_service = WhatsAppService()
