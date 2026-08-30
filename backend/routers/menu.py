from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from database import db, NO_ID, new_id, now_iso, clean, clean_list
from auth import get_current_restaurant_id

router = APIRouter(prefix="/api/menu", tags=["menu"])


class CategoryBody(BaseModel):
    name: str
    sort_order: Optional[int] = 99


class ItemBody(BaseModel):
    category_id: str
    name: str
    description: Optional[str] = ""
    price: float
    available: Optional[bool] = True
    image_url: Optional[str] = ""
    addon_item_ids: Optional[List[str]] = []


class ItemUpdate(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    available: Optional[bool] = None
    image_url: Optional[str] = None
    addon_item_ids: Optional[List[str]] = None


@router.get("")
async def get_menu(rid: str = Depends(get_current_restaurant_id)):
    cats = clean_list(await db.menu_categories.find({"restaurant_id": rid}, NO_ID).sort("sort_order", 1).to_list(200))
    items = clean_list(await db.menu_items.find({"restaurant_id": rid}, NO_ID).to_list(1000))
    return {"categories": cats, "items": items}


@router.post("/categories")
async def create_category(body: CategoryBody, rid: str = Depends(get_current_restaurant_id)):
    doc = {"id": new_id(), "restaurant_id": rid, "name": body.name,
           "sort_order": body.sort_order, "created_at": now_iso()}
    await db.menu_categories.insert_one({**doc})
    return clean(doc)


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, rid: str = Depends(get_current_restaurant_id)):
    await db.menu_categories.delete_one({"id": category_id, "restaurant_id": rid})
    await db.menu_items.delete_many({"category_id": category_id, "restaurant_id": rid})
    return {"ok": True}


@router.post("/items")
async def create_item(body: ItemBody, rid: str = Depends(get_current_restaurant_id)):
    doc = {"id": new_id(), "restaurant_id": rid, "category_id": body.category_id,
           "name": body.name, "description": body.description, "price": body.price,
           "available": body.available, "image_url": body.image_url,
           "addon_item_ids": body.addon_item_ids or [], "created_at": now_iso()}
    await db.menu_items.insert_one({**doc})
    return clean(doc)


@router.put("/items/{item_id}")
async def update_item(item_id: str, body: ItemUpdate, rid: str = Depends(get_current_restaurant_id)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await db.menu_items.update_one({"id": item_id, "restaurant_id": rid}, {"$set": updates})
    return clean(await db.menu_items.find_one({"id": item_id, "restaurant_id": rid}, NO_ID))


@router.delete("/items/{item_id}")
async def delete_item(item_id: str, rid: str = Depends(get_current_restaurant_id)):
    await db.menu_items.delete_one({"id": item_id, "restaurant_id": rid})
    return {"ok": True}
