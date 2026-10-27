import logging
from datetime import datetime
from models import WeatherMetrics, EmbeddedWeatherImpact

logger = logging.getLogger("transport_severa.weather")

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
