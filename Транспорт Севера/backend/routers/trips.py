import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from bson import ObjectId

from database import get_database
from models import TripBase, TripInDB
from routers.auth import get_current_user, require_role
from services.notification_service import dispatch_trip_status_notifications

logger = logging.getLogger("transport_severa.trips")
router = APIRouter(prefix="/trips", tags=["Рейсы и онлайн-табло"])

class StatusOverrideRequest(BaseModel):
    status: str  # SCHEDULED, DELAYED, BOARDING, CANCELLED, ARRIVED, DEPARTED
    delay_minutes: Optional[int] = 0
    delay_reason: Optional[str] = None
    gate_or_platform: Optional[str] = None

class TripHideRequest(BaseModel):
    is_hidden: bool

@router.get("")
async def get_trips(
    transport_type: Optional[str] = Query(None, description="PLANE или BUS"),
    direction: Optional[str] = Query("DEPARTURE", description="DEPARTURE или ARRIVAL"),
    city: Optional[str] = Query(None, description="Фильтр по городу отправления или прибытия"),
    status: Optional[str] = Query(None, description="Фильтр по статусу рейса"),
    search: Optional[str] = Query(None, description="Поиск по номеру рейса или городу"),
    include_hidden: bool = Query(False, description="Включать скрытые рейсы (только для диспетчера)")
):
    db_obj = get_database()
    query = {}
    if not include_hidden:
        query["display_flags.is_hidden"] = {"$ne": True}
    
    if transport_type:
        query["transport_type"] = transport_type.upper()
    
    if status:
        query["status"] = status.upper()

    trips = []
    if db_obj.is_connected:
        cursor = db_obj.db.trips.find(query).sort("schedule.departure_planned", 1)
        raw_trips = await cursor.to_list(length=500)
        for t in raw_trips:
            t["id"] = str(t.get("_id"))
            del t["_id"]
            trips.append(t)
    else:
        for t in db_obj._fallback_store.get("trips", {}).values():
            if not include_hidden and t.get("display_flags", {}).get("is_hidden"):
                continue
            if transport_type and t.get("transport_type") != transport_type.upper():
                continue
            if status and t.get("status") != status.upper():
                continue
            trips.append(t)
        trips.sort(key=lambda x: str(x.get("schedule", {}).get("departure_planned", "")))

    # In-memory post-filters for city & search
    filtered = []
    for t in trips:
        orig = t.get("route", {}).get("origin", {}).get("city", "")
        dest = t.get("route", {}).get("destination", {}).get("city", "")
        num = t.get("trip_number", "")
        carrier = t.get("carrier", {}).get("name", "")

        if city:
            if direction == "DEPARTURE" and orig.lower() != city.lower():
                continue
            elif direction == "ARRIVAL" and dest.lower() != city.lower():
                continue
            elif direction not in ["DEPARTURE", "ARRIVAL"] and (orig.lower() != city.lower() and dest.lower() != city.lower()):
                continue

        if search:
            s_low = search.lower()
            if (s_low not in num.lower() and 
                s_low not in orig.lower() and 
                s_low not in dest.lower() and 
                s_low not in carrier.lower()):
                continue

        filtered.append(t)

    return filtered

@router.get("/{trip_id}")
async def get_trip_by_id(trip_id: str):
    db_obj = get_database()
    t = None
    if db_obj.is_connected:
        if ObjectId.is_valid(trip_id):
            t = await db_obj.db.trips.find_one({"_id": ObjectId(trip_id)})
        if not t:
            t = await db_obj.db.trips.find_one({"id": trip_id})
        if t:
            t["id"] = str(t.get("_id"))
            del t["_id"]
    else:
        t = db_obj._fallback_store.get("trips", {}).get(trip_id)

    if not t:
        raise HTTPException(status_code=404, detail="Рейс не найден")
    return t

@router.post("/{trip_id}/override-status")
async def override_trip_status(
    trip_id: str,
    req: StatusOverrideRequest,
    current_user: dict = Depends(require_role(["DISPATCHER", "ADMIN"]))
):
    """
    Dispatcher overrides trip status, delay reason, or platform/gate.
    Dispatches automated notifications to subscribers and writes an audit log.
    """
    db_obj = get_database()
    t = await get_trip_by_id(trip_id)

    old_status = t.get("status")
    new_status = req.status.upper()
    
    update_fields = {
        "status": new_status,
        "display_flags.manual_override": True,
        "display_flags.requires_dispatcher_review": False
    }

    if req.gate_or_platform is not None:
        update_fields["gate_or_platform"] = req.gate_or_platform

    # Calculate estimated departure if delay is supplied
    if req.delay_minutes and req.delay_minutes > 0:
        planned_dep = t.get("schedule", {}).get("departure_planned")
        if isinstance(planned_dep, str):
            planned_dep = datetime.fromisoformat(planned_dep.replace("Z", "+00:00"))
        new_dep = planned_dep + (planned_dep - planned_dep) + datetime.resolution * 0 # timedelta
        import datetime as dt_mod
        update_fields["schedule.departure_estimated"] = planned_dep + dt_mod.timedelta(minutes=req.delay_minutes)

    if req.delay_reason:
        update_fields["weather_factor.has_impact"] = True
        update_fields["weather_factor.phenomenon"] = req.delay_reason
        update_fields["weather_factor.updated_at"] = datetime.utcnow()

    # Update in DB
    if db_obj.is_connected:
        query_id = {"_id": ObjectId(trip_id)} if ObjectId.is_valid(trip_id) else {"id": trip_id}
        await db_obj.db.trips.update_one(query_id, {"$set": update_fields})
    else:
        # Fallback
        t.update(update_fields)
        if "schedule.departure_estimated" in update_fields:
            t["schedule"]["departure_estimated"] = update_fields["schedule.departure_estimated"]
        if "weather_factor.phenomenon" in update_fields:
            t["weather_factor"]["has_impact"] = True
            t["weather_factor"]["phenomenon"] = update_fields["weather_factor.phenomenon"]
        t["status"] = new_status
        db_obj._fallback_store.get("trips", {})[trip_id] = t

    # Audit log
    audit_doc = {
        "timestamp": datetime.utcnow(),
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "username": current_user.get("username"),
        "event_type": "STATUS_OVERRIDE",
        "entity_id": trip_id,
        "details": {
            "trip_number": t.get("trip_number"),
            "old_status": old_status,
            "new_status": new_status,
            "reason": req.delay_reason,
            "delay_minutes": req.delay_minutes
        }
    }
    if db_obj.is_connected:
        await db_obj.db.audit_logs.insert_one(audit_doc)
    else:
        if "audit_logs" not in db_obj._fallback_store:
            db_obj._fallback_store["audit_logs"] = []
        db_obj._fallback_store["audit_logs"].append(audit_doc)

    # Dispatch notifications
    change_type = "DELAY" if new_status == "DELAYED" else ("CANCELLATION" if new_status == "CANCELLED" else "STATUS_CHANGE")
    updated_trip = await get_trip_by_id(trip_id)
    await dispatch_trip_status_notifications(updated_trip, change_type=change_type)

    return {"message": "Статус рейса успешно обновлён", "trip": updated_trip}

@router.post("/{trip_id}/hide")
async def hide_trip(
    trip_id: str,
    req: TripHideRequest,
    current_user: dict = Depends(require_role(["DISPATCHER", "ADMIN"]))
):
    db_obj = get_database()
    t = await get_trip_by_id(trip_id)
    
    if db_obj.is_connected:
        query_id = {"_id": ObjectId(trip_id)} if ObjectId.is_valid(trip_id) else {"id": trip_id}
        await db_obj.db.trips.update_one(query_id, {"$set": {"display_flags.is_hidden": req.is_hidden}})
    else:
        t["display_flags"]["is_hidden"] = req.is_hidden
        db_obj._fallback_store.get("trips", {})[trip_id] = t

    audit_doc = {
        "timestamp": datetime.utcnow(),
        "user_id": str(current_user.get("_id") or current_user.get("id")),
        "username": current_user.get("username"),
        "event_type": "HIDE_TRIP" if req.is_hidden else "SHOW_TRIP",
        "entity_id": trip_id,
        "details": {"trip_number": t.get("trip_number"), "is_hidden": req.is_hidden}
    }
    if db_obj.is_connected:
        await db_obj.db.audit_logs.insert_one(audit_doc)
    else:
        if "audit_logs" not in db_obj._fallback_store:
            db_obj._fallback_store["audit_logs"] = []
        db_obj._fallback_store["audit_logs"].append(audit_doc)

    return {"message": f"Видимость рейса изменена (скрыт: {req.is_hidden})"}

@router.post("/{trip_id}/verify")
async def verify_trip(
    trip_id: str,
    current_user: dict = Depends(require_role(["DISPATCHER", "ADMIN"]))
):
    """Dispatcher verifies and approves the trip publication on the scoreboard"""
    db_obj = get_database()
    t = await get_trip_by_id(trip_id)
    
    if db_obj.is_connected:
        query_id = {"_id": ObjectId(trip_id)} if ObjectId.is_valid(trip_id) else {"id": trip_id}
        await db_obj.db.trips.update_one(query_id, {"$set": {"display_flags.requires_dispatcher_review": False}})
    else:
        t["display_flags"]["requires_dispatcher_review"] = False
        db_obj._fallback_store.get("trips", {})[trip_id] = t

    return {"message": "Публикация рейса подтверждена диспетчером"}
