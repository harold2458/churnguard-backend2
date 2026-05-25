from datetime import datetime

from pydantic import BaseModel


class ShapReason(BaseModel):
    feature: str
    impact: float
    valeur: float | str | int | None = None


class PredictionResponse(BaseModel):
    client_id: str
    score_churn: float
    score_pct: float
    niveau_risque: str
    decision: str
    top_raisons_shap: list[ShapReason]
    recommandations: list[str]


class PredictionHistoryResponse(BaseModel):
    id: str
    client_id: str
    score: float
    niveau: str
    top_raisons_shap: list[dict]
    recommandations: list[str]
    date_prediction: datetime
