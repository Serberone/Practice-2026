import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from bson import ObjectId

from database import get_database
from services.yandex_rasp_service import yandex_service
from routers.auth import require_role

logger = logging.getLogger("transport_severa.sync")
router = APIRouter(prefix="/sync", tags=["Синхронизация"])

# Базовые маршрутные пары Республики Коми (Сыктывкар — города республики)
DEFAULT_ROUTES = [
    {"from": "c19", "to": "c10943", "from_city": "Сыктывкар", "to_city": "Ухта"},
    {"from": "c19", "to": "c10940", "from_city": "Сыктывкар", "to_city": "Усинск"},
    {"from": "c19", "to": "c10931", "from_city": "Сыктывкар", "to_city": "Воркута"},
    {"from": "c19", "to": "c10938", "from_city": "Сыктывкар", "to_city": "Печора"},
]

@router.post("/yandex")
async def sync_yandex_schedule(
    from_code: str = Query(None, description="Код пункта отправления (например, c19)"),
    to_code: str = Query(None, description="Код пункта назначения (например, c10943)"),
    date_str: str = Query(None, description="Дата в формате YYYY-MM-DD"),
    current_user: dict = Depends(require_role(["ADMIN", "DISPATCHER"]))
):
    """
    Синхронизирует рейсы из API Яндекс.Расписаний.
    Если коды не переданы, синхронизирует основные направления Коми из базы или пресета.
    """
    db_obj = get_database()
    today = date_str or datetime.utcnow().strftime("%Y-%m-%d")
    
    # 1. Формируем список маршрутов для синхронизации
    routes_to_sync = []
    
    if from_code and to_code:
        routes_to_sync.append({"from": from_code, "to": to_code})
    else:
        # Если параметры не заданы вручную — получаем станции из БД, у которых есть yandex_code
        if db_obj.is_connected:
            stations = await db_obj.db.stations.find(
                {"is_active": True, "yandex_code": {"$ne": None}}
            ).to_list(length=100)
            
            # Ищем хаб (Сыктывкар) и строим маршруты к остальным станциям
            hub = next((s for s in stations if "сыктывкар" in s.get("city", "").lower()), None)
            if hub:
                for target in stations:
                    if target.get("yandex_code") != hub.get("yandex_code"):
                        routes_to_sync.append({
                            "from": hub["yandex_code"],
                            "to": target["yandex_code"],
                            "from_city": hub.get("city"),
                            "to_city": target.get("city")
                        })
        
        # Если база пустая или станций нет, используем дефолтные направления по Коми
        if not routes_to_sync:
            routes_to_sync = DEFAULT_ROUTES

    total_synced_trips = 0
    synced_data = []

    # 2. Опрашиваем Яндекс по каждому маршруту
    for route in routes_to_sync:
        res = await yandex_service.get_schedule_between_stations(
            from_code=route["from"],
            to_code=route["to"],
            date_str=today
        )
        
        segments = res.get("segments", [])
        synced_data.append({
            "route": f"{route.get('from_city', route['from'])} -> {route.get('to_city', route['to'])}",
            "segments_count": len(segments),
            "search": res.get("search", {})
        })

        # 3. Сохраняем сегменты в коллекцию рейсов (trips)
        for seg in segments:
            thread = seg.get("thread", {})
            transport_type = "PLANE" if thread.get("transport_type") == "plane" else "BUS"
            
            trip_doc = {
                "trip_number": thread.get("number") or "Б/Н",
                "transport_type": transport_type,
                "carrier": {
                    "name": thread.get("carrier", {}).get("title", "Региональный перевозчик"),
                    "phone": None
                },
                "route": {
                    "origin": {
                        "city": res.get("search", {}).get("from", {}).get("title", route.get("from_city", "")),
                        "name": seg.get("from", {}).get("title", "Автовокзал / Аэропорт")
                    },
                    "destination": {
                        "city": res.get("search", {}).get("to", {}).get("title", route.get("to_city", "")),
                        "name": seg.get("to", {}).get("title", "Автовокзал / Аэропорт")
                    }
                },
                "schedule": {
                    "departure_planned": datetime.fromisoformat(seg["departure"]),
                    "arrival_planned": datetime.fromisoformat(seg["arrival"]),
                    "departure_estimated": None,
                    "arrival_estimated": None
                },
                "status": "SCHEDULED",
                "display_flags": {
                    "is_hidden": False,
                    "requires_dispatcher_review": False,
                    "manual_override": False
                },
                "source": "YANDEX_RASP",
                "last_synced_at": datetime.utcnow()
            }

            if db_obj.is_connected:
                # Обновляем или вставляем рейс, чтобы не плодить дубликаты
                await db_obj.db.trips.update_one(
                    {
                        "trip_number": trip_doc["trip_number"],
                        "schedule.departure_planned": trip_doc["schedule"]["departure_planned"]
                    },
                    {"$set": trip_doc},
                    upsert=True
                )
            else:
                trip_id = f"{trip_doc['trip_number']}_{today}"
                trip_doc["id"] = trip_id
                db_obj._fallback_store.setdefault("trips", {})[trip_id] = trip_doc

            total_synced_trips += 1

    return {
        "message": f"Синхронизация завершена. Добавлено/обновлено рейсов: {total_synced_trips}",
        "routes_processed": len(routes_to_sync),
        "details": synced_data
    }
