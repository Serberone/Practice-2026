from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from database import get_database
from models import StationBase
from routers.auth import require_role

router = APIRouter(prefix="/stations", tags=["Справочник станций"])


def _serialize_station(station_doc: dict) -> dict:
    result = dict(station_doc)
    mongo_id = result.pop("_id", None)
    if mongo_id is not None:
        mongo_id_str = str(mongo_id)
        if not result.get("id"):
            result["id"] = mongo_id_str
        result["_mongo_id"] = mongo_id_str
    return result


async def _find_station_document(db_obj, station_id: str):
    if db_obj.is_connected:
        if ObjectId.is_valid(station_id):
            document = await db_obj.db.stations.find_one({"_id": ObjectId(station_id)})
            if document:
                return document
        document = await db_obj.db.stations.find_one({"id": station_id})
        if document:
            return document
        return await db_obj.db.stations.find_one({"code": station_id})

    store = db_obj._fallback_store.get("stations", {})
    if station_id in store:
        return store[station_id]
    for station in store.values():
        if station.get("id") == station_id or station.get("code") == station_id:
            return station
    return None


def _fallback_station_key(store: dict, station_doc: dict, station_id: str) -> str | None:
    if station_id in store:
        return station_id
    for key, station in store.items():
        if station is station_doc or station.get("id") == station_id or station.get("code") == station_id:
            return key
    return None


@router.get("")
async def get_stations(city: str = None, type: str = None, include_inactive: bool = False):
    db_obj = get_database()
    query = {}
    if not include_inactive:
        query["is_active"] = True
    if city:
        query["city"] = city
    if type:
        query["type"] = type

    stations = []
    if db_obj.is_connected:
        cursor = db_obj.db.stations.find(query)
        items = await cursor.to_list(length=200)
        for station in items:
            stations.append(_serialize_station(station))
    else:
        for station in db_obj._fallback_store.get("stations", {}).values():
            if not include_inactive and not station.get("is_active", True):
                continue
            if city and station.get("city") != city:
                continue
            if type and station.get("type") != type:
                continue
            stations.append(dict(station))
    return stations


@router.post("")
async def create_station(station: StationBase, current_user: dict = Depends(require_role(["ADMIN"]))):
    db_obj = get_database()
    station_dict = station.dict()
    if db_obj.is_connected:
        existing = await db_obj.db.stations.find_one({"code": station_dict["code"]})
        if existing:
            raise HTTPException(status_code=400, detail="Станция с таким кодом уже существует")
        result = await db_obj.db.stations.insert_one(station_dict)
        station_dict["id"] = str(result.inserted_id)
    else:
        if "stations" not in db_obj._fallback_store:
            db_obj._fallback_store["stations"] = {}
        for existing in db_obj._fallback_store["stations"].values():
            if existing.get("code") == station_dict["code"]:
                raise HTTPException(status_code=400, detail="Станция с таким кодом уже существует")
        station_id = str(ObjectId())
        station_dict["id"] = station_id
        db_obj._fallback_store["stations"][station_id] = station_dict
    return station_dict


@router.put("/{station_id}")
async def update_station(
    station_id: str,
    station: StationBase,
    current_user: dict = Depends(require_role(["ADMIN"])),
):
    db_obj = get_database()
    existing = await _find_station_document(db_obj, station_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    updates = station.dict()
    if db_obj.is_connected:
        mongo_id = existing.get("_id")
        conflict = await db_obj.db.stations.find_one({
            "code": updates["code"],
            "_id": {"$ne": mongo_id},
        })
        if conflict:
            raise HTTPException(status_code=400, detail="Станция с таким кодом уже существует")
        await db_obj.db.stations.update_one({"_id": mongo_id}, {"$set": updates})
        updated = await db_obj.db.stations.find_one({"_id": mongo_id})
        return _serialize_station(updated)

    store = db_obj._fallback_store.get("stations", {})
    key = _fallback_station_key(store, existing, station_id)
    if key is None:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    for other_key, other in store.items():
        if other_key != key and other.get("code") == updates["code"]:
            raise HTTPException(status_code=400, detail="Станция с таким кодом уже существует")
    updated = {**existing, **updates, "id": existing.get("id", key)}
    store[key] = updated
    return updated


@router.delete("/{station_id}")
async def delete_station(station_id: str, current_user: dict = Depends(require_role(["ADMIN"]))):
    db_obj = get_database()
    existing = await _find_station_document(db_obj, station_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    if db_obj.is_connected:
        await db_obj.db.stations.delete_one({"_id": existing["_id"]})
    else:
        store = db_obj._fallback_store.get("stations", {})
        key = _fallback_station_key(store, existing, station_id)
        if key is None:
            raise HTTPException(status_code=404, detail="Станция не найдена")
        del store[key]

    return {"message": "Станция удалена", "id": station_id}
