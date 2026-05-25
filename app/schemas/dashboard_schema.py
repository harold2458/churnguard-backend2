from datetime import datetime

from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    nombre_total_clients: int = 0
    nombre_clients_a_risque: int = 0
    clients_critiques: int = 0
    mrr_a_risque: float = 0
    taux_moyen_churn: float = 0
    repartition_risques: dict[str, int] = Field(default_factory=dict)


class DashboardClientWatchResponse(BaseModel):
    id: str
    nom: str
    prenom: str
    email: str
    telephone: str | None = None
    MonthlyCharges: float = 0
    score_churn: float | None = None
    niveau_risque: str | None = None
    derniere_prediction: datetime | None = None


class DashboardAlertResponse(BaseModel):
    id: str
    client_id: str
    client_nom: str
    niveau: str
    motif: str
    score_avant: float | None = None
    score_apres: float
    lue: bool = False
    traitee: bool = False
    created_at: datetime


class DashboardHomeResponse(BaseModel):
    kpis: DashboardStatsResponse
    alertes_non_traitees: int = 0
    a_surveiller_aujourdhui: list[DashboardClientWatchResponse] = Field(default_factory=list)
    dernieres_alertes: list[DashboardAlertResponse] = Field(default_factory=list)


class DashboardPredictionResponse(BaseModel):
    id: str
    client_id: str
    score: float
    niveau: str
    top_raisons_shap: list[dict] = Field(default_factory=list)
    recommandations: list[str] = Field(default_factory=list)
    date_prediction: datetime


class DashboardRiskFactorResponse(BaseModel):
    feature: str = Field(alias="_id")
    impact_moyen: float
    count: int


class DashboardUnresolvedAlertsResponse(BaseModel):
    alertes_non_traitees: int = 0


class DashboardScoreEvolutionResponse(BaseModel):
    id: str
    client_id: str
    score: float
    niveau: str
    date_prediction: datetime
