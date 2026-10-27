import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

from config import settings
from models import WeatherMetrics, EmbeddedWeatherImpact

logger = logging.getLogger("transport_severa.weather")

WEATHER_CITIES = [
    {"city": "Сыктывкар", "latitude": 61.6469, "longitude": 50.8508},
    {"city": "Ухта", "latitude": 63.5658, "longitude": 53.8039},
    {"city": "Усинск", "latitude": 65.9989, "longitude": 57.3686},
    {"city": "Печора", "latitude": 65.1278, "longitude": 57.1264},
]
DEFAULT_CITY_NAMES = [item["city"] for item in WEATHER_CITIES]
OPEN_METEO_CACHE_TTL = timedelta(minutes=10)
OPEN_METEO_TIMEOUT_SECONDS = 10.0
OPEN_METEO_CURRENT_FIELDS = (
    "temperature_2m,relative_humidity_2m,weather_code,"
    "wind_speed_10m,wind_gusts_10m,visibility,surface_pressure"
)

WMO_WEATHER_RU = {
    0: "Ясно",
    1: "Преимущественно ясно",
    2: "Переменная облачность",
    3: "Пасмурно",
    45: "Туман",
    48: "Изморозь, туман",
    51: "Слабая морось",
    53: "Морось",
    55: "Сильная морось",
    56: "Ледяная морось",
    57: "Сильная ледяная морось",
    61: "Слабый дождь",
    63: "Дождь",
    65: "Сильный дождь",
    66: "Ледяной дождь",
    67: "Сильный ледяной дождь",
    71: "Слабый снег",
    73: "Снег",
    75: "Сильный снег",
    77: "Снежные зёрна",
    80: "Слабый ливень",
    81: "Ливень",
    82: "Сильный ливень",
    85: "Снегопад",
    86: "Сильный снегопад",
    95: "Гроза",
    96: "Гроза с градом",
    99: "Сильная гроза с градом",
}

_cache_lock = asyncio.Lock()
_cached_reports: Optional[list[dict]] = None
_cache_expires_at: Optional[datetime] = None

def evaluate_weather_impact(metrics: WeatherMetrics, transport_type: str = "PLANE") -> tuple[EmbeddedWeatherImpact, str, bool, bool]:
    """
    Evaluates weather conditions for extreme Northern conditions (Komi Republic).
    Returns: (weather_factor, alert_level, flight_critical, bus_critical)
    """
    has_impact = False
    phenomena_list = []
    flight_critical = False
    bus_critical = False
    alert_level = "NORMAL"

    # Aviation thresholds
    # Strong wind (>15 m/s or gusts >20 m/s), low visibility (<1000 m), blizzard, freezing rain
    if metrics.wind_speed_ms >= 15.0 or (metrics.wind_gust_ms and metrics.wind_gust_ms >= 20.0):
        flight_critical = True
        phenomena_list.append(f"Шквалистый боковой ветер {metrics.wind_speed_ms} м/с")
    
    if metrics.visibility_meters <= 800:
        flight_critical = True
        phenomena_list.append(f"Критическая видимость {metrics.visibility_meters} м")
    elif metrics.visibility_meters <= 1500:
        phenomena_list.append(f"Пониженная видимость {metrics.visibility_meters} м")

    # Road / Bus thresholds
    # Severe blizzard, icy conditions / freezing rain, extremely low temperature (below -38°C)
    lower_phenomena = metrics.phenomena.lower()
    if "гололёд" in lower_phenomena or "ледяной дождь" in lower_phenomena:
        bus_critical = True
        phenomena_list.append("Гололедица на трассе")

    if "метель" in lower_phenomena or "пурга" in lower_phenomena:
        flight_critical = True
        bus_critical = True
        phenomena_list.append("Сильная метель с перемётами")

    if metrics.temperature_c <= -38.0:
        bus_critical = True
        phenomena_list.append(f"Экстремальный мороз {metrics.temperature_c}°C")

    # Determine alert level
    if flight_critical or bus_critical:
        alert_level = "SEVERE"
        has_impact = True
    elif len(phenomena_list) > 0 or metrics.visibility_meters < 2000 or metrics.wind_speed_ms >= 10:
        alert_level = "ADVISORY"
        has_impact = True
    
    reason = ", ".join(phenomena_list) if phenomena_list else (metrics.phenomena or "Благоприятные метеоусловия")
    
    impact = EmbeddedWeatherImpact(
        has_impact=has_impact,
        phenomenon=reason if has_impact else None,
        updated_at=datetime.utcnow()
    )
    
    return impact, alert_level, flight_critical, bus_critical


def _error_report(city: str) -> dict:
    return {
        "city": city,
        "ok": False,
        "error": "ошибка",
        "timestamp": datetime.utcnow(),
    }


def _describe_wmo_code(code: int) -> str:
    return WMO_WEATHER_RU.get(int(code), "Неизвестные условия")


def _parse_current_observation(city: str, payload: dict) -> dict:
    current = payload.get("current") or {}
    weather_code = current.get("weather_code", 0)
    phenomena = _describe_wmo_code(weather_code)
    visibility_raw = current.get("visibility")
    visibility_meters = int(visibility_raw) if visibility_raw is not None else 10000
    metrics = WeatherMetrics(
        temperature_c=round(float(current.get("temperature_2m", 0.0)), 1),
        wind_speed_ms=round(float(current.get("wind_speed_10m", 0.0)), 1),
        wind_gust_ms=round(float(current.get("wind_gusts_10m") or 0.0), 1),
        visibility_meters=visibility_meters,
        phenomena=phenomena,
        humidity_percent=int(current["relative_humidity_2m"]) if current.get("relative_humidity_2m") is not None else None,
        pressure_hpa=round(float(current["surface_pressure"]), 1) if current.get("surface_pressure") is not None else None,
    )
    _, alert_level, flight_critical, bus_critical = evaluate_weather_impact(metrics)
    observed_at = current.get("time")
    return {
        "city": city,
        "ok": True,
        "timestamp": datetime.fromisoformat(observed_at) if observed_at else datetime.utcnow(),
        "metrics": metrics.model_dump(),
        "alert_level": alert_level,
        "flight_critical": flight_critical,
        "bus_critical": bus_critical,
        "source": "open-meteo",
    }


def _normalize_open_meteo_payload(payload) -> list[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("Неожиданный ответ Open-Meteo")


async def _fetch_open_meteo_reports() -> list[dict]:
    latitudes = ",".join(str(item["latitude"]) for item in WEATHER_CITIES)
    longitudes = ",".join(str(item["longitude"]) for item in WEATHER_CITIES)
    url = f"{settings.OPEN_METEO_BASE_URL.rstrip('/')}/forecast"
    params = {
        "latitude": latitudes,
        "longitude": longitudes,
        "current": OPEN_METEO_CURRENT_FIELDS,
        "wind_speed_unit": "ms",
        "timezone": "Europe/Moscow",
    }
    async with httpx.AsyncClient(timeout=OPEN_METEO_TIMEOUT_SECONDS) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payloads = _normalize_open_meteo_payload(response.json())

    if len(payloads) != len(WEATHER_CITIES):
        raise ValueError(
            f"Open-Meteo вернул {len(payloads)} точек вместо {len(WEATHER_CITIES)}"
        )

    return [
        _parse_current_observation(city_meta["city"], payload)
        for city_meta, payload in zip(WEATHER_CITIES, payloads)
    ]


async def get_latest_weather_reports(city: Optional[str] = None) -> list[dict]:
    requested = [city] if city else list(DEFAULT_CITY_NAMES)
    global _cached_reports, _cache_expires_at

    async with _cache_lock:
        now = datetime.utcnow()
        cache_fresh = (
            _cached_reports is not None
            and _cache_expires_at is not None
            and now < _cache_expires_at
        )
        if not cache_fresh:
            try:
                _cached_reports = await _fetch_open_meteo_reports()
                _cache_expires_at = now + OPEN_METEO_CACHE_TTL
                logger.info("Погода обновлена из Open-Meteo")
            except Exception as exc:
                logger.error("Open-Meteo недоступен: %s", exc)
                _cached_reports = [_error_report(name) for name in DEFAULT_CITY_NAMES]
                _cache_expires_at = now + timedelta(minutes=1)

    by_city = {item["city"]: item for item in _cached_reports}
    return [by_city.get(name, _error_report(name)) for name in requested if name]
