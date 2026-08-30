import os
import logging
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from database import client
import seed
from routers import (auth, restaurant, menu, orders, customers, analytics,
                     whatsapp, conversations, simulator, webhooks, stream)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Restaurant Ordering SaaS")

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "AI Restaurant Ordering SaaS API", "status": "ok"}


@api_router.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(api_router)
app.include_router(auth.router)
app.include_router(restaurant.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(customers.router)
app.include_router(analytics.router)
app.include_router(whatsapp.router)
app.include_router(conversations.router)
app.include_router(simulator.router)
app.include_router(webhooks.router)
app.include_router(stream.router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    try:
        await seed.seed()
        logger.info("Demo data seeded / verified")
    except Exception as e:  # noqa
        logger.exception("Seeding failed: %s", e)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
