from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ml.preprocessing import load_pickle, preprocess_client, risk_level
from app.services.alert_service import create_risk_alert
from app.services.recommendation_service import generate_recommendations
from app.services.shap_service import explain_prediction


def _load_artifacts():
    return load_pickle("churn_model.pkl"), load_pickle("scaler.pkl"), load_pickle("feature_names.pkl")


async def predict_client_churn(db: AsyncIOMotorDatabase, client_id: str) -> dict:
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")

    client = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")

    model, scaler, feature_names = _load_artifacts()
    features = preprocess_client(client, scaler, feature_names)
    score = float(model.predict_proba(features)[0][1])
    level = risk_level(score)
    reasons = explain_prediction(model, features, client)

    behavior = await db.behaviors.find_one({"client_id": client_id}, sort=[("date_enregistrement", -1)])
    recommendations = generate_recommendations(client, behavior)
    now = datetime.now(timezone.utc)

    await db.historique_scores.insert_one(
        {
            "client_id": client_id,
            "score": score,
            "niveau": level,
            "top_raisons_shap": reasons,
            "recommandations": recommendations,
            "date_prediction": now,
        }
    )
    old_score = client.get("score_churn")
    await db.clients.update_one(
        {"_id": ObjectId(client_id)},
        {"$set": {"score_churn": score, "niveau_risque": level, "derniere_prediction": now, "updated_at": now}},
    )
    await create_risk_alert(db, client, old_score, score, level)

    return {
        "client_id": client_id,
        "score_churn": score,
        "score_pct": round(score * 100, 2),
        "niveau_risque": level,
        "decision": "client à risque" if level in {"élevé", "critique"} else "client fidèle",
        "top_raisons_shap": reasons,
        "recommandations": recommendations,
    }
