import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import connect_to_mongo, close_mongo_connection
from seed_data import seed_initial_data
from routers import (
    auth,
    stations,
    carriers,
    trips,
    weather,
    subscriptions,
    notifications,
    audit,
    sync
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("transport_severa")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Transport Severa API...")
    await connect_to_mongo()
    # Seed initial demo data (stations, carriers, weather, initial trips)
    await seed_initial_data()
    yield
    logger.info("Shutting down Transport Severa API...")
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Онлайн-табло междугородних автобусов и авиарейсов с интеграцией метеоданных для Республики Коми",
    lifespan=lifespan
)

# CORS: токен в Authorization, куки не нужны. allow_credentials + ["*"] браузер режет.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_ROUTERS = (
    auth.router,
    stations.router,
    carriers.router,
    trips.router,
    weather.router,
    subscriptions.router,
    notifications.router,
    audit.router,
    sync.router,
)

# Каноничные пути: /api/auth/login, /api/trips, ...
for api_router in API_ROUTERS:
    app.include_router(api_router, prefix=settings.API_PREFIX)

# Совместимость с фронтом, у которого VITE_API_BASE_URL без суффикса /api
# (иначе POST /auth/login даёт 404).
for api_router in API_ROUTERS:
    app.include_router(api_router, include_in_schema=False)

@app.get("/")
async def root():
    return {
        "service": "Транспорт Севера — Онлайн-табло Республики Коми",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX
    }

@app.get("/health")
async def health_check():
    from database import get_database
    db_obj = get_database()
    return {
        "status": "healthy",
        "database_connected": db_obj.is_connected,
        "mode": "mongodb" if db_obj.is_connected else "embedded_fallback"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
