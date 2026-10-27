import logging
from datetime import datetime, timedelta
import httpx
from config import settings
from database import get_database

logger = logging.getLogger("transport_severa.yandex_rasp")

CACHE_TTL = timedelta(minutes=30)
HTTP_TIMEOUT_SECONDS = 20.0
PAGE_LIMIT = 100
MAX_OFFSET = 100
TRANSPORT_TYPES = "plane,bus"


class YandexRaspService:
    def __init__(self):
        self.api_key = settings.YANDEX_RASP_API_KEY
        self.base_url = settings.YANDEX_RASP_BASE_URL

    def _has_api_key(self) -> bool:
        return bool(self.api_key) and self.api_key != "ВАШ_КЛЮЧ"

    async def _read_cache(self, cache_key: str):
        db_obj = get_database()
        now = datetime.utcnow()
        if db_obj.is_connected:
            cached = await db_obj.db.yandex_cache.find_one({"cache_key": cache_key})
            if cached and cached.get("expires_at", datetime.min) > now:
                logger.info(f"Serving Yandex Rasp data from MongoDB cache for {cache_key}")
                return cached.get("data", {})
            return None
        cached = db_obj._fallback_store.get("yandex_cache", {}).get(cache_key)
        if cached and cached.get("expires_at", datetime.min) > now:
            return cached.get("data", {})
        return None

    async def _write_cache(self, cache_key: str, data: dict):
        db_obj = get_database()
        payload = {
            "cache_key": cache_key,
            "data": data,
            "cached_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + CACHE_TTL,
        }
        if db_obj.is_connected:
            await db_obj.db.yandex_cache.update_one(
                {"cache_key": cache_key},
                {"$set": payload},
                upsert=True,
            )
            return
        db_obj._fallback_store.setdefault("yandex_cache", {})[cache_key] = payload

    async def _get_json(self, path: str, params: dict, cache_key: str) -> dict:
        cached = await self._read_cache(cache_key)
        if cached is not None:
            return cached

        if not self._has_api_key():
            return {}

        request_params = {"apikey": self.api_key, "format": "json", "lang": "ru_RU", **params}
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
                resp = await client.get(f"{self.base_url}{path}", params=request_params)
                if resp.status_code == 200:
                    data = resp.json()
                    await self._write_cache(cache_key, data)
                    return data
                logger.warning("Yandex Rasp API %s returned %s: %s", path, resp.status_code, resp.text[:500])
                return {"error": {"http_status": resp.status_code, "body": resp.text[:500]}}
        except Exception as exc:
            logger.error("Error calling Yandex Rasp API %s: %s", path, exc)
            return {"error": {"message": str(exc)}}

    async def get_station_schedule(
        self,
        station_code: str,
        date_str: str = None,
        event: str = "departure",
    ) -> dict:
        """
        Все рейсы по станции (любые направления), endpoint /schedule/.
        Не требует пункта назначения — так находятся Сыктывкар—Москва и остальные.
        """
        today = date_str or datetime.utcnow().strftime("%Y-%m-%d")
        if not self._has_api_key():
            logger.info("Yandex Rasp API key not provided. Returning demo station schedule.")
            return self._get_fallback_station_schedule(station_code, today, event)

        merged_items = []
        first_page = None
        offset = 0
        while offset <= MAX_OFFSET:
            cache_key = f"schedule_{station_code}_{today}_{event}_{offset}"
            page = await self._get_json(
                "/schedule/",
                {
                    "station": station_code,
                    "date": today,
                    "transport_types": TRANSPORT_TYPES,
                    "event": event,
                    "limit": PAGE_LIMIT,
                    "offset": offset,
                },
                cache_key,
            )
            if first_page is None:
                first_page = page
            if page.get("error"):
                break
            items = page.get("schedule") or []
            intervals = page.get("interval_schedule") or []
            merged_items.extend(items)
            merged_items.extend(intervals)
            total = (page.get("pagination") or {}).get("total") or len(items)
            if offset + PAGE_LIMIT >= total or not items:
                break
            offset += PAGE_LIMIT

        result = first_page or {}
        result["schedule"] = merged_items
        result["interval_schedule"] = []
        return result

    async def get_schedule_between_stations(
        self,
        from_code: str,
        to_code: str,
        date_str: str = None
    ) -> dict:
        """Поиск конкретной пары пунктов (ручной запрос с from/to)."""
        today = date_str or datetime.utcnow().strftime("%Y-%m-%d")
        if not self._has_api_key():
            logger.info("Yandex Rasp API key not provided or empty. Returning structured demo schedule.")
            return self._get_fallback_schedule(from_code, to_code)

        cache_key = f"search_{from_code}_{to_code}_{today}"
        data = await self._get_json(
            "/search/",
            {
                "from": from_code,
                "to": to_code,
                "date": today,
                "transport_types": TRANSPORT_TYPES,
            },
            cache_key,
        )
        if data.get("error") and not data.get("segments"):
            return self._get_fallback_schedule(from_code, to_code)
        return data

    def _get_fallback_station_schedule(self, station_code: str, date_str: str, event: str) -> dict:
        moscow_leg = {
            "thread": {
                "number": "7R-167",
                "title": "Сыктывкар — Москва" if event == "departure" else "Москва — Сыктывкар",
                "transport_type": "plane",
                "carrier": {"title": "РусЛайн", "code": "7R"},
            },
            "departure": f"{date_str}T08:15:00",
            "arrival": f"{date_str}T10:05:00",
            "terminal": "A",
            "platform": "Выход 1",
        }
        regional_leg = {
            "thread": {
                "number": "KO-225",
                "title": "Сыктывкар — Усинск" if event == "departure" else "Усинск — Сыктывкар",
                "transport_type": "plane",
                "carrier": {"title": "Комиавиатранс", "code": "KO"},
            },
            "departure": f"{date_str}T09:30:00",
            "arrival": f"{date_str}T10:50:00",
            "terminal": None,
            "platform": "Сектор 2",
        }
        return {
            "station": {"code": station_code, "title": "Демо-станция"},
            "schedule": [moscow_leg, regional_leg],
            "is_fallback": True,
        }

    def _get_fallback_schedule(self, from_code: str, to_code: str) -> dict:
        return {
            "search": {"from": {"code": from_code}, "to": {"code": to_code}},
            "segments": [
                {
                    "thread": {
                        "number": "KO-225",
                        "title": "Сыктывкар — Усинск",
                        "transport_type": "plane",
                        "carrier": {"title": "Комиавиатранс", "code": "KO"}
                    },
                    "departure": f"{datetime.utcnow().strftime('%Y-%m-%d')}T09:30:00",
                    "arrival": f"{datetime.utcnow().strftime('%Y-%m-%d')}T10:50:00",
                    "duration": 4800,
                    "has_transfers": False
                },
                {
                    "thread": {
                        "number": "АВ-505",
                        "title": "Сыктывкар — Ухта",
                        "transport_type": "bus",
                        "carrier": {"title": "КомиАвтотранс", "code": "KAT"}
                    },
                    "departure": f"{datetime.utcnow().strftime('%Y-%m-%d')}T11:00:00",
                    "arrival": f"{datetime.utcnow().strftime('%Y-%m-%d')}T16:20:00",
                    "duration": 19200,
                    "has_transfers": False
                }
            ],
            "is_fallback": True
        }

yandex_service = YandexRaspService()
