import logging
from datetime import datetime, timedelta
import httpx
from config import settings
from database import get_database

logger = logging.getLogger("transport_severa.yandex_rasp")

class YandexRaspService:
    def __init__(self):
        self.api_key = settings.YANDEX_RASP_API_KEY
        self.base_url = settings.YANDEX_RASP_BASE_URL

    async def get_schedule_between_stations(
        self,
        from_code: str,
        to_code: str,
        date_str: str = None
    ) -> dict:
        """
        Retrieves schedule between two stations from Yandex.Schedules v3 API.
        Checks cache in MongoDB first to avoid exceeding the daily limit (500 requests).
        """
        db_obj = get_database()
        today = date_str or datetime.utcnow().strftime("%Y-%m-%d")
        cache_key = f"{from_code}_{to_code}_{today}"

        # 1. Check cache
        if db_obj.is_connected:
            cached = await db_obj.db.yandex_cache.find_one({"cache_key": cache_key})
            if cached and cached.get("expires_at", datetime.min) > datetime.utcnow():
                logger.info(f"Serving Yandex Rasp data from MongoDB cache for {cache_key}")
                return cached.get("data", {})

        # 2. Check if API key is configured
        if not self.api_key or self.api_key == "ВАШ_КЛЮЧ":
            logger.info("Yandex Rasp API key not provided or empty. Returning structured demo schedule.")
            return self._get_fallback_schedule(from_code, to_code)

        # 3. Call Yandex Rasp API
        params = {
            "apikey": self.api_key,
            "from": from_code,
            "to": to_code,
            "format": "json",
            "lang": "ru_RU",
            "date": today
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/search/", params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    # Cache in MongoDB for 30 minutes
                    if db_obj.is_connected:
                        await db_obj.db.yandex_cache.update_one(
                            {"cache_key": cache_key},
                            {
                                "$set": {
                                    "cache_key": cache_key,
                                    "data": data,
                                    "cached_at": datetime.utcnow(),
                                    "expires_at": datetime.utcnow() + timedelta(minutes=30)
                                }
                            },
                            upsert=True
                        )
                    return data
                else:
                    logger.warning(f"Yandex Rasp API returned {resp.status_code}: {resp.text}")
                    return self._get_fallback_schedule(from_code, to_code)
        except Exception as e:
            logger.error(f"Error calling Yandex Rasp API: {e}")
            return self._get_fallback_schedule(from_code, to_code)

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
