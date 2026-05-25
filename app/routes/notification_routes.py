from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.utils.dependencies import get_current_user
from app.utils.object_id import serialize_doc, serialize_docs


router = APIRouter(prefix="/notifications", tags=["Notifications"], dependencies=[Depends(get_current_user)])


@router.get("")
async def list_notifications(db: AsyncIOMotorDatabase = Depends(get_database), unread_only: bool = False):
    query = {"lue": False} if unread_only else {}
    docs = await db.notifications.find(query).sort("created_at", -1).to_list(300)
    return serialize_docs(docs)


@router.patch("/{notification_id}/read")
async def mark_notification_read(notification_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(status_code=400, detail="ID notification invalide")
    result = await db.notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"lue": True, "read_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    return serialize_doc(await db.notifications.find_one({"_id": ObjectId(notification_id)}))


@router.patch("/read-all")
async def mark_all_notifications_read(db: AsyncIOMotorDatabase = Depends(get_database)):
    await db.notifications.update_many({"lue": False}, {"$set": {"lue": True, "read_at": datetime.now(timezone.utc)}})
    return {"message": "Toutes les notifications sont marquées comme lues"}


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(notification_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(status_code=400, detail="ID notification invalide")
    result = await db.notifications.delete_one({"_id": ObjectId(notification_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification introuvable")
