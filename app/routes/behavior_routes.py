from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.behavior_model import BehaviorInDB
from app.schemas.behavior_schema import BehaviorCreate, BehaviorResponse
from app.utils.dependencies import get_current_user
from app.utils.object_id import serialize_doc, serialize_docs


router = APIRouter(prefix="/behaviors", tags=["Analyse comportementale"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=BehaviorResponse, status_code=201)
async def create_behavior(payload: BehaviorCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.behaviors.insert_one(BehaviorInDB(**payload.model_dump()).model_dump())
    return serialize_doc(await db.behaviors.find_one({"_id": result.inserted_id}))


@router.get("/client/{client_id}", response_model=list[BehaviorResponse])
async def get_behaviors(client_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    docs = await db.behaviors.find({"client_id": client_id}).sort("date_enregistrement", -1).to_list(200)
    return serialize_docs(docs)
