from datetime import datetime

from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    nombre_total_clients: int = 0
    nombre_clients_a_risque: int = 0
    clients_critiques: int = 0
    mrr_a_risque: float = 0
    taux_moyen_churn: float = 0
    repartition_risques: dict[str, int] = Field(default_factory=dict)


class DashboardClientWatchItem(BaseModel):
    id: str
    nom: str
    prenom: str
    email: str
    telephone: str | None = None
    MonthlyCharges: float = 0
    score_churn: float | None = None
    niveau_risque: str | None = None
    derniere_prediction: datetime | None = None


class DashboardAlertItem(BaseModel):
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


class DashboardHome(BaseModel):
    kpis: DashboardStats
    alertes_non_traitees: int = 0
    a_surveiller_aujourdhui: list[DashboardClientWatchItem] = Field(default_factory=list)
    dernieres_alertes: list[DashboardAlertItem] = Field(default_factory=list)


class DashboardPredictionItem(BaseModel):
    id: str
    client_id: str
    score: float
    niveau: str
    top_raisons_shap: list[dict] = Field(default_factory=list)
    recommandations: list[str] = Field(default_factory=list)
    date_prediction: datetime


class DashboardRiskFactor(BaseModel):
    feature: str = Field(alias="_id")
    impact_moyen: float
    count: int


class DashboardUnresolvedAlerts(BaseModel):
    alertes_non_traitees: int = 0


class DashboardScoreEvolutionItem(BaseModel):
    id: str
    client_id: str
    score: float
    niveau: str
    date_prediction: datetime
