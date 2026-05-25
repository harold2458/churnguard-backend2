from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.schemas.action_schema import ActionCreate, ActionResponse, ActionUpdate
from app.services.action_service import create_action, get_client_actions, update_action
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(prefix="/actions", tags=["Actions commerciales"])


@router.post("", response_model=ActionResponse, status_code=201)
async def add_action(
    payload: ActionCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(require_roles("admin", "manager", "commercial")),
):
    return await create_action(db, payload, current_user["id"])


@router.get("/client/{client_id}", response_model=list[ActionResponse])
async def list_client_actions(
    client_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    _user: dict = Depends(get_current_user),
):
    return await get_client_actions(db, client_id)


@router.get("", response_model=list[ActionResponse])
async def list_actions(
    statut: str | None = None,
    priorite: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
    _user: dict = Depends(get_current_user),
):
    query = {}
    if statut:
        query["statut"] = statut
    if priorite:
        query["priorite"] = priorite
    docs = await db.actions.find(query).sort("date_suivi", 1).to_list(300)
    from app.utils.object_id import serialize_docs

    return serialize_docs(docs)


@router.get("/board")
async def actions_board(
    db: AsyncIOMotorDatabase = Depends(get_database),
    _user: dict = Depends(get_current_user),
):
    en_cours = await db.actions.find({"statut": "en_attente"}).sort("date_suivi", 1).to_list(300)
    historique = await db.actions.find({"statut": {"$in": ["faite", "annulee"]}}).sort("updated_at", -1).to_list(300)
    urgentes = [dict(action) for action in en_cours if action.get("priorite") == "urgent"]
    from app.utils.object_id import serialize_docs

    return {
        "en_cours": serialize_docs(en_cours),
        "urgentes": serialize_docs(urgentes),
        "historique": serialize_docs(historique),
        "compteurs": {
            "en_cours": len(en_cours),
            "urgentes": len(urgentes),
            "historique": len(historique),
        },
    }


@router.patch("/{action_id}/done", response_model=ActionResponse)
async def mark_action_done(action_id: str, db: AsyncIOMotorDatabase = Depends(get_database), _user=Depends(get_current_user)):
    return await update_action(db, action_id, ActionUpdate(statut="faite"))


@router.patch("/{action_id}", response_model=ActionResponse)
async def patch_action(
    action_id: str,
    payload: ActionUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    _user=Depends(get_current_user),
):
    return await update_action(db, action_id, payload)
