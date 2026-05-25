from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ActionInDB(BaseModel):
    client_id: str
    commercial_id: str
    type_action: str
    description: str
    note: str | None = None
    statut: Literal["en_attente", "faite", "annulee"] = "en_attente"
    date_suivi: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
