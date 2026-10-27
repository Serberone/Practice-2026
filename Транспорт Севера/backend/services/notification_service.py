import logging
from datetime import datetime
from bson import ObjectId
from models import Notification, SubscriptionInDB, TripInDB
from database import get_database

logger = logging.getLogger("transport_severa.notifications")

async def dispatch_trip_status_notifications(
    trip: dict,
    change_type: str,
    custom_message: str = None
) -> list[dict]:
    """
    Finds all active subscriptions for the given trip and generates notifications.
    Stores them in MongoDB collection 'notifications'.
    """
    db_obj = get_database()
    dispatched = []

    trip_id = str(trip.get("_id") or trip.get("id"))
    trip_number = trip.get("trip_number", "Рейс")
    origin_city = trip.get("route", {}).get("origin", {}).get("city", "")
    dest_city = trip.get("route", {}).get("destination", {}).get("city", "")
    status = trip.get("status", "")
    weather_reason = trip.get("weather_factor", {}).get("phenomenon") or ""

    if custom_message:
        message_body = custom_message
    else:
        if change_type == "DELAY":
            est_dep = trip.get("schedule", {}).get("departure_estimated")
            est_str = est_dep.strftime("%H:%M %d.%m.%Y") if isinstance(est_dep, datetime) else str(est_dep or "уточняется")
            message_body = f"Внимание! Рейс {trip_number} ({origin_city} → {dest_city}) задержан. Новое расчётное время отправления: {est_str}."
            if weather_reason:
                message_body += f" Причина: {weather_reason}."
        elif change_type == "CANCELLATION":
            message_body = f"Срочно! Рейс {trip_number} ({origin_city} → {dest_city}) отменён."
            if weather_reason:
                message_body += f" Причина: сложные метеоусловия ({weather_reason})."
        elif change_type == "GATE_CHANGE":
            gate = trip.get("gate_or_platform", "уточняется")
            message_body = f"Изменение выхода/платформы для рейса {trip_number}: назначен сектор/гейт {gate}."
        else:
            message_body = f"Информация по рейсу {trip_number} ({origin_city} → {dest_city}): текущий статус {status}."

    # Look for subscribers
    subscribers = []
    if db_obj.is_connected:
        try:
            cursor = db_obj.db.subscriptions.find({"trip_id": ObjectId(trip_id) if ObjectId.is_valid(trip_id) else trip_id, "is_active": True})
            subscribers = await cursor.to_list(length=1000)
        except Exception as e:
            logger.error(f"Error fetching subscribers from MongoDB: {e}")
    else:
        # Fallback in-memory
        subscribers = [
            s for s in db_obj._fallback_store.get("subscriptions", {}).values()
            if str(s.get("trip_id")) == trip_id and s.get("is_active", True)
        ]

    logger.info(f"Dispatching notifications for trip {trip_number} to {len(subscribers)} subscribers...")

    for sub in subscribers:
        sub_id = str(sub.get("_id") or sub.get("id"))
        recipient = sub.get("recipient")
        channel = sub.get("channel", "EMAIL")

        notif_doc = {
            "subscription_id": sub_id,
            "trip_id": trip_id,
            "recipient": recipient,
            "change_type": change_type,
            "channel": channel,
            "payload": {
                "trip_number": trip_number,
                "message": message_body,
                "origin": origin_city,
                "destination": dest_city,
                "status": status
            },
            "status": "SENT",
            "retry_count": 0,
            "sent_at": datetime.utcnow()
        }

        if db_obj.is_connected:
            try:
                res = await db_obj.db.notifications.insert_one(notif_doc)
                notif_doc["_id"] = str(res.inserted_id)
            except Exception as e:
                logger.error(f"Error writing notification to Mongo: {e}")
                notif_doc["_id"] = str(ObjectId())
        else:
            if "notifications" not in db_obj._fallback_store:
                db_obj._fallback_store["notifications"] = {}
            nid = str(ObjectId())
            notif_doc["_id"] = nid
            db_obj._fallback_store["notifications"][nid] = notif_doc

        dispatched.append(notif_doc)
        logger.info(f"Notification sent to {recipient} via {channel}: {message_body}")

    return dispatched
