from datetime import datetime

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.utils.dependencies import require_roles


router = APIRouter(prefix="/history", tags=["Historique global"], dependencies=[Depends(require_roles("admin", "manager"))])


@router.get("/global")
async def global_history(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    type_event: str | None = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    events = []

    def in_range(value):
        if not value:
            return True
        if date_from and value < date_from:
            return False
        if date_to and value > date_to:
            return False
        return True

    predictions = await db.historique_scores.find({}).sort("date_prediction", -1).to_list(500)
    for prediction in predictions:
        date = prediction.get("date_prediction")
        if in_range(date) and type_event in (None, "prediction", "tout"):
            events.append(
                {
                    "type": "prediction",
                    "date": date,
                    "client_id": prediction.get("client_id"),
                    "description": f"Score calculé: {round((prediction.get('score') or 0) * 100, 2)}%",
                    "niveau": prediction.get("niveau"),
                }
            )

    alerts = await db.alertes.find({}).sort("created_at", -1).to_list(500)
    for alert in alerts:
        date = alert.get("created_at")
        if in_range(date) and type_event in (None, "alerte", "tout"):
            events.append(
                {
                    "type": "alerte",
                    "date": date,
                    "client_id": alert.get("client_id"),
                    "description": alert.get("motif"),
                    "niveau": alert.get("niveau"),
                }
            )

    actions = await db.actions.find({}).sort("updated_at", -1).to_list(500)
    for action in actions:
        date = action.get("updated_at") or action.get("created_at")
        if in_range(date) and type_event in (None, "action", "tout"):
            events.append(
                {
                    "type": "action",
                    "date": date,
                    "client_id": action.get("client_id"),
                    "commercial_id": action.get("commercial_id"),
                    "description": action.get("description"),
                    "statut": action.get("statut"),
                }
            )

    events.sort(key=lambda event: event.get("date") or datetime.min, reverse=True)
    return {"total": len(events), "events": events[:200]}
