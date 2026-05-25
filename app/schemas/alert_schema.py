from datetime import datetime

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: str
    client_id: str
    client_nom: str
    niveau: str
    motif: str
    score_avant: float | None = None
    score_apres: float
    lue: bool
    traitee: bool
    traitee_par: str | None = None
    traitee_le: datetime | None = None
    created_at: datetime
