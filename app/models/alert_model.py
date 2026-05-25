from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AlertInDB(BaseModel):
    client_id: str
    client_nom: str
    niveau: str
    motif: str
    score_avant: float | None = None
    score_apres: float
    lue: bool = False
    traitee: bool = False
    traitee_par: str | None = None
    traitee_le: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
