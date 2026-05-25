from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.action_schema import ActionCreate, ActionUpdate
from app.utils.object_id import serialize_doc, serialize_docs


async def create_action(db: AsyncIOMotorDatabase, payload: ActionCreate, commercial_id: str) -> dict:
    now = datetime.now(timezone.utc)
    doc = payload.model_dump()
    doc.update({"commercial_id": commercial_id, "statut": "en_attente", "created_at": now, "updated_at": now})
    result = await db.actions.insert_one(doc)
    return serialize_doc(await db.actions.find_one({"_id": result.inserted_id}))


async def get_client_actions(db: AsyncIOMotorDatabase, client_id: str) -> list[dict]:
    return serialize_docs(await db.actions.find({"client_id": client_id}).sort("created_at", -1).to_list(200))


async def update_action(db: AsyncIOMotorDatabase, action_id: str, payload: ActionUpdate) -> dict:
    if not ObjectId.is_valid(action_id):
        raise HTTPException(status_code=400, detail="ID action invalide")
    data = payload.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.now(timezone.utc)
    await db.actions.update_one({"_id": ObjectId(action_id)}, {"$set": data})
    action = await db.actions.find_one({"_id": ObjectId(action_id)})
    if not action:
        raise HTTPException(status_code=404, detail="Action introuvable")
    return serialize_doc(action)
