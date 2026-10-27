import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, Depends

from config import settings
from database import get_database
from seed_data import seed_initial_data
from services.yandex_rasp_service import yandex_service
from routers.auth import require_role

logger = logging.getLogger("transport_severa.sync")
router = APIRouter(prefix="/sync", tags=["Синхронизация"])

SCHEDULE_EVENTS = ("departure", "arrival")
DEFAULT_LEG_DURATION = timedelta(hours=2)
TITLE_SEPARATORS = (" — ", " – ", " - ")

# Если в БД ещё нет станций — те же 4 города Коми, что в seed_data.
DEFAULT_STATIONS = [
    {"id": "st_scw_air", "name": "Международный аэропорт Сыктывкар им. П.А. Истомина", "city": "Сыктывкар", "yandex_code": "s9600378"},
    {"id": "st_scw_bus", "name": "Автовокзал Сыктывкар (ул. Морозова, 202)", "city": "Сыктывкар", "yandex_code": "s9637101"},
    {"id": "st_usk_air", "name": "Аэропорт Усинск", "city": "Усинск", "yandex_code": "s9600382"},
    {"id": "st_usk_bus", "name": "Автостанция Усинск (ул. Заводская)", "city": "Усинск", "yandex_code": "s9637105"},
    {"id": "st_uct_air", "name": "Аэропорт Ухта", "city": "Ухта", "yandex_code": "s9600380"},
    {"id": "st_uct_bus", "name": "Автовокзал Ухта (ул. Октябрьская, 24)", "city": "Ухта", "yandex_code": "s9637103"},
    {"id": "st_peo_air", "name": "Аэропорт Печора", "city": "Печора", "yandex_code": "s9600381"},
    {"id": "st_peo_bus", "name": "Автостанция Печора (Привокзальная пл.)", "city": "Печора", "yandex_code": "s9637107"},
]


def _parse_yandex_datetime(value: str, date_str: str) -> datetime:
    raw = str(value).strip().replace("Z", "+00:00")
    if "T" in raw or (" " in raw and len(raw) > 10):
        parsed = datetime.fromisoformat(raw.replace(" ", "T", 1))
    else:
        if len(raw) == 5:
            raw = f"{raw}:00"
        parsed = datetime.fromisoformat(f"{date_str}T{raw}")
    if parsed.tzinfo is not None:
        return parsed.replace(tzinfo=None)
    return parsed


def _city_from_place(place: str) -> str:
    return (place.split("(")[0].strip() or place).strip()


def _split_thread_title(title: str):
    if not title:
        return None, None
    for separator in TITLE_SEPARATORS:
        if separator in title:
            left, right = title.split(separator, 1)
            return left.strip(), right.strip()
    return None, None


def _remote_place(title: str, local_city: str, event: str) -> str:
    left, right = _split_thread_title(title)
    local_key = (local_city or "").lower()
    if event == "arrival":
        if left and local_key and local_key in left.lower() and right:
            return right
        return left or right or "Неизвестный пункт"
    if right and local_key and local_key in right.lower() and left:
        return left
    return right or left or "Неизвестный пункт"


def _carrier_name(thread: dict) -> str:
    carrier = thread.get("carrier") or {}
    if isinstance(carrier, str):
        return carrier
    return carrier.get("title") or "Региональный перевозчик"

async def _load_sync_stations(db_obj):
    stations = []
    if db_obj.is_connected:
        stations = await db_obj.db.stations.find(
            {"is_active": True, "yandex_code": {"$nin": [None, ""]}}
        ).to_list(length=50)
    else:
        stations = [
            s for s in db_obj._fallback_store.get("stations", {}).values()
            if s.get("is_active", True) and s.get("yandex_code")
        ]
    if not stations:
        stations = DEFAULT_STATIONS
    return stations


async def _upsert_trip(db_obj, trip_doc: dict, today: str) -> bool:
    trip_filter = {
        "trip_number": trip_doc["trip_number"],
        "schedule.departure_planned": trip_doc["schedule"]["departure_planned"],
    }
    if db_obj.is_connected:
        existing = await db_obj.db.trips.find_one(trip_filter)
        if existing and existing.get("display_flags", {}).get("manual_override"):
            await db_obj.db.trips.update_one(
                trip_filter,
                {"$set": {"last_synced_at": trip_doc["last_synced_at"]}},
            )
            return True
        await db_obj.db.trips.update_one(trip_filter, {"$set": trip_doc}, upsert=True)
        return True

    trip_id = f"{trip_doc['trip_number']}_{today}_{trip_doc['schedule']['departure_planned']}"
    trip_doc["id"] = trip_id
    store = db_obj._fallback_store.setdefault("trips", {})
    existing = store.get(trip_id)
    if existing and existing.get("display_flags", {}).get("manual_override"):
        existing["last_synced_at"] = trip_doc["last_synced_at"]
        return True
    store[trip_id] = trip_doc
    return True


def _trip_from_schedule_item(item: dict, station: dict, event: str, date_str: str):
    thread = item.get("thread") or {}
    yandex_transport = thread.get("transport_type")
    if yandex_transport not in {"plane", "bus"}:
        return None

    departure_raw = item.get("departure")
    arrival_raw = item.get("arrival")
    if event == "departure" and not departure_raw:
        return None
    if event == "arrival" and not arrival_raw and not departure_raw:
        return None

    try:
        if departure_raw:
            departure_planned = _parse_yandex_datetime(departure_raw, date_str)
        else:
            departure_planned = _parse_yandex_datetime(arrival_raw, date_str) - DEFAULT_LEG_DURATION
        if arrival_raw:
            arrival_planned = _parse_yandex_datetime(arrival_raw, date_str)
        else:
            arrival_planned = departure_planned + DEFAULT_LEG_DURATION
    except (TypeError, ValueError):
        logger.warning("Пропущен рейс с некорректной датой: %s / %s", departure_raw, arrival_raw)
        return None

    if arrival_planned <= departure_planned:
        arrival_planned = departure_planned + DEFAULT_LEG_DURATION

    local_place = {
        "station_id": station.get("id"),
        "city": station.get("city") or "",
        "name": station.get("name") or station.get("city") or "Станция",
    }
    remote_title = _remote_place(thread.get("title") or "", local_place["city"], event)
    remote_place = {
        "station_id": None,
        "city": _city_from_place(remote_title),
        "name": remote_title,
    }

    origin = local_place if event == "departure" else remote_place
    destination = remote_place if event == "departure" else local_place
    transport_type = "PLANE" if yandex_transport == "plane" else "BUS"

    return {
        "trip_number": thread.get("number") or "Б/Н",
        "transport_type": transport_type,
        "carrier": {"name": _carrier_name(thread), "phone": None},
        "route": {"origin": origin, "destination": destination},
        "schedule": {
            "departure_planned": departure_planned,
            "arrival_planned": arrival_planned,
            "departure_estimated": None,
            "arrival_estimated": None,
        },
        "status": "SCHEDULED",
        "gate_or_platform": item.get("platform") or item.get("terminal"),
        "display_flags": {
            "is_hidden": False,
            "requires_dispatcher_review": False,
            "manual_override": False,
        },
        "source": "YANDEX_RASP",
        "last_synced_at": datetime.utcnow(),
    }


@router.post("/yandex")
async def sync_yandex_schedule(
    from_code: str = Query(None, description="Код пункта отправления (ручной поиск пары)"),
    to_code: str = Query(None, description="Код пункта назначения (ручной поиск пары)"),
    date_str: str = Query(None, description="Дата в формате YYYY-MM-DD"),
    current_user: dict = Depends(require_role(["ADMIN", "DISPATCHER"]))
):
    """
    По умолчанию тянет все рейсы plane/bus по станциям 4 городов Коми
    (отправления и прибытия, любые направления, включая Москву).
    from_code+to_code оставляют точечный поиск пары.
    """
    db_obj = get_database()
    today = date_str or datetime.utcnow().strftime("%Y-%m-%d")
    total_synced_trips = 0
    synced_data = []

    if from_code and to_code:
        res = await yandex_service.get_schedule_between_stations(
            from_code=from_code,
            to_code=to_code,
            date_str=today,
        )
        segments = res.get("segments") or []
        synced_data.append({
            "route": f"{from_code} -> {to_code}",
            "mode": "search_pair",
            "segments_count": len(segments),
            "search": res.get("search", {}),
            "error": res.get("error"),
        })
        for seg in segments:
            station = {
                "id": None,
                "city": res.get("search", {}).get("from", {}).get("title", ""),
                "name": (seg.get("from") or {}).get("title") or "Станция",
            }
            fake_item = {
                **seg,
                "thread": {
                    **(seg.get("thread") or {}),
                    "title": (seg.get("thread") or {}).get("title")
                    or f"{station['city']} — {(res.get('search', {}).get('to') or {}).get('title', '')}",
                },
            }
            trip_doc = _trip_from_schedule_item(fake_item, station, "departure", today)
            if not trip_doc:
                continue
            dest_title = (res.get("search", {}).get("to") or {}).get("title") or trip_doc["route"]["destination"]["city"]
            trip_doc["route"]["destination"] = {
                "station_id": None,
                "city": dest_title,
                "name": (seg.get("to") or {}).get("title") or dest_title,
            }
            if await _upsert_trip(db_obj, trip_doc, today):
                total_synced_trips += 1
        return {
            "message": f"Синхронизация завершена. Добавлено/обновлено рейсов: {total_synced_trips}",
            "stations_processed": 0,
            "routes_processed": 1,
            "details": synced_data,
        }

    stations = await _load_sync_stations(db_obj)
    for station in stations:
        station_code = station.get("yandex_code")
        station_label = f"{station.get('city')} / {station.get('name')}"
        for event in SCHEDULE_EVENTS:
            res = await yandex_service.get_station_schedule(
                station_code=station_code,
                date_str=today,
                event=event,
            )
            items = res.get("schedule") or []
            saved_here = 0
            for item in items:
                trip_doc = _trip_from_schedule_item(item, station, event, today)
                if not trip_doc:
                    continue
                if await _upsert_trip(db_obj, trip_doc, today):
                    total_synced_trips += 1
                    saved_here += 1
            synced_data.append({
                "route": f"{station_label} [{event}]",
                "mode": "station_schedule",
                "yandex_code": station_code,
                "segments_count": len(items),
                "saved": saved_here,
                "error": res.get("error"),
            })

    return {
        "message": f"Синхронизация завершена. Добавлено/обновлено рейсов: {total_synced_trips}",
        "stations_processed": len(stations),
        "routes_processed": len(synced_data),
        "details": synced_data,
    }


@router.get("/status")
async def get_sync_status(current_user: dict = Depends(require_role(["ADMIN", "DISPATCHER"]))):
    db_obj = get_database()
    cached_queries = 0
    if db_obj.is_connected:
        cached_queries = await db_obj.db.yandex_cache.count_documents({})
    else:
        cached_queries = len(db_obj._fallback_store.get("yandex_cache", {}))

    api_key = settings.YANDEX_RASP_API_KEY or ""
    return {
        "yandex_key_configured": bool(api_key.strip()) and api_key != "ВАШ_КЛЮЧ",
        "cached_queries": cached_queries,
        "database_connected": db_obj.is_connected,
    }


@router.post("/seed")
async def seed_demo_data(current_user: dict = Depends(require_role(["ADMIN"]))):
    await seed_initial_data()
    return {"message": "Демо-данные Республики Коми загружены"}
