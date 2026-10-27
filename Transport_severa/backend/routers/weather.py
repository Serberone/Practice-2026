import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from database import get_database
from models import WeatherMetrics, WeatherLog
from routers.auth import require_role
from services.weather_service import evaluate_weather_impact, get_latest_weather_reports

logger = logging.getLogger("transport_severa.weather_router")
router = APIRouter(prefix="/weather", tags=["Метеоданные"])

@router.get("/latest")
async def get_latest_weather(city: Optional[str] = None):
    """
    Актуальная погода по станциям Коми из Open-Meteo.
    Если API недоступен, по каждому городу возвращается ok=false и error="ошибка".
    """
    return await get_latest_weather_reports(city)

@router.post("/ingest")
async def ingest_weather_report(
    city: str,
    metrics: WeatherMetrics,
    current_user: dict = Depends(require_role(["DISPATCHER", "ADMIN"]))
):
    """
    Ingest a new weather observation and automatically calculate impact on flights and buses.
    """
    db_obj = get_database()
    
    impact_plane, alert_level, flight_critical, bus_critical = evaluate_weather_impact(metrics, "PLANE")
    
    log_doc = {
        "city": city,
        "timestamp": datetime.utcnow(),
        "metrics": metrics.dict(),
        "alert_level": alert_level,
        "flight_critical": flight_critical,
        "bus_critical": bus_critical
    }

    if db_obj.is_connected:
        res = await db_obj.db.weather_logs.insert_one(log_doc)
        log_doc["id"] = str(res.inserted_id)
        del log_doc["_id"]
    else:
        wid = str(ObjectId())
        log_doc["id"] = wid
        if "weather" not in db_obj._fallback_store:
            db_obj._fallback_store["weather"] = {}
        db_obj._fallback_store["weather"][city] = log_doc

    return {
        "message": "Метеосводка успешно принята",
        "weather": log_doc,
        "evaluation": {
            "alert_level": alert_level,
            "flight_critical": flight_critical,
            "bus_critical": bus_critical,
            "impact_reason": impact_plane.phenomenon
        }
    }
