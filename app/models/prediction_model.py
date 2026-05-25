from datetime import datetime, timezone

from pydantic import BaseModel, Field


class PredictionHistoryInDB(BaseModel):
    client_id: str
    score: float
    niveau: str
    top_raisons_shap: list[dict]
    recommandations: list[str]
    date_prediction: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
