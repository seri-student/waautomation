"""Common WhatsApp provider interface + normalized message types.

Business logic must ONLY depend on these types and the abstract
WhatsAppProvider interface, never on Evolution or Meta specifics.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IncomingMessage:
    restaurant_id: str
    provider: str
    customer_phone: str
    message_id: str
    text: str
    timestamp: str
    customer_name: Optional[str] = None


@dataclass
class OutgoingMessage:
    to_phone: str
    text: str


@dataclass
class ConnectionStatus:
    status: str  # connected | connecting | disconnected | error
    connected_number: Optional[str] = None
    last_connected_at: Optional[str] = None
    qr_code: Optional[str] = None  # base64 data URL when connecting
    detail: Optional[str] = None
    logs: list = field(default_factory=list)


class WhatsAppProvider(ABC):
    """Interface every provider implementation must satisfy."""

    name: str = "base"

    def __init__(self, restaurant_id: str, config: dict):
        self.restaurant_id = restaurant_id
        self.config = config or {}

    @abstractmethod
    async def connect(self) -> ConnectionStatus:
        ...

    @abstractmethod
    async def disconnect(self) -> ConnectionStatus:
        ...

    @abstractmethod
    async def send_message(self, to_phone: str, text: str) -> bool:
        ...

    @abstractmethod
    async def get_connection_status(self) -> ConnectionStatus:
        ...

    @abstractmethod
    async def get_qr_code(self) -> ConnectionStatus:
        ...

    async def send_image(self, to_phone: str, url: str, caption: str = "") -> bool:
        return await self.send_message(to_phone, caption or url)

    async def send_document(self, to_phone: str, url: str, filename: str = "") -> bool:
        return await self.send_message(to_phone, filename or url)
