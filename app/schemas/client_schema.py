from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.models.client_model import RiskLevel


class ClientBase(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    telephone: str | None = None
    gender: Literal["Male", "Female"]
    SeniorCitizen: Literal[0, 1] = 0
    Partner: Literal["Yes", "No"]
    Dependents: Literal["Yes", "No"]
    tenure: int = Field(ge=0)
    PhoneService: Literal["Yes", "No"]
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Literal["Yes", "No", "No internet service"]
    OnlineBackup: Literal["Yes", "No", "No internet service"]
    DeviceProtection: Literal["Yes", "No", "No internet service"]
    TechSupport: Literal["Yes", "No", "No internet service"]
    StreamingTV: Literal["Yes", "No", "No internet service"]
    StreamingMovies: Literal["Yes", "No", "No internet service"]
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: Literal["Yes", "No"]
    PaymentMethod: Literal[
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)",
    ]
    MonthlyCharges: float = Field(ge=0)
    TotalCharges: float = Field(ge=0)
    statut_actif: bool = True


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    nom: str | None = None
    prenom: str | None = None
    email: EmailStr | None = None
    telephone: str | None = None
    gender: Literal["Male", "Female"] | None = None
    SeniorCitizen: Literal[0, 1] | None = None
    Partner: Literal["Yes", "No"] | None = None
    Dependents: Literal["Yes", "No"] | None = None
    tenure: int | None = Field(default=None, ge=0)
    PhoneService: Literal["Yes", "No"] | None = None
    MultipleLines: Literal["Yes", "No", "No phone service"] | None = None
    InternetService: Literal["DSL", "Fiber optic", "No"] | None = None
    OnlineSecurity: Literal["Yes", "No", "No internet service"] | None = None
    OnlineBackup: Literal["Yes", "No", "No internet service"] | None = None
    DeviceProtection: Literal["Yes", "No", "No internet service"] | None = None
    TechSupport: Literal["Yes", "No", "No internet service"] | None = None
    StreamingTV: Literal["Yes", "No", "No internet service"] | None = None
    StreamingMovies: Literal["Yes", "No", "No internet service"] | None = None
    Contract: Literal["Month-to-month", "One year", "Two year"] | None = None
    PaperlessBilling: Literal["Yes", "No"] | None = None
    PaymentMethod: Literal[
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)",
    ] | None = None
    MonthlyCharges: float | None = Field(default=None, ge=0)
    TotalCharges: float | None = Field(default=None, ge=0)
    statut_actif: bool | None = None


class ClientResponse(ClientBase):
    id: str
    score_churn: float | None = None
    niveau_risque: RiskLevel | None = None
    derniere_prediction: datetime | None = None
    created_at: datetime
    updated_at: datetime
