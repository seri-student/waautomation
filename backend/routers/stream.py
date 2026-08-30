"""Server-Sent Events stream for real-time dashboard updates."""
import os
import asyncio
import jwt
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

from database import db, NO_ID
from events import bus

router = APIRouter(prefix="/api", tags=["stream"])


async def _restaurant_from_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
        user = await db.users.find_one({"id": payload.get("sub")}, NO_ID)
        return user.get("restaurant_id") if user else None
    except Exception:
        return None


@router.get("/stream")
async def stream(request: Request, token: str = ""):
    restaurant_id = await _restaurant_from_token(token)
    if not restaurant_id:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    async def event_generator():
        q = await bus.subscribe(restaurant_id)
        try:
            yield "event: ready\ndata: connected\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=20)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            bus.unsubscribe(restaurant_id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                                      "Connection": "keep-alive"})
