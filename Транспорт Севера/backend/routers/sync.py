import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from config import settings
from database import get_database
from routers.auth import require_role
from services.yandex_rasp_service import yandex_service
from seed_data import seed_initial_data

logger = logging.getLogger("transport_severa.sync")
router = APIRouter(prefix="/sync", tags=["Синхронизация и интеграции"])

@router.get("/status")
async def get_sync_status():
    has_key = bool(settings.YANDEX_RASP_API_KEY and settings.YANDEX_RASP_API_KEY != "ВАШ_КЛЮЧ")
    db_obj = get_database()
    cached_count = 0
    if db_obj.is_connected:
        cached_count = await db_obj.db.yandex_cache.count_documents({})
    return {
        "yandex_key_configured": has_key,
        "daily_limit": 500,
        "cached_queries": cached_count,
        "database_connected": db_obj.is_connected,
        "timestamp": datetime.utcnow()
    }

@router.post("/yandex")
async def sync_with_yandex(
    from_code: str = "c19",  # Сыктывкар
    to_code: str = "c10935", # Усинск
    current_user: dict = Depends(require_role(["DISPATCHER", "ADMIN"]))
):
    """
    Triggers rate-limited sync with Yandex.Schedules API
    """
    logger.info(f"User {current_user.get('username')} requested Yandex Rasp sync {from_code} -> {to_code}")
    res = await yandex_service.get_schedule_between_stations(from_code, to_code)
    return {
        "message": "Данные успешно синхронизированы",
        "data": res
    }

@router.post("/seed")
async def trigger_seed(current_user: dict = Depends(require_role(["ADMIN"]))):
    """
    Populates database with realistic Komi Republic stations, carriers, and weather-impacted trips
    """
    await seed_initial_data()
    return {"message": "База данных успешно инициализирована тестовыми данными Республики Коми"}
