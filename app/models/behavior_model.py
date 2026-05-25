from datetime import datetime, timezone

from pydantic import BaseModel, Field


class BehaviorInDB(BaseModel):
    client_id: str
    frequence_utilisation: int = Field(ge=0)
    nombre_reclamations: int = Field(ge=0)
    retards_paiement: int = Field(ge=0)
    interactions_service_client: int = Field(ge=0)
    baisse_activite: bool = False
    historique_consommation: list[float] = Field(default_factory=list)
    date_enregistrement: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
