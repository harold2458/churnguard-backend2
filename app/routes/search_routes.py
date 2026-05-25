from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.utils.dependencies import get_current_user
from app.utils.object_id import serialize_docs


router = APIRouter(prefix="/search", tags=["Recherche"], dependencies=[Depends(get_current_user)])


@router.get("")
async def global_search(q: str = Query(min_length=1), db: AsyncIOMotorDatabase = Depends(get_database)):
    regex = {"$regex": q, "$options": "i"}
    clients = await db.clients.find(
        {"$or": [{"nom": regex}, {"prenom": regex}, {"email": regex}, {"telephone": regex}]}
    ).limit(10).to_list(10)
    alerts = await db.alertes.find({"$or": [{"client_nom": regex}, {"motif": regex}, {"niveau": regex}]}).limit(10).to_list(10)
    actions = await db.actions.find({"$or": [{"type_action": regex}, {"description": regex}, {"note": regex}]}).limit(10).to_list(10)
    return {
        "clients": serialize_docs(clients),
        "alertes": serialize_docs(alerts),
        "actions": serialize_docs(actions),
    }
