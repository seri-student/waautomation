import asyncio
import json
from typing import Dict, Set


class EventBus:
    """In-memory per-restaurant pub/sub for Server-Sent Events."""

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}

    async def subscribe(self, restaurant_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(restaurant_id, set()).add(q)
        return q

    def unsubscribe(self, restaurant_id: str, q: asyncio.Queue):
        subs = self._subscribers.get(restaurant_id)
        if subs and q in subs:
            subs.discard(q)
            if not subs:
                self._subscribers.pop(restaurant_id, None)

    async def publish(self, restaurant_id: str, event_type: str, data: dict):
        subs = self._subscribers.get(restaurant_id)
        if not subs:
            return
        payload = json.dumps({"type": event_type, "data": data})
        for q in list(subs):
            await q.put(payload)


bus = EventBus()
