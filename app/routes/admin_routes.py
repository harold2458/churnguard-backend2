from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.ml.preprocessing import load_pickle
from app.schemas.user_schema import UserInviteRequest, UserResponse, UserRoleUpdate
from app.utils.dependencies import require_roles
from app.utils.object_id import serialize_doc, serialize_docs
from app.utils.security import create_password_reset_token, hash_password, hash_reset_token, password_reset_expiry


router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_roles("admin"))])


@router.get("/users", response_model=list[UserResponse])
async def users(db: AsyncIOMotorDatabase = Depends(get_database)):
    docs = await db.users.find({}).sort("created_at", -1).to_list(200)
    return serialize_docs(docs)


@router.patch("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(user_id: str, active: bool = True, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": active, "updated_at": datetime.now(timezone.utc)}},
    )
    return serialize_doc(await db.users.find_one({"_id": ObjectId(user_id)}))


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_role(user_id: str, payload: UserRoleUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": payload.role, "updated_at": datetime.now(timezone.utc)}},
    )
    return serialize_doc(await db.users.find_one({"_id": ObjectId(user_id)}))


@router.post("/users/invite", status_code=201)
async def invite_user(payload: UserInviteRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=409, detail="Cet email est déjà associé à un compte")
    now = datetime.now(timezone.utc)
    reset_token = create_password_reset_token()
    doc = {
        "email": payload.email.lower(),
        "nom": payload.nom,
        "prenom": payload.prenom,
        "role": payload.role,
        "hashed_password": hash_password(create_password_reset_token()[:16]),
        "is_active": True,
        "password_reset_token_hash": hash_reset_token(reset_token),
        "password_reset_expires_at": password_reset_expiry(minutes=48 * 60),
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(doc)
    user = serialize_doc(await db.users.find_one({"_id": result.inserted_id}))
    user.pop("hashed_password", None)
    user.pop("password_reset_token_hash", None)
    return {"message": "Invitation générée", "invite_token": reset_token, "user": user}


@router.post("/users/{user_id}/reset-password")
async def admin_reset_user_password(user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    token = create_password_reset_token()
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password_reset_token_hash": hash_reset_token(token),
                "password_reset_expires_at": password_reset_expiry(),
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {"message": "Token de réinitialisation généré", "reset_token": token}


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID utilisateur invalide")
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")


@router.get("/model/metrics")
async def model_metrics():
    try:
        metrics = load_pickle("model_metrics.pkl")
    except FileNotFoundError:
        return {"message": "Aucune métrique modèle disponible", "metrics": None}
    return {"metrics": metrics}


@router.post("/model/retrain")
async def retrain_model():
    return {"message": "Endpoint prévu pour lancer le réentraînement via pipeline ML externe."}


@router.get("/settings")
async def get_settings(db: AsyncIOMotorDatabase = Depends(get_database)):
    settings = await db.settings.find_one({"key": "global"})
    return serialize_doc(settings) if settings else {"key": "global", "values": {}}


@router.patch("/settings")
async def update_settings(values: dict, db: AsyncIOMotorDatabase = Depends(get_database)):
    await db.settings.update_one(
        {"key": "global"},
        {"$set": {"values": values, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return serialize_doc(await db.settings.find_one({"key": "global"}))
