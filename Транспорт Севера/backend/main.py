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

# CORS Middleware (crucial for frontend hosted on Vercel/Netlify communicating with backend on Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(stations.router, prefix=settings.API_PREFIX)
app.include_router(carriers.router, prefix=settings.API_PREFIX)
app.include_router(trips.router, prefix=settings.API_PREFIX)
app.include_router(weather.router, prefix=settings.API_PREFIX)
app.include_router(subscriptions.router, prefix=settings.API_PREFIX)
app.include_router(notifications.router, prefix=settings.API_PREFIX)
app.include_router(audit.router, prefix=settings.API_PREFIX)
app.include_router(sync.router, prefix=settings.API_PREFIX)

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
