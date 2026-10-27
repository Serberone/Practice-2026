from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from database import get_database
from models import CarrierBase
from routers.auth import require_role

router = APIRouter(prefix="/carriers", tags=["Справочник перевозчиков"])


def _serialize_carrier(carrier_doc: dict) -> dict:
    result = dict(carrier_doc)
    mongo_id = result.pop("_id", None)
    if mongo_id is not None:
        mongo_id_str = str(mongo_id)
        if not result.get("id"):
            result["id"] = mongo_id_str
        result["_mongo_id"] = mongo_id_str
    return result


async def _find_carrier_document(db_obj, carrier_id: str):
    if db_obj.is_connected:
        if ObjectId.is_valid(carrier_id):
            document = await db_obj.db.carriers.find_one({"_id": ObjectId(carrier_id)})
            if document:
                return document
        document = await db_obj.db.carriers.find_one({"id": carrier_id})
        if document:
            return document
        return await db_obj.db.carriers.find_one({"inn": carrier_id})

    store = db_obj._fallback_store.get("carriers", {})
    if carrier_id in store:
        return store[carrier_id]
    for carrier in store.values():
        if carrier.get("id") == carrier_id or carrier.get("inn") == carrier_id:
            return carrier
    return None


def _fallback_carrier_key(store: dict, carrier_doc: dict, carrier_id: str) -> str | None:
    if carrier_id in store:
        return carrier_id
    for key, carrier in store.items():
        if carrier is carrier_doc or carrier.get("id") == carrier_id or carrier.get("inn") == carrier_id:
            return key
    return None


@router.get("")
async def get_carriers(transport_type: str = None):
    db_obj = get_database()
    query = {}
    if transport_type:
        query["transport_type"] = transport_type

    carriers = []
    if db_obj.is_connected:
        cursor = db_obj.db.carriers.find(query)
        items = await cursor.to_list(length=100)
        for carrier in items:
            carriers.append(_serialize_carrier(carrier))
    else:
        for carrier in db_obj._fallback_store.get("carriers", {}).values():
            if transport_type and carrier.get("transport_type") != transport_type:
                continue
            carriers.append(dict(carrier))
    return carriers


@router.post("")
async def create_carrier(carrier: CarrierBase, current_user: dict = Depends(require_role(["ADMIN"]))):
    db_obj = get_database()
    carrier_dict = carrier.dict()
    if db_obj.is_connected:
        if carrier_dict.get("inn"):
            existing = await db_obj.db.carriers.find_one({"inn": carrier_dict["inn"]})
            if existing:
                raise HTTPException(status_code=400, detail="Перевозчик с таким ИНН уже существует")
        result = await db_obj.db.carriers.insert_one(carrier_dict)
        carrier_dict["id"] = str(result.inserted_id)
    else:
        if "carriers" not in db_obj._fallback_store:
            db_obj._fallback_store["carriers"] = {}
        if carrier_dict.get("inn"):
            for existing in db_obj._fallback_store["carriers"].values():
                if existing.get("inn") == carrier_dict["inn"]:
                    raise HTTPException(status_code=400, detail="Перевозчик с таким ИНН уже существует")
        carrier_id = str(ObjectId())
        carrier_dict["id"] = carrier_id
        db_obj._fallback_store["carriers"][carrier_id] = carrier_dict
    return carrier_dict


@router.put("/{carrier_id}")
async def update_carrier(
    carrier_id: str,
    carrier: CarrierBase,
    current_user: dict = Depends(require_role(["ADMIN"])),
):
    db_obj = get_database()
    existing = await _find_carrier_document(db_obj, carrier_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Перевозчик не найден")

    updates = carrier.dict()
    if db_obj.is_connected:
        mongo_id = existing.get("_id")
        if updates.get("inn"):
            conflict = await db_obj.db.carriers.find_one({
                "inn": updates["inn"],
                "_id": {"$ne": mongo_id},
            })
            if conflict:
                raise HTTPException(status_code=400, detail="Перевозчик с таким ИНН уже существует")
        await db_obj.db.carriers.update_one({"_id": mongo_id}, {"$set": updates})
        updated = await db_obj.db.carriers.find_one({"_id": mongo_id})
        return _serialize_carrier(updated)

    store = db_obj._fallback_store.get("carriers", {})
    key = _fallback_carrier_key(store, existing, carrier_id)
    if key is None:
        raise HTTPException(status_code=404, detail="Перевозчик не найден")
    if updates.get("inn"):
        for other_key, other in store.items():
            if other_key != key and other.get("inn") == updates["inn"]:
                raise HTTPException(status_code=400, detail="Перевозчик с таким ИНН уже существует")
    updated = {**existing, **updates, "id": existing.get("id", key)}
    store[key] = updated
    return updated


@router.delete("/{carrier_id}")
async def delete_carrier(carrier_id: str, current_user: dict = Depends(require_role(["ADMIN"]))):
    db_obj = get_database()
    existing = await _find_carrier_document(db_obj, carrier_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Перевозчик не найден")

    if db_obj.is_connected:
        await db_obj.db.carriers.delete_one({"_id": existing["_id"]})
    else:
        store = db_obj._fallback_store.get("carriers", {})
        key = _fallback_carrier_key(store, existing, carrier_id)
        if key is None:
            raise HTTPException(status_code=404, detail="Перевозчик не найден")
        del store[key]

    return {"message": "Перевозчик удалён", "id": carrier_id}
