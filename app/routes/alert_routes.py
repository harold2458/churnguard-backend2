from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.schemas.alert_schema import AlertResponse
from app.utils.dependencies import get_current_user
from app.utils.object_id import serialize_doc, serialize_docs


router = APIRouter(prefix="/alerts", tags=["Alertes"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(db: AsyncIOMotorDatabase = Depends(get_database), non_traitees: bool = False):
    query = {"traitee": False} if non_traitees else {}
    docs = await db.alertes.find(query).sort("created_at", -1).to_list(200)
    return serialize_docs(docs)


@router.get("/summary/counts")
async def alert_counts(db: AsyncIOMotorDatabase = Depends(get_database)):
    return {
        "total": await db.alertes.count_documents({}),
        "non_lues": await db.alertes.count_documents({"lue": False}),
        "non_traitees": await db.alertes.count_documents({"traitee": False}),
        "critique": await db.alertes.count_documents({"niveau": "critique"}),
        "élevé": await db.alertes.count_documents({"niveau": "élevé"}),
        "modéré": await db.alertes.count_documents({"niveau": "modéré"}),
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="ID alerte invalide")
    alert = await db.alertes.find_one({"_id": ObjectId(alert_id)})
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    return serialize_doc(alert)


@router.patch("/{alert_id}/read", response_model=AlertResponse)
async def mark_read(alert_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="ID alerte invalide")
    result = await db.alertes.update_one({"_id": ObjectId(alert_id)}, {"$set": {"lue": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    return serialize_doc(await db.alertes.find_one({"_id": ObjectId(alert_id)}))


@router.patch("/{alert_id}/done", response_model=AlertResponse)
async def mark_done(
    alert_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(alert_id):
        raise HTTPException(status_code=400, detail="ID alerte invalide")
    result = await db.alertes.update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"traitee": True, "traitee_par": current_user["id"], "traitee_le": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    return serialize_doc(await db.alertes.find_one({"_id": ObjectId(alert_id)}))
