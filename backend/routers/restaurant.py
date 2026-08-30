from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import db, NO_ID, now_iso, clean
from auth import get_current_restaurant_id

router = APIRouter(prefix="/api/restaurant", tags=["restaurant"])


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None
    description: Optional[str] = None
    whatsapp_number: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    opening_hours: Optional[str] = None
    delivery_areas: Optional[str] = None
    delivery_fee: Optional[float] = None
    min_order: Optional[float] = None
    prep_time_min: Optional[int] = None
    prep_time_max: Optional[int] = None
    delivery_time_min: Optional[int] = None
    delivery_time_max: Optional[int] = None
    currency: Optional[str] = None
    ai_greeting: Optional[str] = None


class AISettingsUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    personality: Optional[str] = None
    language_behavior: Optional[str] = None
    upsell_enabled: Optional[bool] = None
    max_upsell_attempts: Optional[int] = None
    human_handoff_enabled: Optional[bool] = None


@router.get("")
async def get_restaurant(rid: str = Depends(get_current_restaurant_id)):
    return clean(await db.restaurants.find_one({"id": rid}, NO_ID))


@router.put("")
async def update_restaurant(body: RestaurantUpdate, rid: str = Depends(get_current_restaurant_id)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await db.restaurants.update_one({"id": rid}, {"$set": updates})
    return clean(await db.restaurants.find_one({"id": rid}, NO_ID))


@router.get("/ai-settings")
async def get_ai_settings(rid: str = Depends(get_current_restaurant_id)):
    return clean(await db.ai_settings.find_one({"restaurant_id": rid}, NO_ID))


@router.put("/ai-settings")
async def update_ai_settings(body: AISettingsUpdate, rid: str = Depends(get_current_restaurant_id)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await db.ai_settings.update_one({"restaurant_id": rid}, {"$set": updates})
    return clean(await db.ai_settings.find_one({"restaurant_id": rid}, NO_ID))
