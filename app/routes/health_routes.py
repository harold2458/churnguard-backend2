from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database


router = APIRouter(prefix="/health", tags=["Santé"])


@router.get("")
async def health(db: AsyncIOMotorDatabase = Depends(get_database)):
    await db.command("ping")
    return {"status": "ok", "database": "connected"}
