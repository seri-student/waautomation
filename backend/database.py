import os
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Projection to strip Mongo's internal _id from every read
NO_ID = {"_id": 0}


def clean(doc):
    """Return a JSON-safe copy of a Mongo document (drops the internal _id)."""
    if not doc:
        return doc
    return {k: v for k, v in doc.items() if k != "_id"}


def clean_list(docs):
    return [clean(d) for d in docs]


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def next_order_number(restaurant_id: str) -> int:
    """Atomic per-restaurant order counter. First order returns 1001."""
    key = f"orders:{restaurant_id}"
    doc = await db.counters.find_one_and_update(
        {"id": key},
        {"$inc": {"seq": 1}, "$setOnInsert": {"id": key}},
        upsert=True,
        return_document=True,
    )
    seq = doc["seq"]
    if seq < 1001:
        # ensure we start at 1001
        await db.counters.update_one({"id": key}, {"$set": {"seq": 1001}})
        return 1001
    return seq
