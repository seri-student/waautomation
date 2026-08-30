from datetime import datetime, timezone, timedelta
from collections import defaultdict
from fastapi import APIRouter, Depends

from database import db, NO_ID
from auth import get_current_restaurant_id

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _parse(dt: str):
    try:
        return datetime.fromisoformat(dt)
    except Exception:
        return None


@router.get("/summary")
async def summary(rid: str = Depends(get_current_restaurant_id)):
    orders = await db.orders.find({"restaurant_id": rid}, NO_ID).to_list(2000)
    now = datetime.now(timezone.utc)
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    today_orders = today_sales = week_sales = month_sales = 0.0
    today_count = pending = completed = 0
    total_sales = 0.0
    counted = 0
    item_counts = defaultdict(int)
    item_revenue = defaultdict(float)

    for o in orders:
        created = _parse(o.get("created_at", "")) or now
        if o.get("status") != "Cancelled":
            total_sales += o.get("total", 0)
            counted += 1
        if created.date() == today and o.get("status") != "Cancelled":
            today_count += 1
            today_sales += o.get("total", 0)
        if created >= week_ago and o.get("status") != "Cancelled":
            week_sales += o.get("total", 0)
        if created >= month_ago and o.get("status") != "Cancelled":
            month_sales += o.get("total", 0)
        if o.get("status") in ("New", "Confirmed", "Preparing", "Ready", "Out for Delivery"):
            pending += 1
        if o.get("status") == "Delivered":
            completed += 1
        for it in o.get("items", []):
            item_counts[it["name"]] += it.get("qty", 0)
            item_revenue[it["name"]] += it.get("line_total", 0)

    top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    aov = round(total_sales / counted, 0) if counted else 0

    return {
        "today_orders": today_count,
        "today_sales": round(today_sales, 0),
        "week_sales": round(week_sales, 0),
        "month_sales": round(month_sales, 0),
        "pending_orders": pending,
        "completed_orders": completed,
        "average_order_value": aov,
        "total_orders": len(orders),
        "top_items": [{"name": n, "qty": q, "revenue": round(item_revenue[n], 0)} for n, q in top_items],
    }
