from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.schemas.prediction_schema import PredictionResponse
from app.services.prediction_service import predict_client_churn
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/predictions", tags=["Prédictions"], dependencies=[Depends(get_current_user)])


@router.post("/client/{client_id}", response_model=PredictionResponse)
async def predict_client(client_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await predict_client_churn(db, client_id)
