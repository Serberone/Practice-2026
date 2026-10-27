import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from bson import ObjectId

from database import get_database
from models import SubscriptionCreate

logger = logging.getLogger("transport_severa.subscriptions")
router = APIRouter(prefix="/subscriptions", tags=["Подписки пассажиров"])

@router.post("")
async def create_subscription(sub: SubscriptionCreate):
    """
    Passenger subscribes to receive flight/bus status change alerts via email or push
    """
    db_obj = get_database()
    sub_dict = sub.dict()
    sub_dict["created_at"] = datetime.utcnow()
    sub_dict["is_active"] = True

    if db_obj.is_connected:
        # Check duplicate
        existing = await db_obj.db.subscriptions.find_one({
            "trip_id": sub.trip_id,
            "recipient": sub.recipient,
            "is_active": True
        })
        if existing:
            return {"message": "Вы уже подписаны на обновления этого рейса", "id": str(existing.get("_id"))}

        res = await db_obj.db.subscriptions.insert_one(sub_dict)
        sub_dict["id"] = str(res.inserted_id)
        if "_id" in sub_dict:
            del sub_dict["_id"]
    else:
        if "subscriptions" not in db_obj._fallback_store:
            db_obj._fallback_store["subscriptions"] = {}
        for s in db_obj._fallback_store["subscriptions"].values():
            if s.get("trip_id") == sub.trip_id and s.get("recipient") == sub.recipient and s.get("is_active", True):
                return {"message": "Вы уже подписаны на обновления этого рейса", "id": s.get("id")}
        sid = str(ObjectId())
        sub_dict["id"] = sid
        db_obj._fallback_store["subscriptions"][sid] = sub_dict

    logger.info(f"New subscription registered for trip {sub.trip_id} by {sub.recipient}")
    return {"message": "Подписка успешно оформлена! Вы будете получать уведомления об изменении статуса рейса.", "subscription": sub_dict}

@router.delete("/{sub_id}")
async def cancel_subscription(sub_id: str):
    db_obj = get_database()
    if db_obj.is_connected:
        if ObjectId.is_valid(sub_id):
            await db_obj.db.subscriptions.update_one({"_id": ObjectId(sub_id)}, {"$set": {"is_active": False}})
        else:
            await db_obj.db.subscriptions.update_one({"id": sub_id}, {"$set": {"is_active": False}})
    else:
        if sub_id in db_obj._fallback_store.get("subscriptions", {}):
            db_obj._fallback_store["subscriptions"][sub_id]["is_active"] = False
    return {"message": "Подписка отменена"}
