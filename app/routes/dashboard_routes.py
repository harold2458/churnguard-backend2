from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.schemas.dashboard_schema import (
    DashboardHomeResponse,
    DashboardPredictionResponse,
    DashboardRiskFactorResponse,
    DashboardScoreEvolutionResponse,
    DashboardStatsResponse,
    DashboardUnresolvedAlertsResponse,
)
from app.utils.dependencies import get_current_user, require_roles
from app.utils.object_id import serialize_docs


router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(require_roles("admin", "manager"))])


@router.get("/stats", response_model=DashboardStatsResponse)
async def stats(db: AsyncIOMotorDatabase = Depends(get_database)):
    total = await db.clients.count_documents({})
    risque_query = {"niveau_risque": {"$in": ["élevé", "critique"]}}
    at_risk = await db.clients.count_documents(risque_query)
    pipeline = [{"$group": {"_id": None, "avg_score": {"$avg": "$score_churn"}}}]
    avg_doc = await db.clients.aggregate(pipeline).to_list(1)
    repartition = await db.clients.aggregate(
        [{"$group": {"_id": "$niveau_risque", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    ).to_list(10)
    return {
        "nombre_total_clients": total,
        "nombre_clients_a_risque": at_risk,
        "clients_critiques": await db.clients.count_documents({"niveau_risque": "critique"}),
        "mrr_a_risque": await _mrr_at_risk(db),
        "taux_moyen_churn": round((avg_doc[0]["avg_score"] or 0) * 100, 2) if avg_doc else 0,
        "repartition_risques": {item["_id"] or "non_predits": item["count"] for item in repartition},
    }


@router.get("/home", response_model=DashboardHomeResponse)
async def home_dashboard(db: AsyncIOMotorDatabase = Depends(get_database)):
    stats_data = await stats(db)
    watch = await db.clients.find({"niveau_risque": {"$in": ["élevé", "critique"]}}).sort("score_churn", -1).limit(3).to_list(3)
    latest_alerts = await db.alertes.find({"traitee": False}).sort("created_at", -1).limit(5).to_list(5)
    return {
        "kpis": stats_data,
        "alertes_non_traitees": await db.alertes.count_documents({"traitee": False}),
        "a_surveiller_aujourdhui": serialize_docs(watch),
        "dernieres_alertes": serialize_docs(latest_alerts),
    }


async def _mrr_at_risk(db: AsyncIOMotorDatabase) -> float:
    docs = await db.clients.find({"niveau_risque": {"$in": ["élevé", "critique"]}}).to_list(5000)
    return round(sum(float(doc.get("MonthlyCharges") or 0) for doc in docs), 2)


@router.get("/latest-predictions", response_model=list[DashboardPredictionResponse])
async def latest_predictions(db: AsyncIOMotorDatabase = Depends(get_database), limit: int = 10):
    docs = await db.historique_scores.find({}).sort("date_prediction", -1).limit(limit).to_list(limit)
    return serialize_docs(docs)


@router.get("/top-risk-factors", response_model=list[DashboardRiskFactorResponse], response_model_by_alias=False)
async def top_risk_factors(db: AsyncIOMotorDatabase = Depends(get_database)):
    pipeline = [
        {"$unwind": "$top_raisons_shap"},
        {"$group": {"_id": "$top_raisons_shap.feature", "impact_moyen": {"$avg": {"$abs": "$top_raisons_shap.impact"}}, "count": {"$sum": 1}}},
        {"$sort": {"impact_moyen": -1}},
        {"$limit": 10},
    ]
    return await db.historique_scores.aggregate(pipeline).to_list(10)


@router.get("/unresolved-alerts", response_model=DashboardUnresolvedAlertsResponse)
async def unresolved_alerts(db: AsyncIOMotorDatabase = Depends(get_database)):
    return {"alertes_non_traitees": await db.alertes.count_documents({"traitee": False})}


@router.get("/score-evolution/{client_id}", response_model=list[DashboardScoreEvolutionResponse])
async def score_evolution(client_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    docs = await db.historique_scores.find({"client_id": client_id}).sort("date_prediction", 1).to_list(500)
    return serialize_docs(docs)
