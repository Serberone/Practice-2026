import logging
from datetime import datetime, timedelta
from bson import ObjectId
from database import get_database

logger = logging.getLogger("transport_severa.seed")

def hash_pw(password: str) -> str:
    import hashlib
    salt = "sever_transport_salt_2026"
    return hashlib.sha256((password + salt).encode()).hexdigest()

async def seed_initial_data():
    db_obj = get_database()
    logger.info("Seeding initial data for Transport Severa (Komi Republic)...")

    # 1. Stations
    stations = [
        {
            "id": "st_scw_air",
            "name": "Международный аэропорт Сыктывкар им. П.А. Истомина",
            "city": "Сыктывкар",
            "type": "AIRPORT",
            "code": "SCW",
            "yandex_code": "s9600378",
            "location": {"type": "Point", "coordinates": [50.8508, 61.6469]},
            "is_active": True
        },
        {
            "id": "st_scw_bus",
            "name": "Автовокзал Сыктывкар (ул. Морозова, 202)",
            "city": "Сыктывкар",
            "type": "BUS_STATION",
            "code": "SCW_BUS",
            "yandex_code": "s9637101",
            "location": {"type": "Point", "coordinates": [50.8142, 61.6485]},
            "is_active": True
        },
        {
            "id": "st_usk_air",
            "name": "Аэропорт Усинск",
            "city": "Усинск",
            "type": "AIRPORT",
            "code": "USK",
            "yandex_code": "s9600382",
            "location": {"type": "Point", "coordinates": [57.3686, 65.9989]},
            "is_active": True
        },
        {
            "id": "st_usk_bus",
            "name": "Автостанция Усинск (ул. Заводская)",
            "city": "Усинск",
            "type": "BUS_STATION",
            "code": "USK_BUS",
            "yandex_code": "s9637105",
            "location": {"type": "Point", "coordinates": [57.3120, 65.9940]},
            "is_active": True
        },
        {
            "id": "st_uct_air",
            "name": "Аэропорт Ухта",
            "city": "Ухта",
            "type": "AIRPORT",
            "code": "UCT",
            "yandex_code": "s9600380",
            "location": {"type": "Point", "coordinates": [53.8039, 63.5658]},
            "is_active": True
        },
        {
            "id": "st_uct_bus",
            "name": "Автовокзал Ухта (ул. Октябрьская, 24)",
            "city": "Ухта",
            "type": "BUS_STATION",
            "code": "UCT_BUS",
            "yandex_code": "s9637103",
            "location": {"type": "Point", "coordinates": [53.6820, 63.5610]},
            "is_active": True
        },
        {
            "id": "st_peo_air",
            "name": "Аэропорт Печора",
            "city": "Печора",
            "type": "AIRPORT",
            "code": "PEO",
            "yandex_code": "s9600381",
            "location": {"type": "Point", "coordinates": [57.1264, 65.1278]},
            "is_active": True
        },
        {
            "id": "st_peo_bus",
            "name": "Автостанция Печора (Привокзальная пл.)",
            "city": "Печора",
            "type": "BUS_STATION",
            "code": "PEO_BUS",
            "yandex_code": "s9637107",
            "location": {"type": "Point", "coordinates": [57.1500, 65.1400]},
            "is_active": True
        }
    ]

    # 2. Carriers
    carriers = [
        {
            "id": "car_komi_air",
            "name": "АО «Комиавиатранс»",
            "short_name": "Комиавиатранс",
            "transport_type": "AIR",
            "phone": "+7 (8212) 28-02-00",
            "inn": "1101016867"
        },
        {
            "id": "car_rusline",
            "name": "Авиакомпания «РусЛайн»",
            "short_name": "РусЛайн",
            "transport_type": "AIR",
            "phone": "+7 (800) 555-58-00",
            "inn": "7701193390"
        },
        {
            "id": "car_komi_bus",
            "name": "АО «Комиавтотранс»",
            "short_name": "Комиавтотранс",
            "transport_type": "BUS",
            "phone": "+7 (8212) 21-13-14",
            "inn": "1101123456"
        },
        {
            "id": "car_sever_bus",
            "name": "ООО «СеверТрансАвто»",
            "short_name": "СеверТрансАвто",
            "transport_type": "BUS",
            "phone": "+7 (82144) 4-12-34",
            "inn": "1106098765"
        }
    ]

    # 3. Default Users
    users = [
        {
            "username": "admin",
            "full_name": "Служба системного администрирования",
            "role": "ADMIN",
            "is_active": True,
            "hashed_password": hash_pw("admin123"),
            "created_at": datetime.utcnow()
        },
        {
            "username": "dispatcher",
            "full_name": "Центральный диспетчер Минтранса РК",
            "role": "DISPATCHER",
            "is_active": True,
            "hashed_password": hash_pw("disp123"),
            "created_at": datetime.utcnow()
        }
    ]

    now = datetime.utcnow()

    # 5. Trips
    trips = [
        {
            "id": "tr_ko_225",
            "trip_number": "KO-225",
            "transport_type": "PLANE",
            "carrier": {"id": "car_komi_air", "name": "АО «Комиавиатранс»", "phone": "+7 (8212) 28-02-00"},
            "route": {
                "origin": {"station_id": "st_scw_air", "city": "Сыктывкар", "name": "Аэропорт Сыктывкар им. П.А. Истомина"},
                "destination": {"station_id": "st_usk_air", "city": "Усинск", "name": "Аэропорт Усинск"}
            },
            "schedule": {
                "departure_planned": now + timedelta(hours=1),
                "arrival_planned": now + timedelta(hours=2, minutes=20),
                "departure_estimated": now + timedelta(hours=3, minutes=30),
                "arrival_estimated": now + timedelta(hours=4, minutes=50)
            },
            "status": "DELAYED",
            "gate_or_platform": "Сектор 2",
            "weather_factor": {
                "has_impact": True,
                "phenomenon": "Задержка вылета: в аэропорту Усинск метель, боковой ветер 17 м/с, видимость 650 м",
                "updated_at": now
            },
            "display_flags": {"is_hidden": False, "requires_dispatcher_review": False, "manual_override": True},
            "source": "YANDEX_RASP",
            "last_synced_at": now
        },
        {
            "id": "tr_7r_132",
            "trip_number": "7R-132",
            "transport_type": "PLANE",
            "carrier": {"id": "car_rusline", "name": "Авиакомпания «РусЛайн»", "phone": "+7 (800) 555-58-00"},
            "route": {
                "origin": {"station_id": "st_scw_air", "city": "Сыктывкар", "name": "Аэропорт Сыктывкар им. П.А. Истомина"},
                "destination": {"station_id": "st_uct_air", "city": "Ухта", "name": "Аэропорт Ухта"}
            },
            "schedule": {
                "departure_planned": now + timedelta(minutes=40),
                "arrival_planned": now + timedelta(hours=1, minutes=30),
                "departure_estimated": now + timedelta(minutes=40),
                "arrival_estimated": now + timedelta(hours=1, minutes=30)
            },
            "status": "BOARDING",
            "gate_or_platform": "Выход 1",
            "weather_factor": {"has_impact": False, "phenomenon": "Погодные условия в норме", "updated_at": now},
            "display_flags": {"is_hidden": False, "requires_dispatcher_review": False, "manual_override": False},
            "source": "YANDEX_RASP",
            "last_synced_at": now
        },
        {
            "id": "tr_ko_228",
            "trip_number": "KO-228",
            "transport_type": "PLANE",
            "carrier": {"id": "car_komi_air", "name": "АО «Комиавиатранс»", "phone": "+7 (8212) 28-02-00"},
            "route": {
                "origin": {"station_id": "st_uct_air", "city": "Ухта", "name": "Аэропорт Ухта"},
                "destination": {"station_id": "st_peo_air", "city": "Печора", "name": "Аэропорт Печора"}
            },
            "schedule": {
                "departure_planned": now + timedelta(hours=2),
                "arrival_planned": now + timedelta(hours=3),
                "departure_estimated": now + timedelta(hours=2),
                "arrival_estimated": now + timedelta(hours=3)
            },
            "status": "SCHEDULED",
            "gate_or_platform": "Сектор A",
            "weather_factor": {"has_impact": True, "phenomenon": "Внимание: в Печоре низовая метель", "updated_at": now},
            "display_flags": {"is_hidden": False, "requires_dispatcher_review": True, "manual_override": False},
            "source": "YANDEX_RASP",
            "last_synced_at": now
        },
        {
            "id": "tr_bus_505",
            "trip_number": "АВ-505",
            "transport_type": "BUS",
            "carrier": {"id": "car_komi_bus", "name": "АО «Комиавтотранс»", "phone": "+7 (8212) 21-13-14"},
            "route": {
                "origin": {"station_id": "st_scw_bus", "city": "Сыктывкар", "name": "Автовокзал Сыктывкар"},
                "destination": {"station_id": "st_uct_bus", "city": "Ухта", "name": "Автовокзал Ухта"}
            },
            "schedule": {
                "departure_planned": now + timedelta(hours=1, minutes=15),
                "arrival_planned": now + timedelta(hours=6, minutes=30),
                "departure_estimated": now + timedelta(hours=1, minutes=15),
                "arrival_estimated": now + timedelta(hours=6, minutes=30)
            },
            "status": "SCHEDULED",
            "gate_or_platform": "Платформа 3",
            "weather_factor": {"has_impact": False, "phenomenon": "Трасса свободна", "updated_at": now},
            "display_flags": {"is_hidden": False, "requires_dispatcher_review": False, "manual_override": False},
            "source": "CARRIER_DIRECT",
            "last_synced_at": now
        },
        {
            "id": "tr_bus_520",
            "trip_number": "АВ-520",
            "transport_type": "BUS",
            "carrier": {"id": "car_sever_bus", "name": "ООО «СеверТрансАвто»", "phone": "+7 (82144) 4-12-34"},
            "route": {
                "origin": {"station_id": "st_uct_bus", "city": "Ухта", "name": "Автовокзал Ухта"},
                "destination": {"station_id": "st_usk_bus", "city": "Усинск", "name": "Автостанция Усинск"}
            },
            "schedule": {
                "departure_planned": now + timedelta(hours=1, minutes=45),
                "arrival_planned": now + timedelta(hours=8, minutes=0),
                "departure_estimated": now + timedelta(hours=3, minutes=0),
                "arrival_estimated": now + timedelta(hours=9, minutes=15)
            },
            "status": "DELAYED",
            "gate_or_platform": "Платформа 1",
            "weather_factor": {
                "has_impact": True,
                "phenomenon": "Задержка рейса: снежные заносы и гололедица на трассе Ухта — Усинск",
                "updated_at": now
            },
            "display_flags": {"is_hidden": False, "requires_dispatcher_review": False, "manual_override": True},
            "source": "CARRIER_DIRECT",
            "last_synced_at": now
        },
        {
            "id": "tr_bus_530",
            "trip_number": "АВ-530",
            "transport_type": "BUS",
            "carrier": {"id": "car_sever_bus", "name": "ООО «СеверТрансАвто»", "phone": "+7 (82144) 4-12-34"},
            "route": {
                "origin": {"station_id": "st_peo_bus", "city": "Печора", "name": "Автостанция Печора"},
                "destination": {"station_id": "st_usk_bus", "city": "Усинск", "name": "Автостанция Усинск"}
            },
            "schedule": {
                "departure_planned": now + timedelta(hours=2, minutes=30),
                "arrival_planned": now + timedelta(hours=6, minutes=45)
            },
            "status": "CANCELLED",
            "gate_or_platform": "Платформа 2",
            "weather_factor": {
                "has_impact": True,
                "phenomenon": "Рейс отменён: нулевая видимость и штормовое предупреждение по северу РК",
                "updated_at": now
            },
            "display_flags": {"is_hidden": False, "requires_dispatcher_review": False, "manual_override": True},
            "source": "CARRIER_DIRECT",
            "last_synced_at": now
        }
    ]

    # Save to MongoDB or Fallback store
    if db_obj.is_connected:
        try:
            # Stations
            for s in stations:
                await db_obj.db.stations.update_one({"code": s["code"]}, {"$set": s}, upsert=True)
            # Carriers
            for c in carriers:
                await db_obj.db.carriers.update_one({"inn": c["inn"]}, {"$set": c}, upsert=True)
            # Users
            for u in users:
                await db_obj.db.users.update_one({"username": u["username"]}, {"$set": u}, upsert=True)
            # Trips
            for t in trips:
                await db_obj.db.trips.update_one({"trip_number": t["trip_number"]}, {"$set": t}, upsert=True)
            logger.info("MongoDB successfully seeded with Komi Republic data.")
        except Exception as e:
            logger.error(f"Error seeding MongoDB: {e}")
    else:
        # Fallback memory store
        db_obj._fallback_store["stations"] = {s["id"]: s for s in stations}
        db_obj._fallback_store["carriers"] = {c["id"]: c for c in carriers}
        db_obj._fallback_store["users"] = {u["username"]: u for u in users}
        db_obj._fallback_store["weather"] = {}
        db_obj._fallback_store["trips"] = {t["id"]: t for t in trips}
        db_obj._fallback_store["subscriptions"] = {}
        db_obj._fallback_store["notifications"] = {}
        db_obj._fallback_store["audit_logs"] = []
        logger.info("Embedded in-memory store initialized with demo data.")
