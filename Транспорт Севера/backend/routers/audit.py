from fastapi import APIRouter, Depends
from database import get_database
from routers.auth import require_role

router = APIRouter(prefix="/audit", tags=["Журнал аудита"])

@router.get("")
async def get_audit_logs(
    event_type: str = None,
    current_user: dict = Depends(require_role(["DISPATCHER", "ADMIN"]))
):
    """
    Returns system audit logs (status overrides, manual edits, hiding trips)
    """
    db_obj = get_database()
    logs = []
    if db_obj.is_connected:
        query = {}
        if event_type:
            query["event_type"] = event_type
        cursor = db_obj.db.audit_logs.find(query).sort("timestamp", -1)
        items = await cursor.to_list(length=200)
        for log in items:
            log["id"] = str(log.get("_id"))
            del log["_id"]
            logs.append(log)
    else:
        for log in db_obj._fallback_store.get("audit_logs", []):
            if event_type and log.get("event_type") != event_type:
                continue
            logs.append(log)
        logs.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)

    return logs
