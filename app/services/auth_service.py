from datetime import datetime, timezone

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.user_schema import ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest, UserCreate
from app.utils.object_id import serialize_doc
from app.utils.security import (
    create_access_token,
    create_password_reset_token,
    hash_password,
    hash_reset_token,
    password_reset_expiry,
    verify_password,
)


async def register_user(db: AsyncIOMotorDatabase, payload: UserCreate) -> dict:
    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")
    now = datetime.now(timezone.utc)
    doc = {
        "email": payload.email.lower(),
        "nom": payload.nom,
        "prenom": payload.prenom,
        "role": payload.role,
        "hashed_password": hash_password(payload.password),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(doc)
    user = await db.users.find_one({"_id": result.inserted_id})
    return serialize_doc(user)


async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> dict:
    user = await db.users.find_one({"email": email.lower()})
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Compte désactivé")
    return serialize_doc(user)


def build_token_response(user: dict) -> dict:
    token = create_access_token(subject=user["id"], data={"role": user["role"], "email": user["email"]})
    safe_user = {k: v for k, v in user.items() if k != "hashed_password"}
    return {"access_token": token, "token_type": "bearer", "user": safe_user}


async def request_password_reset(db: AsyncIOMotorDatabase, payload: ForgotPasswordRequest) -> dict:
    user = await db.users.find_one({"email": payload.email.lower()})
    message = "Si ce compte existe, un lien de réinitialisation a été généré."
    if not user:
        return {"message": message, "reset_token": None}

    token = create_password_reset_token()
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_reset_token_hash": hash_reset_token(token),
                "password_reset_expires_at": password_reset_expiry(),
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return {"message": message, "reset_token": token}


async def reset_password(db: AsyncIOMotorDatabase, payload: ResetPasswordRequest) -> dict:
    token_hash = hash_reset_token(payload.token)
    user = await db.users.find_one({"password_reset_token_hash": token_hash})
    if not user:
        raise HTTPException(status_code=400, detail="Token de réinitialisation invalide")

    expires_at = user.get("password_reset_expires_at")
    if not expires_at or expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token de réinitialisation expiré")

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "hashed_password": hash_password(payload.new_password),
                "password_reset_token_hash": None,
                "password_reset_expires_at": None,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return {"message": "Mot de passe réinitialisé avec succès"}


async def change_password(db: AsyncIOMotorDatabase, user_id: str, payload: ChangePasswordRequest) -> dict:
    from bson import ObjectId

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not verify_password(payload.old_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Ancien mot de passe invalide")
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "hashed_password": hash_password(payload.new_password),
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return {"message": "Mot de passe modifié avec succès"}
