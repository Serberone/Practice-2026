from fastapi import APIRouter, Depends
from database import get_database
from routers.auth import require_role

router = APIRouter(prefix="/notifications", tags=["Журнал уведомлений"])

@router.get("")
async def get_notifications(
    trip_id: str = None,
    current_user: dict = Depends(require_role(["DISPATCHER", "ADMIN"]))
):
    """
    Returns dispatched notifications history
    """
    db_obj = get_database()
    notifs = []
    if db_obj.is_connected:
        query = {}
        if trip_id:
            query["trip_id"] = trip_id
        cursor = db_obj.db.notifications.find(query).sort("sent_at", -1)
        items = await cursor.to_list(length=200)
        for n in items:
            n["id"] = str(n.get("_id"))
            del n["_id"]
            notifs.append(n)
    else:
        for n in db_obj._fallback_store.get("notifications", {}).values():
            if trip_id and n.get("trip_id") != trip_id:
                continue
            notifs.append(n)
        notifs.sort(key=lambda x: str(x.get("sent_at", "")), reverse=True)

    return notifs
