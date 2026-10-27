import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from bson import ObjectId

from database import get_database
from services.yandex_rasp_service import yandex_service
from routers.auth import require_role

logger = logging.getLogger("transport_severa.sync")
router = APIRouter(prefix="/sync", tags=["Синхронизация"])

# Коды населённых пунктов Яндекс.Расписаний (settlement), не коды станций s...
# Поиск по станциям часто отвечает 404 / пустым segments.
SETTLEMENT_CODES = {
    "сыктывкар": "c19",
    "ухта": "c10943",
    "усинск": "c10940",
    "воркута": "c10931",
    "печора": "c10938",
}

DEFAULT_ROUTES = [
    {"from": "c19", "to": "c10943", "from_city": "Сыктывкар", "to_city": "Ухта"},
    {"from": "c19", "to": "c10940", "from_city": "Сыктывкар", "to_city": "Усинск"},
    {"from": "c19", "to": "c10931", "from_city": "Сыктывкар", "to_city": "Воркута"},
    {"from": "c19", "to": "c10938", "from_city": "Сыктывкар", "to_city": "Печора"},
]

HUB_CITY = "сыктывкар"


def _parse_yandex_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed

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
        # Пары городов Коми по кодам населённых пунктов. Коды станций (s...) сюда не тащим —
        # Яндекс на них часто отдаёт 404.
        if db_obj.is_connected:
            stations = await db_obj.db.stations.find({"is_active": True}).to_list(length=100)
            cities = []
            for station in stations:
                city_name = (station.get("city") or "").strip()
                city_key = city_name.lower()
                if city_name and city_key not in {c.lower() for c in cities}:
                    cities.append(city_name)

            hub_city = next((c for c in cities if HUB_CITY in c.lower()), "Сыктывкар")
            hub_code = SETTLEMENT_CODES.get(hub_city.lower()) or SETTLEMENT_CODES[HUB_CITY]
            for city_name in cities:
                city_key = city_name.lower()
                if HUB_CITY in city_key:
                    continue
                dest_code = SETTLEMENT_CODES.get(city_key)
                if dest_code:
                    routes_to_sync.append({
                        "from": hub_code,
                        "to": dest_code,
                        "from_city": hub_city,
                        "to_city": city_name,
                    })

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
            if not seg.get("departure") or not seg.get("arrival"):
                continue
            try:
                departure_planned = _parse_yandex_datetime(seg["departure"])
                arrival_planned = _parse_yandex_datetime(seg["arrival"])
            except (TypeError, ValueError):
                logger.warning("Пропущен сегмент с некорректной датой: %s", seg.get("departure"))
                continue

            thread = seg.get("thread", {})
            yandex_transport = thread.get("transport_type")
            if yandex_transport not in {"plane", "bus"}:
                continue
            transport_type = "PLANE" if yandex_transport == "plane" else "BUS"
            
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
                    "departure_planned": departure_planned,
                    "arrival_planned": arrival_planned,
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
